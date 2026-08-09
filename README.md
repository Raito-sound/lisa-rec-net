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

GitHub Pages（`main` ブランチのルート）。独自ドメイン `lisa-rec.net` へ切り替える際は `CNAME` ファイルを追加し、DNS の apex と www のみ変更する。既存のサブドメインのレコードは消さないこと。
