# lisa-rec.net

株式会社リサレコ（Lisa-Rec Co.,Ltd）の公式サイト。会社トップと自動生成する静的ブログで構成。

- 本番URL（予定）: https://lisa-rec.net/
- 会社: 株式会社リサレコ / 代表取締役 久場 超（作曲家・来兎）/ 2010年3月設立 / 沖縄県那覇市
- 連絡先: contact@lisa-rec.com

## ファイル

| ファイル | 役割 |
|---|---|
| `index.html` | サイト本体（日本語）。`templates/home.html` + `content/i18n/home.ja.json` から生成 |
| `en/index.html` | 英語版トップ。同じテンプレート + `content/i18n/home.en.json` から生成 |
| `templates/home.html`, `templates/works-list.html` | トップのテンプレートと実績一覧の共通断片 |
| `content/i18n/home.{ja,en}.json` | トップの全文面（FAQ 含む）。文面はここを直す |
| `_tools/build_home.py` | `index.html` と `en/index.html` を再生成する |
| `lang.js` | 初回訪問のブラウザ言語による `/` ↔ `/en/` の振り分けと、ヘッダー切替の選択保存 |
| `site-refresh.css` | コーポレートカラーと可読性を定義するサイトデザイン |
| `404.html` | 存在しないURLに来たとき用 |
| `ogp-v3.png` | SNS共有時のカード画像（1200×630） |
| `llms.txt` | 生成AI・LLM向けのサイト要約（AIフレンドリー方針） |
| `robots.txt` | クローラー設定。AIクローラーは全許可 |
| `sitemap.xml` | サイトマップ |
| `REQUIREMENTS.md` | デザイン、可読性、AIフレンドリー、情報品質の要件定義 |
| `blog/index.html` | 最新記事と新着記事を掲載するブログトップ |
| `blog/page/<n>/index.html` | 12記事ずつのページ分割一覧 |
| `blog/archive/` | 年別アーカイブ |
| `blog/feed.xml` | 最新30記事のRSSフィード |
| `post/<slug>/index.html` | 旧Wix URLを引き継ぐ静的記事ページ |
| `content/blog/*.json` | Wixから抽出した記事の正規化データ |
| `content/posts/*.md` | 今後追加するブログ記事のMarkdown原稿 |
| `content/blog-tags.json` | AIが記事内容から選ぶブログタグの管理候補 |
| `assets/blog/` | Wix依存をなくすためにローカル保存した記事画像 |
| `_tools/migrate_wix_blog.py` | Wixの公開HTMLから記事・画像・メタデータを移行するスクリプト |
| `content/work-links.json` | raito.studio の作品ページ一覧（`raito/scripts/build-works-pages.py` が生成）。記事本文に作品名があれば「関連する作品」リンクと BlogPosting の `mentions` を自動付与 |
| `_tools/build_blog.py` | 記事・一覧・年別アーカイブ・RSS・サイトマップを一括再生成する通常更新用コマンド |

## 設計方針

- **AIフレンドリー**: 検索AI・対話AIに正しく引用されることを前提に、固有名詞のフル表記・主語の明示・数字と年の記載を徹底する
- **実績一覧は静的HTML**: WORKSの全件をHTMLに直接書き出す。JavaScriptで生成しない（LLMクローラーはJSを実行しないため）
- **構造化データ**: JSON-LD で Organization / Person / WebSite を宣言。Person は `https://raito.studio/#person` を共通IDにして raito.studio と同一人物として接続する
- **軽量維持**: 外部CDN・外部フォント・トラッキングを入れない。Core Web Vitals は軽さで勝つ

詳細は [`REQUIREMENTS.md`](REQUIREMENTS.md) を参照する。

## 更新の流れ

実績データ（WORKS）と本文原稿は Notion 側が原本。Notion を更新したうえで `index.html` に反映する。

## Wixブログ移行

現在は390記事を移行済み。旧URLの `/post/<slug>/`、本文、画像、外部リンク、YouTube、公開日、OGP、BlogPosting構造化データを維持する。記事画像はEXIFを除去し、長辺1920px以内に最適化してから `assets/blog/` で配信する。一覧は12記事ずつに分割し、年別アーカイブ、RSS、前後の記事リンクを自動生成する。

トップの文面を直したとき（日英とも）:

```sh
python3 _tools/build_home.py
```

生成順は raito 側の `scripts/build-works-pages.py` → `_tools/build_home.py` → `_tools/build_blog.py`。ブログとトップのヘッダーには EN／日本語 切替があり、英語版は `/en/` のみ（記事は日本語のまま）。

通常の再生成と新規Markdown記事の反映:

```sh
python3 _tools/build_blog.py
```

新規記事は `content/posts/_template.md` を参考に、`content/posts/YYYY-MM-DD-slug.md` として作成する。画像は `assets/blog/<slug>/` に配置する。チャットで原稿やメモ、写真を渡し、文章整理・Markdown作成・画像最適化・プレビュー確認まで行う運用を想定している。

タグは執筆者に入力を求めず、記事内容を読んだAIが `content/blog-tags.json` の候補から原則1〜3個を選ぶ。候補外・過剰なタグは生成処理で拒否し、表記揺れとタグの乱立を防ぐ。

このコマンドが記事ページ、12件ごとの一覧、ページ番号、年別アーカイブ、RSS、サイトマップをすべて自動更新するため、一覧HTMLを手作業で直す必要はない。各記事には BlogPosting とパンくず、一覧には Blog / CollectionPage / ItemList の構造化データを出力する。

ダウンロード済みのWix HTMLを再インポートする場合:

```sh
python3 _tools/migrate_wix_blog.py --source-dir /path/to/wix-html
```

新たに画像を取得して最適化する場合は、Pillowが利用できるPythonで実行する。

```sh
python3 _tools/migrate_wix_blog.py --source-dir /path/to/wix-html --download-images --optimize-images
```

## 公開

GitHub Pagesで配信する。`main`への更新を `.github/workflows/pages.yml` が公開する。
公開用ファイルのみを配信し、原稿・生成スクリプト・バックアップはサイトの配信対象から除外する。
Jekyllを経由せず、アンダースコアで始まる旧ブログURLも維持する。

- 仮公開URL: https://raito-sound.github.io/lisa-rec-net/
- 本番URL（予定）: https://lisa-rec.net/

### 独自ドメイン切替時のチェックリスト

1. Settings → Pages の公開元を GitHub Actions にする。独自ドメインをGitHub側に登録してからDNSを変更する（Actions公開では `CNAME` ファイルは使わない）
2. DNS は **apex と www のみ** 変更する。**既存のサブドメインのレコードは消さない**（別サービスが稼働しているため）
3. Settings → Pages → Custom domain に `lisa-rec.net` を設定し、Enforce HTTPS を有効にする
4. `https://lisa-rec.net/ogp-v3.png` が表示されることを確認する。`index.html` の `og:image` はこのURLを指しているため、DNS切替までSNSの共有カードには画像が出ない（想定どおりの挙動）
5. Google Search Console と Bing Webmaster Tools にサイトを登録する

## 更新方法

ファイルを編集したあと、リポジトリのフォルダで次を実行する。

```
git add -A
git commit -m "変更内容"
git push
```
