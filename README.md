# lisa-rec.net

株式会社リサレコ（Lisa-Rec Co.,Ltd）の公式サイト。静的HTML1枚構成。

- 本番URL（予定）: https://lisa-rec.net/
- 会社: 株式会社リサレコ / 代表取締役 久場 超（作曲家・来兎）/ 2010年3月設立 / 沖縄県那覇市
- 連絡先: contact@lisa-rec.net

## ファイル

| ファイル | 役割 |
|---|---|
| `index.html` | サイト本体。CSS・JS・ロゴ・音符SVGをすべてインラインした自己完結型の1ファイル |
| `404.html` | 存在しないURLに来たとき用 |
| `ogp.png` | SNS共有時のカード画像（1200×630） |
| `llms.txt` | 生成AI・LLM向けのサイト要約（AIフレンドリー方針） |
| `robots.txt` | クローラー設定。AIクローラーは全許可 |
| `sitemap.xml` | サイトマップ |

## 設計方針

- **AIフレンドリー**: 検索AI・対話AIに正しく引用されることを前提に、固有名詞のフル表記・主語の明示・数字と年の記載を徹底する
- **実績一覧は静的HTML**: WORKSの全件をHTMLに直接書き出す。JavaScriptで生成しない（LLMクローラーはJSを実行しないため）
- **構造化データ**: JSON-LD で Organization / Person / WebSite を宣言。Person は `https://raito.studio/#person` を共通IDにして raito.studio と同一人物として接続する
- **軽量維持**: 外部CDN・外部フォント・トラッキングを入れない。Core Web Vitals は軽さで勝つ

## 更新の流れ

実績データ（WORKS）と本文原稿は Notion 側が原本。Notion を更新したうえで `index.html` に反映する。

## 公開

GitHub Pages（`main` ブランチのルート）で配信する。

- 仮公開URL: https://raito-sound.github.io/lisa-rec-net/
- 本番URL（予定）: https://lisa-rec.net/

### 独自ドメイン切替時のチェックリスト

1. `CNAME` ファイル（中身は `lisa-rec.net` の1行）をリポジトリのルートに追加する
2. DNS は **apex と www のみ** 変更する。**既存のサブドメインのレコードは消さない**（別サービスが稼働しているため）
3. Settings → Pages → Custom domain に `lisa-rec.net` を設定し、Enforce HTTPS を有効にする
4. `https://lisa-rec.net/ogp.png` が表示されることを確認する。`index.html` の `og:image` はこのURLを指しているため、DNS切替までSNSの共有カードには画像が出ない（想定どおりの挙動）
5. Google Search Console と Bing Webmaster Tools にサイトを登録する

## 更新方法

ファイルを編集したあと、リポジトリのフォルダで次を実行する。

```
git add -A
git commit -m "変更内容"
git push
```
