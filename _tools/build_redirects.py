#!/usr/bin/env python3
"""Generate static redirect stubs for old URLs (WordPress-era /YYYY/MM/slug/, etc.).

Input: content/redirects.json  {"/2017/03/honda-marumaru/": "/post/%E3%80%90cm%E3%80%91honda-.../", ...}
Output: <old path>/index.html with canonical + meta refresh + JS redirect.
`--list-top` prints the top-level directories that hold stubs (for the build script).
GitHub Pages cannot send 301s, so this is the closest static equivalent; Google treats an
instant meta refresh as a permanent redirect.
"""
import json, sys, html
from urllib.parse import unquote
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE_URL = "https://lisa-rec.net"
SRC = ROOT / "content" / "redirects.json"

def load() -> dict:
    return json.loads(SRC.read_text(encoding="utf-8")) if SRC.is_file() else {}

def stub(new_url: str) -> str:
    u = html.escape(new_url, quote=True)
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>移動しました｜株式会社リサレコ</title>
<link rel="canonical" href="{u}">
<meta http-equiv="refresh" content="0; url={u}">
<script>location.replace({json.dumps(new_url)});</script>
</head>
<body>
<p>このページは移動しました。自動的に移動しない場合は <a href="{u}">{u}</a> を開いてください。</p>
</body>
</html>
"""

def main() -> None:
    mapping = load()
    if "--list-top" in sys.argv:
        print(" ".join(sorted({unquote(p).strip("/").split("/")[0] for p in mapping})))
        return
    n = 0
    for old, new in mapping.items():
        if not old.startswith("/"):
            raise SystemExit(f"old path must start with '/': {old}")
        if new.startswith("/"):
            new = SITE_URL + new
        out = ROOT / unquote(old).strip("/") / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(stub(new), encoding="utf-8")
        n += 1
    print(f"wrote {n} redirect stubs")

if __name__ == "__main__":
    main()
