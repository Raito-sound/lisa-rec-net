#!/usr/bin/env python3
"""Convert server-rendered Wix Blog pages into static Lisa-Rec blog pages.

The script deliberately uses only the Python standard library.  Wix's public
HTML contains both BlogPosting JSON-LD and a server-rendered rich-content tree,
so the migration does not depend on a browser or on Wix at runtime.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import shutil
import sys
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import format_datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, urlparse
from xml.sax.saxutils import escape as xml_escape


SITE_URL = "https://lisa-rec.net"
PAGE_SIZE = 12
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


@dataclass
class Media:
    uri: str
    alt: str = ""
    caption: str = ""
    width: int | None = None
    height: int | None = None

    @property
    def filename(self) -> str:
        return Path(urlparse(self.uri).path).name

    @property
    def source_url(self) -> str:
        if self.uri.startswith(("https://", "http://")):
            return self.uri.split("/v1/", 1)[0]
        return f"https://static.wixstatic.com/media/{quote(self.uri, safe='~._-')}"


@dataclass
class Post:
    slug: str
    title: str
    description: str
    published: str
    modified: str
    author: str
    blocks: list[dict] = field(default_factory=list)
    media: list[Media] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    @property
    def encoded_slug(self) -> str:
        return quote(self.slug, safe="-._~")

    @property
    def canonical(self) -> str:
        return f"{SITE_URL}/post/{self.encoded_slug}/"

    @property
    def published_date(self) -> str:
        return self.published[:10]

    @property
    def published_jp(self) -> str:
        date = datetime.fromisoformat(self.published.replace("Z", "+00:00"))
        return f"{date.year}年{date.month}月{date.day}日"

    @property
    def hero(self) -> Media | None:
        return self.media[0] if self.media else None


class WixPostParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ld_scripts: list[str] = []
        self._in_ld = False
        self._ld_parts: list[str] = []
        self._in_post = False
        self._post_section_depth = 0
        self._block_tag: str | None = None
        self._block_parts: list[str] = []
        self._figure = False
        self._figure_media: Media | None = None
        self._caption = False
        self._caption_parts: list[str] = []
        self._video_id: str | None = None
        self.blocks: list[dict] = []
        self.media: list[Media] = []

    def handle_starttag(self, tag: str, attrs_list: list[tuple[str, str | None]]) -> None:
        attrs = {key: value or "" for key, value in attrs_list}

        if tag == "script" and attrs.get("type") == "application/ld+json":
            self._in_ld = True
            self._ld_parts = []

        if not self._in_post and tag == "section" and attrs.get("data-hook") == "post-description":
            self._in_post = True
            self._post_section_depth = 1
            return
        if not self._in_post:
            return
        if tag == "section":
            self._post_section_depth += 1

        if tag == "figure":
            self._figure = True
            self._figure_media = None
            self._caption_parts = []
            self._video_id = None
            return

        if self._figure:
            if tag == "wow-image" and attrs.get("data-image-info"):
                try:
                    data = json.loads(attrs["data-image-info"])["imageData"]
                    self._figure_media = Media(
                        uri=data["uri"],
                        width=int(data["width"]) if data.get("width") else None,
                        height=int(data["height"]) if data.get("height") else None,
                    )
                except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                    pass
            elif tag == "img":
                if self._figure_media:
                    self._figure_media.alt = attrs.get("alt", "")
                elif attrs.get("src"):
                    uri = attrs["src"].split("/media/", 1)[-1].split("/v1/", 1)[0]
                    self._figure_media = Media(uri=uri, alt=attrs.get("alt", ""))
            elif tag == "figcaption":
                self._caption = True
            elif tag == "button":
                match = re.search(r"i\.ytimg\.com/vi/([^/]+)/", attrs.get("style", ""))
                if match:
                    self._video_id = match.group(1)
            return

        if tag in {"p", "h2", "h3", "h4", "blockquote"} and self._block_tag is None:
            self._block_tag = tag
            self._block_parts = []
        elif self._block_tag and tag == "a":
            href = html.escape(attrs.get("href", ""), quote=True)
            external = href.startswith(("http://", "https://"))
            extra = ' target="_blank" rel="noopener noreferrer"' if external else ""
            self._block_parts.append(f'<a href="{href}"{extra}>')
        elif self._block_tag and tag in {"strong", "em", "u"}:
            self._block_parts.append(f"<{tag}>")
        elif self._block_tag and tag == "br":
            self._block_parts.append("<br>")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._in_ld:
            self.ld_scripts.append("".join(self._ld_parts))
            self._in_ld = False
            self._ld_parts = []

        if not self._in_post:
            return

        if self._figure:
            if tag == "figcaption":
                self._caption = False
            elif tag == "figure":
                if self._figure_media:
                    self._figure_media.caption = "".join(self._caption_parts).strip()
                    self.media.append(self._figure_media)
                    self.blocks.append({"type": "image", "media_index": len(self.media) - 1})
                elif self._video_id:
                    self.blocks.append({"type": "youtube", "id": self._video_id})
                self._figure = False
            return

        if self._block_tag and tag in {"a", "strong", "em", "u"}:
            self._block_parts.append(f"</{tag}>")
        elif self._block_tag == tag:
            content = "".join(self._block_parts).strip()
            text_only = re.sub(r"<[^>]+>", "", content).strip()
            if text_only:
                self.blocks.append({"type": self._block_tag, "html": content})
            self._block_tag = None
            self._block_parts = []

        if tag == "section":
            self._post_section_depth -= 1
            if self._post_section_depth == 0:
                self._in_post = False

    def handle_data(self, data: str) -> None:
        if self._in_ld:
            self._ld_parts.append(data)
        if not self._in_post:
            return
        if self._figure and self._caption:
            self._caption_parts.append(data)
        elif self._block_tag:
            self._block_parts.append(html.escape(data))


def parse_post(source: Path) -> Post:
    parser = WixPostParser()
    parser.feed(source.read_text(encoding="utf-8"))
    metadata = None
    for raw in parser.ld_scripts:
        try:
            candidate = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if candidate.get("@type") == "BlogPosting":
            metadata = candidate
            break
    if not metadata:
        raise ValueError(f"BlogPosting JSON-LD not found: {source}")

    page_url = metadata.get("url") or metadata["mainEntityOfPage"]["url"]
    slug = html.unescape(urlparse(page_url).path.split("/post/", 1)[1]).rstrip("/")
    post = Post(
        slug=slug,
        title=html.unescape(metadata["headline"]),
        description=html.unescape(metadata.get("description", "")),
        published=metadata["datePublished"],
        modified=metadata.get("dateModified", metadata["datePublished"]),
        author=metadata.get("author", {}).get("name", "Masaru Kuba"),
        blocks=parser.blocks,
        media=parser.media,
    )
    restore_description_links(post)
    return post


def load_content_json(source: Path) -> Post:
    data = json.loads(source.read_text(encoding="utf-8"))
    return Post(
        slug=data["slug"],
        title=data["title"],
        description=data.get("description", ""),
        published=data["published"],
        modified=data.get("modified", data["published"]),
        author=data.get("author", "来兎（久場 超）"),
        blocks=data.get("blocks", []),
        media=[Media(**item) for item in data.get("media", [])],
        tags=data.get("tags", []),
    )


def normalize_post_date(value: str) -> str:
    value = value.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return f"{value}T09:00:00+09:00"
    return value


def inline_markdown(value: str) -> str:
    rendered = html.escape(value.strip())
    rendered = re.sub(r"`([^`]+)`", r"<code>\1</code>", rendered)
    rendered = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", rendered)
    rendered = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", rendered)

    def replace_link(match: re.Match[str]) -> str:
        label, href = match.group(1), match.group(2)
        extra = ' target="_blank" rel="noopener noreferrer"' if href.startswith(("http://", "https://")) else ""
        return f'<a href="{href}"{extra}>{label}</a>'

    return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", replace_link, rendered)


def parse_front_matter(source: Path) -> tuple[dict[str, str], list[str]]:
    lines = source.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"Markdown front matter is required: {source}")
    try:
        end = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration as error:
        raise ValueError(f"Markdown front matter is not closed: {source}") from error
    metadata: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, separator, value = line.partition(":")
        if not separator:
            raise ValueError(f"Invalid front matter line in {source}: {line}")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        metadata[key.strip()] = value
    return metadata, lines[end + 1 :]


def parse_markdown_post(source: Path, allowed_tags: set[str], max_tags: int) -> Post:
    metadata, lines = parse_front_matter(source)
    if not metadata.get("title") or not metadata.get("date"):
        raise ValueError(f"Markdown requires title and date: {source}")
    slug = metadata.get("slug") or re.sub(r"^\d{4}-\d{2}-\d{2}-", "", source.stem)
    published = normalize_post_date(metadata["date"])
    modified = normalize_post_date(metadata.get("modified", metadata["date"]))
    media: list[Media] = []
    cover = metadata.get("cover", "").strip()
    if cover:
        media.append(Media(uri=cover, alt=metadata.get("cover_alt", metadata["title"])))
    blocks: list[dict] = []
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            blocks.append({"type": "p", "html": inline_markdown(" ".join(paragraph))})
            paragraph.clear()

    index = 0
    while index < len(lines):
        line = lines[index].rstrip()
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            index += 1
            continue
        image_match = re.fullmatch(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+[\"']([^\"']*)[\"'])?\)", stripped)
        youtube_match = re.fullmatch(r"\{\{youtube:([A-Za-z0-9_-]{6,})\}\}", stripped)
        heading_match = re.match(r"^(#{2,4})\s+(.+)$", stripped)
        if image_match:
            flush_paragraph()
            alt, filename, caption = image_match.groups()
            existing = next((i for i, item in enumerate(media) if item.filename == Path(filename).name), None)
            if existing is None:
                media.append(Media(uri=Path(filename).name, alt=alt, caption=caption or ""))
                existing = len(media) - 1
            blocks.append({"type": "image", "media_index": existing})
        elif youtube_match:
            flush_paragraph()
            blocks.append({"type": "youtube", "id": youtube_match.group(1)})
        elif heading_match:
            flush_paragraph()
            blocks.append({"type": f"h{len(heading_match.group(1))}", "html": inline_markdown(heading_match.group(2))})
        elif stripped.startswith("> "):
            flush_paragraph()
            quote_lines: list[str] = []
            while index < len(lines) and lines[index].strip().startswith("> "):
                quote_lines.append(lines[index].strip()[2:])
                index += 1
            blocks.append({"type": "blockquote", "html": inline_markdown(" ".join(quote_lines))})
            continue
        elif re.match(r"^[-*]\s+", stripped):
            flush_paragraph()
            items: list[str] = []
            while index < len(lines) and re.match(r"^[-*]\s+", lines[index].strip()):
                items.append(re.sub(r"^[-*]\s+", "", lines[index].strip()))
                index += 1
            blocks.append({"type": "raw", "html": "<ul>" + "".join(f"<li>{inline_markdown(item)}</li>" for item in items) + "</ul>"})
            continue
        elif re.match(r"^\d+\.\s+", stripped):
            flush_paragraph()
            items = []
            while index < len(lines) and re.match(r"^\d+\.\s+", lines[index].strip()):
                items.append(re.sub(r"^\d+\.\s+", "", lines[index].strip()))
                index += 1
            blocks.append({"type": "raw", "html": "<ol>" + "".join(f"<li>{inline_markdown(item)}</li>" for item in items) + "</ol>"})
            continue
        elif stripped == "---":
            flush_paragraph()
            blocks.append({"type": "raw", "html": "<hr>"})
        else:
            paragraph.append(stripped)
        index += 1
    flush_paragraph()
    description = metadata.get("description", "").strip()
    if not description:
        first_paragraph = next((block["html"] for block in blocks if block["type"] == "p"), metadata["title"])
        description = html.unescape(re.sub(r"<[^>]+>", "", first_paragraph))[:180]
    tags = list(dict.fromkeys(tag.strip() for tag in metadata.get("tags", "").split(",") if tag.strip()))
    if not tags:
        raise ValueError(f"Markdown requires 1-{max_tags} curated tags: {source}")
    if len(tags) > max_tags:
        raise ValueError(f"Markdown has too many tags (maximum {max_tags}): {source}")
    unknown_tags = [tag for tag in tags if tag not in allowed_tags]
    if unknown_tags:
        raise ValueError(f"Unknown blog tags in {source}: {', '.join(unknown_tags)}")
    return Post(
        slug=slug,
        title=metadata["title"],
        description=description,
        published=published,
        modified=modified,
        author=metadata.get("author", "来兎（久場 超）"),
        blocks=blocks,
        media=media,
        tags=tags,
    )


def restore_description_links(post: Post) -> None:
    """Restore legacy-editor links that Wix exposes only in SEO description text."""
    existing = "\n".join(block.get("html", "") for block in post.blocks)
    existing_video_ids = {block["id"] for block in post.blocks if block["type"] == "youtube"}
    description = html.unescape(post.description).replace("&hellip;", "…")
    candidates = re.findall(r"https?://[^\s<>\"…]+", description)
    for raw_url in candidates:
        url = raw_url.rstrip("。、，．）」』】〉》")
        if not url or html.escape(url, quote=True) in existing:
            continue
        youtube = re.search(r"(?:youtube\.com/watch\?v=|youtu\.be/)([A-Za-z0-9_-]{6,})", url)
        if youtube:
            video_id = youtube.group(1)
            if video_id not in existing_video_ids:
                post.blocks.append({"type": "youtube", "id": video_id})
                existing_video_ids.add(video_id)
            continue
        escaped_url = html.escape(url, quote=True)
        post.blocks.append({
            "type": "p",
            "html": f'<a href="{escaped_url}" target="_blank" rel="noopener noreferrer">{html.escape(url)}</a>',
        })
        existing += f"\n{escaped_url}"


def plain_post_text(post: Post) -> str:
    return " ".join(
        html.unescape(re.sub(r"<[^>]+>", " ", block.get("html", "")))
        for block in post.blocks
        if block.get("html")
    )


WORK_LINKS_FILE = Path(__file__).resolve().parent.parent / "content" / "work-links.json"
_WORK_LINKS: list[dict] | None = None


def _keyword_pattern(keyword: str) -> re.Pattern[str]:
    if re.fullmatch(r"[A-Za-z0-9 :\-!.]+", keyword):
        return re.compile(r"(?<![A-Za-z0-9])" + re.escape(keyword) + r"(?![A-Za-z0-9])")
    return re.compile(re.escape(keyword))


def load_work_links() -> list[dict]:
    """Works from raito.studio (content/work-links.json) that blog posts can point to."""
    global _WORK_LINKS
    if _WORK_LINKS is None:
        _WORK_LINKS = []
        if WORK_LINKS_FILE.is_file():
            for work in json.loads(WORK_LINKS_FILE.read_text(encoding="utf-8"))["works"]:
                work["_patterns"] = [_keyword_pattern(k) for k in work["keywords"]]
                _WORK_LINKS.append(work)
    return _WORK_LINKS


def related_works(post: Post) -> list[dict]:
    text = post.title + " " + plain_post_text(post)
    return [w for w in load_work_links() if any(p.search(text) for p in w["_patterns"])]


def render_related_works(post: Post) -> str:
    works = related_works(post)
    if not works:
        return ""
    links = "".join(
        f'<a href="{html.escape(w["url"])}"><strong>{html.escape(w["title_ja"])}</strong><span>{html.escape(w["roles_ja"])} · {html.escape(w["year"])}</span></a>'
        for w in works
    )
    return f'<nav class="related-works" aria-label="関連する作品"><p class="post-label">関連する作品（来兎の担当作品ページ）</p>{links}</nav>\n'


def page_head(post: Post) -> str:
    title = html.escape(f"{post.title}｜リサレコブログ")
    description = html.escape(post.description[:180], quote=True)
    image = f"{SITE_URL}/ogp-v3.png"
    if post.hero:
        image = f"{SITE_URL}/assets/blog/{quote(post.slug, safe='-._~')}/{quote(post.hero.filename)}"
    schema = {
        "@type": "BlogPosting",
        "@id": f"{post.canonical}#article",
        "headline": post.title,
        "description": post.description,
        "datePublished": post.published,
        "dateModified": post.modified,
        "mainEntityOfPage": post.canonical,
        "inLanguage": "ja",
        "author": {"@type": "Person", "@id": "https://raito.studio/#person", "name": "来兎（久場 超）"},
        "publisher": {"@type": "Organization", "@id": f"{SITE_URL}/#org", "name": "株式会社リサレコ"},
        "isPartOf": {"@type": "Blog", "@id": f"{SITE_URL}/blog/#blog", "name": "リサレコブログ"},
        "wordCount": len(re.sub(r"\s+", "", plain_post_text(post))),
    }
    if post.tags:
        schema["keywords"] = post.tags
        schema["articleSection"] = post.tags[0]
    if post.hero:
        schema["image"] = image
    mentioned = related_works(post)
    if mentioned:
        schema["mentions"] = [{"@type": "CreativeWork", "@id": f"{w['url'].replace('/ja/works/', '/works/')}#work", "name": w["title_ja"], "url": w["url"]} for w in mentioned]
    breadcrumb = {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "トップ", "item": f"{SITE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": "ブログ", "item": f"{SITE_URL}/blog/"},
            {"@type": "ListItem", "position": 3, "name": post.title, "item": post.canonical},
        ],
    }
    schema_json = json.dumps(
        {"@context": "https://schema.org", "@graph": [schema, breadcrumb]},
        ensure_ascii=False,
        separators=(",", ":"),
    ).replace("</", "<\\/")
    return f"""<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{post.canonical}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
<meta property="og:type" content="article">
<meta property="og:site_name" content="株式会社リサレコ">
<meta property="og:locale" content="ja_JP">
<meta property="og:url" content="{post.canonical}">
<meta property="og:title" content="{html.escape(post.title, quote=True)}">
<meta property="og:description" content="{description}">
<meta property="og:image" content="{image}">
<meta property="article:published_time" content="{html.escape(post.published)}">
<meta property="article:modified_time" content="{html.escape(post.modified)}">
<meta name="twitter:card" content="summary_large_image">
<link rel="alternate" type="application/rss+xml" title="リサレコブログ RSS" href="../../blog/feed.xml">
<link rel="stylesheet" href="../../blog.css">
<script src="../../lang.js" defer></script>
<script type="application/ld+json">{schema_json}</script>"""


def render_blocks(post: Post) -> str:
    rendered: list[str] = []
    for block in post.blocks:
        kind = block["type"]
        if kind in {"p", "h2", "h3", "h4", "blockquote"}:
            rendered.append(f"<{kind}>{block['html']}</{kind}>")
        elif kind == "image":
            media = post.media[block["media_index"]]
            alt_text = media.alt or post.title
            attrs = ""
            if media.width and media.height:
                attrs = f' width="{media.width}" height="{media.height}"'
            caption = f"<figcaption>{html.escape(media.caption)}</figcaption>" if media.caption else ""
            rendered.append(
                f'<figure><img src="../../assets/blog/{quote(post.slug, safe="-._~")}/{quote(media.filename)}" '
                f'alt="{html.escape(alt_text, quote=True)}" loading="lazy" decoding="async"{attrs}>{caption}</figure>'
            )
        elif kind == "youtube":
            video_id = html.escape(block["id"], quote=True)
            rendered.append(
                '<div class="video"><iframe loading="lazy" '
                f'src="https://www.youtube-nocookie.com/embed/{video_id}" '
                'title="YouTube動画" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" '
                'referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></div>'
            )
        elif kind == "raw":
            rendered.append(block["html"])
    return "\n".join(rendered)


def render_article_navigation(newer: Post | None, older: Post | None) -> str:
    links: list[str] = []
    if newer:
        links.append(
            f'<a class="newer" href="../../post/{newer.encoded_slug}/index.html">'
            f'<span>← 新しい記事</span><strong>{html.escape(newer.title)}</strong></a>'
        )
    if older:
        links.append(
            f'<a class="older" href="../../post/{older.encoded_slug}/index.html">'
            f'<span>古い記事 →</span><strong>{html.escape(older.title)}</strong></a>'
        )
    return '<nav class="article-navigation" aria-label="前後の記事">' + "".join(links) + "</nav>"


def render_post(post: Post, newer: Post | None = None, older: Post | None = None) -> str:
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
{page_head(post)}
</head>
<body>
<header class="site-header">
  <a class="wordmark" href="../../index.html" aria-label="株式会社リサレコ トップ"><img src="../../logo.png" alt="株式会社リサレコ" width="1946" height="342"></a>
  <nav aria-label="ブログナビゲーション"><a href="../../index.html">会社サイト</a><a href="../../blog/index.html">ブログ</a></nav>
  <nav class="lang-switch" aria-label="言語"><a href="../../en/" lang="en" hreflang="en" data-lang-switch="en">EN</a><span aria-hidden="true">/</span><a href="../../index.html" lang="ja" hreflang="ja" data-lang-switch="ja" aria-current="page">日本語</a></nav>
</header>
<main class="post-page">
  <nav class="breadcrumb" aria-label="パンくずリスト"><a href="../../index.html">トップ</a><span>／</span><a href="../../blog/index.html">ブログ</a></nav>
  <article>
    <header class="post-header">
      <p class="post-label">LISA-REC JOURNAL</p>
      <h1>{html.escape(post.title)}</h1>
      <div class="post-meta"><span>来兎（久場 超）</span><time datetime="{post.published}">{post.published_jp}</time></div>
    </header>
    <div class="post-content">
{render_blocks(post)}
    </div>
  </article>
  {render_related_works(post)}{render_article_navigation(newer, older)}
  <nav class="post-back"><a href="../../blog/index.html">← ブログ一覧へ</a></nav>
</main>
<footer><div><span>© Lisa-Rec Co.,Ltd</span><a href="mailto:contact@lisa-rec.com">contact@lisa-rec.com</a></div></footer>
</body>
</html>
"""


def render_blog_header(root_prefix: str, blog_prefix: str) -> str:
    return f"""<header class="site-header">
  <a class="wordmark" href="{root_prefix}index.html" aria-label="株式会社リサレコ トップ"><img src="{root_prefix}logo.png" alt="株式会社リサレコ" width="1946" height="342"></a>
  <nav aria-label="ブログナビゲーション"><a href="{root_prefix}index.html">会社サイト</a><a aria-current="page" href="{blog_prefix}index.html">ブログ</a></nav>
  <nav class="lang-switch" aria-label="言語"><a href="{root_prefix}en/" lang="en" hreflang="en" data-lang-switch="en">EN</a><span aria-hidden="true">/</span><a href="{root_prefix}index.html" lang="ja" hreflang="ja" data-lang-switch="ja" aria-current="page">日本語</a></nav>
</header>"""


def render_blog_tools(blog_prefix: str) -> str:
    return f"""<nav class="blog-tools" aria-label="ブログメニュー">
  <a href="{blog_prefix}index.html">最新記事</a>
  <a href="{blog_prefix}archive/index.html">年別アーカイブ</a>
  <a href="{blog_prefix}feed.xml">RSS</a>
</nav>"""


def render_card(post: Post, root_prefix: str, featured: bool = False) -> str:
    post_href = f'{root_prefix}post/{post.encoded_slug}/index.html'
    image = '<div class="card-placeholder" aria-hidden="true">♪</div>'
    if post.hero:
        alt_text = post.hero.alt or post.title
        image = (
            f'<img src="{root_prefix}assets/blog/{quote(post.slug, safe="-._~")}/{quote(post.hero.filename)}" '
            f'alt="{html.escape(alt_text, quote=True)}" loading="lazy" decoding="async" '
            f'width="{post.hero.width or 1600}" height="{post.hero.height or 900}">'
        )
    class_name = "featured-post" if featured else "post-card"
    excerpt_length = 190 if featured else 120
    media_label = f' aria-label="{html.escape(post.title, quote=True)}"' if not post.hero else ""
    return f"""<article class="{class_name}">
  <a class="card-media" href="{post_href}"{media_label}>{image}</a>
  <div class="card-body">
    <time datetime="{post.published}">{post.published_jp}</time>
    <h2><a href="{post_href}">{html.escape(post.title)}</a></h2>
    <p>{html.escape(post.description[:excerpt_length])}{'…' if len(post.description) > excerpt_length else ''}</p>
    <a class="read-more" href="{post_href}">記事を読む →</a>
  </div>
</article>"""


def blog_page_href(page_number: int, blog_prefix: str) -> str:
    return f"{blog_prefix}index.html" if page_number == 1 else f"{blog_prefix}page/{page_number}/index.html"


def pagination_numbers(current: int, total: int) -> list[int | None]:
    candidates = {1, total, current - 2, current - 1, current, current + 1, current + 2}
    numbers = sorted(number for number in candidates if 1 <= number <= total)
    result: list[int | None] = []
    previous = 0
    for number in numbers:
        if previous and number - previous > 1:
            result.append(None)
        result.append(number)
        previous = number
    return result


def render_pagination(current: int, total: int, blog_prefix: str) -> str:
    if total <= 1:
        return ""
    items: list[str] = []
    if current > 1:
        items.append(f'<a class="pagination-edge" href="{blog_page_href(current - 1, blog_prefix)}">← 前へ</a>')
    for number in pagination_numbers(current, total):
        if number is None:
            items.append('<span class="pagination-ellipsis" aria-hidden="true">…</span>')
        elif number == current:
            items.append(f'<span class="pagination-current" aria-current="page">{number}</span>')
        else:
            items.append(f'<a href="{blog_page_href(number, blog_prefix)}" aria-label="{number}ページ目">{number}</a>')
    if current < total:
        items.append(f'<a class="pagination-edge" href="{blog_page_href(current + 1, blog_prefix)}">次へ →</a>')
    return '<nav class="pagination" aria-label="記事一覧のページ送り">' + "".join(items) + "</nav>"


def render_blog_head(title: str, description: str, canonical: str, root_prefix: str, blog_prefix: str, previous: str = "", following: str = "") -> str:
    relations = []
    if previous:
        relations.append(f'<link rel="prev" href="{previous}">')
    if following:
        relations.append(f'<link rel="next" href="{following}">')
    return f"""<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description, quote=True)}">
<link rel="canonical" href="{canonical}">
{chr(10).join(relations)}
<link rel="alternate" type="application/rss+xml" title="リサレコブログ RSS" href="{blog_prefix}feed.xml">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
<meta property="og:type" content="website">
<meta property="og:site_name" content="株式会社リサレコ">
<meta property="og:title" content="{html.escape(title, quote=True)}">
<meta property="og:description" content="{html.escape(description, quote=True)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE_URL}/ogp-v3.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="{root_prefix}blog.css">
<script src="{root_prefix}lang.js" defer></script>"""


def collection_schema(title: str, description: str, canonical: str, posts: list[Post]) -> str:
    item_list = [
        {
            "@type": "ListItem",
            "position": index,
            "item": {
                "@type": "BlogPosting",
                "@id": f"{post.canonical}#article",
                "url": post.canonical,
                "headline": post.title,
                "datePublished": post.published,
                "author": {"@type": "Person", "@id": "https://raito.studio/#person", "name": "来兎（久場 超）"},
            },
        }
        for index, post in enumerate(posts, 1)
    ]
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Blog",
                "@id": f"{SITE_URL}/blog/#blog",
                "url": f"{SITE_URL}/blog/",
                "name": "リサレコブログ",
                "description": "株式会社リサレコと作曲家・来兎の公式ブログです。",
                "inLanguage": "ja",
                "publisher": {"@type": "Organization", "@id": f"{SITE_URL}/#org", "name": "株式会社リサレコ"},
            },
            {
                "@type": "CollectionPage",
                "@id": f"{canonical}#page",
                "url": canonical,
                "name": title,
                "description": description,
                "isPartOf": {"@id": f"{SITE_URL}/blog/#blog"},
                "mainEntity": {"@id": f"{canonical}#items"},
                "inLanguage": "ja",
            },
            {"@type": "ItemList", "@id": f"{canonical}#items", "numberOfItems": len(posts), "itemListElement": item_list},
        ],
    }
    return '<script type="application/ld+json">' + json.dumps(
        graph, ensure_ascii=False, separators=(",", ":")
    ).replace("</", "<\\/") + "</script>"


def archive_index_schema(title: str, description: str, years: dict[str, list[Post]]) -> str:
    canonical = f"{SITE_URL}/blog/archive/"
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Blog",
                "@id": f"{SITE_URL}/blog/#blog",
                "url": f"{SITE_URL}/blog/",
                "name": "リサレコブログ",
                "inLanguage": "ja",
                "publisher": {"@type": "Organization", "@id": f"{SITE_URL}/#org", "name": "株式会社リサレコ"},
            },
            {
                "@type": "CollectionPage",
                "@id": f"{canonical}#page",
                "url": canonical,
                "name": title,
                "description": description,
                "isPartOf": {"@id": f"{SITE_URL}/blog/#blog"},
                "mainEntity": {"@id": f"{canonical}#items"},
                "inLanguage": "ja",
            },
            {
                "@type": "ItemList",
                "@id": f"{canonical}#items",
                "numberOfItems": len(years),
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": index,
                        "item": {
                            "@type": "CollectionPage",
                            "url": f"{SITE_URL}/blog/archive/{year}/",
                            "name": f"{year}年の記事",
                        },
                    }
                    for index, year in enumerate(years, 1)
                ],
            },
        ],
    }
    return '<script type="application/ld+json">' + json.dumps(
        graph, ensure_ascii=False, separators=(",", ":")
    ).replace("</", "<\\/") + "</script>"


def render_blog_page(page_posts: list[Post], all_posts: list[Post], page_number: int, total_pages: int, root_prefix: str, blog_prefix: str) -> str:
    description = "株式会社リサレコと作曲家・来兎の活動、音楽制作、ゲーム、CMに関する記事です。"
    title = "ブログ｜株式会社リサレコ" if page_number == 1 else f"ブログ {page_number}ページ｜株式会社リサレコ"
    canonical = f"{SITE_URL}/blog/" if page_number == 1 else f"{SITE_URL}/blog/page/{page_number}/"
    previous = "" if page_number == 1 else (f"{SITE_URL}/blog/" if page_number == 2 else f"{SITE_URL}/blog/page/{page_number - 1}/")
    following = "" if page_number == total_pages else f"{SITE_URL}/blog/page/{page_number + 1}/"
    if page_number == 1:
        latest = render_card(page_posts[0], root_prefix, featured=True)
        grid_posts = page_posts[1:]
        listing = f'<section class="featured-area" aria-labelledby="latest-heading"><p id="latest-heading">最新の記事</p>{latest}</section>'
        listing += '<div class="section-heading"><p>RECENT POSTS</p><h2>新着記事</h2></div>'
    else:
        grid_posts = page_posts
        listing = f'<div class="section-heading page-heading"><p>POSTS</p><h2>{page_number}ページ目</h2></div>'
    listing += '<section class="post-grid" aria-label="記事一覧">' + "".join(render_card(post, root_prefix) for post in grid_posts) + "</section>"
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
{render_blog_head(title, description, canonical, root_prefix, blog_prefix, previous, following)}
{collection_schema(title, description, canonical, page_posts)}
</head>
<body>
{render_blog_header(root_prefix, blog_prefix)}
<main class="blog-page">
  <header class="blog-hero"><p>LISA-REC JOURNAL</p><h1>ブログ</h1><div><strong>{len(all_posts)}</strong><span>記事</span></div></header>
  {render_blog_tools(blog_prefix)}
  {listing}
  {render_pagination(page_number, total_pages, blog_prefix)}
</main>
<footer><div><span>© Lisa-Rec Co.,Ltd</span><a href="mailto:contact@lisa-rec.com">contact@lisa-rec.com</a></div></footer>
</body>
</html>
"""


def group_posts_by_year(posts: list[Post]) -> dict[str, list[Post]]:
    years: dict[str, list[Post]] = {}
    for post in posts:
        years.setdefault(post.published[:4], []).append(post)
    return years


def render_archive_index(posts: list[Post]) -> str:
    root_prefix, blog_prefix = "../../", "../"
    years = group_posts_by_year(posts)
    year_cards = "".join(
        f'<a class="year-card" href="{year}/index.html"><strong>{year}</strong><span>{len(year_posts)}記事</span></a>'
        for year, year_posts in years.items()
    )
    title = "年別アーカイブ｜リサレコブログ"
    description = "リサレコブログの記事を公開年ごとに一覧できます。"
    return f"""<!DOCTYPE html>
<html lang="ja"><head>
{render_blog_head(title, description, f"{SITE_URL}/blog/archive/", root_prefix, blog_prefix)}
{archive_index_schema(title, description, years)}
</head><body>
{render_blog_header(root_prefix, blog_prefix)}
<main class="archive-page">
  <nav class="breadcrumb" aria-label="パンくずリスト"><a href="{blog_prefix}index.html">ブログ</a><span>／</span><span>年別アーカイブ</span></nav>
  <header class="archive-header"><p>LISA-REC JOURNAL</p><h1>年別アーカイブ</h1><span>全{len(posts)}記事</span></header>
  {render_blog_tools(blog_prefix)}
  <section class="year-grid" aria-label="年別の記事一覧">{year_cards}</section>
</main>
<footer><div><span>© Lisa-Rec Co.,Ltd</span><a href="mailto:contact@lisa-rec.com">contact@lisa-rec.com</a></div></footer>
</body></html>
"""


def render_year_archive(year: str, posts: list[Post]) -> str:
    root_prefix, blog_prefix = "../../../", "../../"
    items = "".join(
        f'<li><time datetime="{post.published}">{post.published[5:10].replace("-", ".")}</time>'
        f'<a href="{root_prefix}post/{post.encoded_slug}/index.html">{html.escape(post.title)}</a></li>'
        for post in posts
    )
    title = f"{year}年の記事｜リサレコブログ"
    description = f"リサレコブログの{year}年公開記事一覧です。"
    return f"""<!DOCTYPE html>
<html lang="ja"><head>
{render_blog_head(title, description, f"{SITE_URL}/blog/archive/{year}/", root_prefix, blog_prefix)}
{collection_schema(title, description, f"{SITE_URL}/blog/archive/{year}/", posts)}
</head><body>
{render_blog_header(root_prefix, blog_prefix)}
<main class="archive-page">
  <nav class="breadcrumb" aria-label="パンくずリスト"><a href="{blog_prefix}index.html">ブログ</a><span>／</span><a href="../index.html">年別アーカイブ</a><span>／</span><span>{year}</span></nav>
  <header class="archive-header"><p>YEAR ARCHIVE</p><h1>{year}</h1><span>{len(posts)}記事</span></header>
  {render_blog_tools(blog_prefix)}
  <ol class="archive-list">{items}</ol>
</main>
<footer><div><span>© Lisa-Rec Co.,Ltd</span><a href="mailto:contact@lisa-rec.com">contact@lisa-rec.com</a></div></footer>
</body></html>
"""


def write_blog_pages(posts: list[Post], root: Path) -> int:
    blog = root / "blog"
    blog.mkdir(parents=True, exist_ok=True)
    total_pages = math.ceil(len(posts) / PAGE_SIZE)
    for page_number in range(1, total_pages + 1):
        page_posts = posts[(page_number - 1) * PAGE_SIZE : page_number * PAGE_SIZE]
        if page_number == 1:
            destination = blog / "index.html"
            root_prefix, blog_prefix = "../", ""
        else:
            directory = blog / "page" / str(page_number)
            directory.mkdir(parents=True, exist_ok=True)
            destination = directory / "index.html"
            root_prefix, blog_prefix = "../../../", "../../"
        destination.write_text(render_blog_page(page_posts, posts, page_number, total_pages, root_prefix, blog_prefix), encoding="utf-8")
    archive = blog / "archive"
    archive.mkdir(parents=True, exist_ok=True)
    (archive / "index.html").write_text(render_archive_index(posts), encoding="utf-8")
    for year, year_posts in group_posts_by_year(posts).items():
        directory = archive / year
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "index.html").write_text(render_year_archive(year, year_posts), encoding="utf-8")
    return total_pages


def rss_date(value: str) -> str:
    date = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    return format_datetime(date.astimezone(timezone.utc), usegmt=True)


def write_rss(posts: list[Post], root: Path) -> None:
    items = []
    for post in posts[:30]:
        items.append(f"""    <item>
      <title>{xml_escape(post.title)}</title>
      <link>{post.canonical}</link>
      <guid isPermaLink="true">{post.canonical}</guid>
      <pubDate>{rss_date(post.published)}</pubDate>
      <description>{xml_escape(post.description)}</description>
    </item>""")
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>リサレコブログ</title>
    <link>{SITE_URL}/blog/</link>
    <description>株式会社リサレコと作曲家・来兎の活動、音楽制作、ゲーム、CMに関する記事です。</description>
    <language>ja</language>
    <lastBuildDate>{rss_date(posts[0].modified)}</lastBuildDate>
    <atom:link href="{SITE_URL}/blog/feed.xml" rel="self" type="application/rss+xml" />
{chr(10).join(items)}
  </channel>
</rss>
"""
    (root / "blog" / "feed.xml").write_text(feed, encoding="utf-8")


def optimize_image(target: Path) -> None:
    try:
        from PIL import Image, ImageOps
    except ImportError as error:
        raise RuntimeError("Image optimization requires Pillow. Use the bundled Codex Python runtime.") from error

    temporary = target.with_name(f"{target.stem}.optimized{target.suffix}")
    with Image.open(target) as source:
        image = ImageOps.exif_transpose(source)
        image.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
        suffix = target.suffix.lower()
        if suffix in {".jpg", ".jpeg"}:
            if image.mode not in {"RGB", "L"}:
                image = image.convert("RGB")
            image.save(temporary, format="JPEG", quality=84, optimize=True, progressive=True)
        elif suffix == ".png":
            image.save(temporary, format="PNG", optimize=True)
        else:
            image.save(temporary)
    temporary.replace(target)


def download_media(post: Post, root: Path, optimize: bool = False) -> None:
    destination = root / "assets" / "blog" / post.slug
    destination.mkdir(parents=True, exist_ok=True)
    for media in post.media:
        target = destination / media.filename
        if target.exists() and target.stat().st_size:
            continue
        request = urllib.request.Request(media.source_url, headers={"User-Agent": "Mozilla/5.0 LisaRecMigration/1.0"})
        with urllib.request.urlopen(request, timeout=60) as response, target.open("wb") as output:
            shutil.copyfileobj(response, output)
        if optimize:
            optimize_image(target)
        print(f"downloaded {media.source_url} -> {target.relative_to(root)}")


def save_content_json(post: Post, root: Path) -> None:
    destination = root / "content" / "blog"
    destination.mkdir(parents=True, exist_ok=True)
    data = {
        "source": f"https://www.lisa-rec.net/post/{post.encoded_slug}",
        "slug": post.slug,
        "title": post.title,
        "description": post.description,
        "published": post.published,
        "modified": post.modified,
        "author": post.author,
        "blocks": post.blocks,
        "media": [media.__dict__ for media in post.media],
        "tags": post.tags,
    }
    (destination / f"{post.slug}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_sitemap(posts: list[Post], root: Path, total_pages: int) -> None:
    latest = max(post.modified[:10] for post in posts)
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        "  <url>",
        f"    <loc>{SITE_URL}/</loc>",
        "    <lastmod>2026-08-29</lastmod>",
        "    <changefreq>monthly</changefreq>",
        "    <priority>1.0</priority>",
        "  </url>",
        "  <url>",
        f"    <loc>{SITE_URL}/en/</loc>",
        "    <lastmod>2026-09-11</lastmod>",
        "    <changefreq>monthly</changefreq>",
        "    <priority>0.9</priority>",
        "  </url>",
        "  <url>",
        f"    <loc>{SITE_URL}/blog/</loc>",
        f"    <lastmod>{latest}</lastmod>",
        "    <changefreq>weekly</changefreq>",
        "    <priority>0.8</priority>",
        "  </url>",
    ]
    for page_number in range(2, total_pages + 1):
        lines.extend([
            "  <url>",
            f"    <loc>{SITE_URL}/blog/page/{page_number}/</loc>",
            f"    <lastmod>{latest}</lastmod>",
            "    <changefreq>weekly</changefreq>",
            "    <priority>0.5</priority>",
            "  </url>",
        ])
    lines.extend([
        "  <url>",
        f"    <loc>{SITE_URL}/blog/archive/</loc>",
        f"    <lastmod>{latest}</lastmod>",
        "    <changefreq>monthly</changefreq>",
        "    <priority>0.5</priority>",
        "  </url>",
    ])
    for year, year_posts in group_posts_by_year(posts).items():
        lines.extend([
            "  <url>",
            f"    <loc>{SITE_URL}/blog/archive/{year}/</loc>",
            f"    <lastmod>{max(post.modified[:10] for post in year_posts)}</lastmod>",
            "    <changefreq>yearly</changefreq>",
            "    <priority>0.4</priority>",
            "  </url>",
        ])
    for post in posts:
        lines.extend([
            "  <url>",
            f"    <loc>{post.canonical}</loc>",
            f"    <lastmod>{post.modified[:10]}</lastmod>",
            "    <changefreq>yearly</changefreq>",
            "    <priority>0.6</priority>",
            "  </url>",
        ])
    lines.append("</urlset>")
    (root / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_all_posts(root: Path) -> list[Post]:
    json_sources = sorted((root / "content" / "blog").glob("*.json"))
    markdown_dir = root / "content" / "posts"
    markdown_sources = sorted(
        source for source in markdown_dir.glob("*.md")
        if not source.name.startswith("_") and source.name.lower() != "readme.md"
    ) if markdown_dir.exists() else []
    taxonomy = json.loads((root / "content" / "blog-tags.json").read_text(encoding="utf-8"))
    allowed_tags = set(taxonomy["tags"])
    max_tags = int(taxonomy.get("max_tags", 3))
    posts = [load_content_json(source) for source in json_sources]
    posts.extend(parse_markdown_post(source, allowed_tags, max_tags) for source in markdown_sources)
    slugs: set[str] = set()
    for post in posts:
        if post.slug in slugs:
            raise ValueError(f"Duplicate blog slug: {post.slug}")
        slugs.add(post.slug)
    return sorted(posts, key=lambda post: post.published, reverse=True)


def missing_media(posts: list[Post], root: Path) -> list[Path]:
    missing: list[Path] = []
    for post in posts:
        for media in post.media:
            target = root / "assets" / "blog" / post.slug / media.filename
            if not target.is_file():
                missing.append(target)
    return missing


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, help="Optional directory containing downloaded Wix HTML files to import")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--download-images", action="store_true")
    parser.add_argument("--optimize-images", action="store_true", help="Strip metadata and resize newly downloaded images")
    args = parser.parse_args()

    if args.download_images and not args.source_dir:
        parser.error("--download-images requires --source-dir")
    if args.optimize_images and not args.download_images:
        parser.error("--optimize-images requires --download-images")

    if args.source_dir:
        sources = sorted(args.source_dir.glob("*.html"))
        if not sources:
            print(f"No HTML files found in {args.source_dir}", file=sys.stderr)
            return 1
        imported = [parse_post(source) for source in sources]
        for post in imported:
            save_content_json(post, args.root)
            if args.download_images:
                download_media(post, args.root, optimize=args.optimize_images)

    try:
        posts = load_all_posts(args.root)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(error, file=sys.stderr)
        return 1
    if not posts:
        print("No blog content found", file=sys.stderr)
        return 1
    unavailable = missing_media(posts, args.root)
    if unavailable:
        print("Missing blog media:", file=sys.stderr)
        for target in unavailable[:20]:
            print(f"  {target}", file=sys.stderr)
        return 1

    for index, post in enumerate(posts):
        newer = posts[index - 1] if index > 0 else None
        older = posts[index + 1] if index + 1 < len(posts) else None
        destination = args.root / "post" / post.slug
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "index.html").write_text(render_post(post, newer, older), encoding="utf-8")

    total_pages = write_blog_pages(posts, args.root)
    write_rss(posts, args.root)
    write_sitemap(posts, args.root, total_pages)
    print(f"generated {len(posts)} posts, {total_pages} index pages, archives, RSS, and sitemap")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
