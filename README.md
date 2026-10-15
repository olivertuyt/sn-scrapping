# 企業情報スクレイピング & 生成AI抽出

10社の上場企業の公式サイトをクロールし、生成AI（LLM）で以下の4項目を抽出するプログラムです。

1. 本社住所
2. 代表者名
3. 資本金
4. 設立年月

## 動作環境

- Python 3.12 以上
- インターネット接続（対象企業の公式サイトと LLM API にアクセスできること）

## セットアップ

```bash
# 1. 仮想環境の作成（Windows PowerShell の例）
python -m venv .venv
.venv\Scripts\activate        # macOS/Linux: source .venv/bin/activate

# 2. 依存パッケージのインストール
pip install -r requirements.txt
```

## LLM API キーの設定

Gemini API の `generateContent` REST API を使用します。キーは環境変数に設定してください
（リポジトリにはコミットしないこと）。既定モデルは無料枠のある Gemini 3.1 Flash-Lite です。
無料枠の上限は Google の料金表を確認してください。

```powershell
# PowerShell の例
$env:GEMINI_API_KEY = "自分のキー"
$env:GEMINI_MODEL = "gemini-3.1-flash-lite"        # 省略可（既定値）
```

`GOOGLE_API_KEY` も利用できます（両方設定した場合は `GOOGLE_API_KEY` を優先）。
Gemini のキーがない場合は、従来の Anthropic 互換設定
（`LLM_API_KEY` / `ANTHROPIC_AUTH_TOKEN` / `ANTHROPIC_API_KEY`）を使用します。
ローカルで `.env.example` を `.env` にコピーしてキーを保存する方法もあります。
`.env` は Git から除外されますが、プログラムは自動では読み込みません。
PowerShell から実行する場合は、次のようにプロセス環境へ読み込んでください。

```powershell
$keyLine = Get-Content .env | Where-Object { $_ -match '^GEMINI_API_KEY=' } | Select-Object -First 1
if (-not $keyLine -or -not ($keyLine -split '=', 2)[1]) { throw 'GEMINI_API_KEY is missing from .env' }
$env:GEMINI_API_KEY = ($keyLine -split '=', 2)[1]
python -m src.pipeline
Remove-Item Env:GEMINI_API_KEY
```

`.env` と実キーはコミットしないでください。

## 実行方法

```bash
# 全10社の実行（クロール → クリーニング → LLM抽出 → 検証 → 出力）
python -m src.pipeline

# 特定企業のみ実行（会社名は src/companies.py 参照）
python -m src.pipeline Nissui "Sakata Seed"
```

結果は `result/` に出力されます。

- `result/companies.json` — 企業ごとの4項目。各項目は
  `value` / `status`（FOUND / NOT_FOUND / CONFLICT / MULTIPLE_CANDIDATES）/
  `source_url` / `evidence`（該当ページからの引用）を持つ
- `result/companies_readable.json` — 利用者向けに会社情報をまとめたJSON。住所と代表者は配列で表示し、
  `sources` / `field_sources` / `evidence` / `statuses` で項目ごとの出典・根拠・判定を確認できる
- `result/companies.csv` — 同内容のCSV（Excel で開けるよう UTF-8 BOM 付き）

## テスト

```bash
python -m pytest -q
```

URL 正規化・ドメインポリシー・ランキング・抽出結果の検証ロジック
（設立月の推定禁止、引用と値の照合など）の単体テストが含まれます。

## 出力データのルール

- 値が見つからない項目は `status: NOT_FOUND` で明示（空文字や推測値を入れない）
- 設立「月」は年の情報だけからは推定しない（例: 「1911年」だけなら月は入れない）
- 複数の代表者・複数の本社が存在する場合は黙って1つに絞らず MULTIPLE_CANDIDATES として列挙
- すべての非null値に出典URL（source_url）とページ本文からの引用（evidence）が付く
- 抽出値が引用から裏付けられない場合は抽出を1回再試行し、それでも不正なら処理を中止して結果ファイルを更新しない

## ディレクトリ構成

```text
├── prompts/       # 生成AIとの対話履歴と抽出用システムプロンプト
├── result/        # 収集データ（JSON / CSV）
├── src/           # ソースコード
│   ├── companies.py  # 対象10社の定義
│   ├── crawler.py    # 同一ドメイン内クローラ（正規化・重複排除・再試行付き）
│   ├── urls.py       # URL正規化・ドメインポリシー
│   ├── ranking.py    # 候補ページのキーワードランキング
│   ├── cleaner.py    # HTML から本文テキストへのクリーニング
│   ├── extract.py    # LLM 構造化抽出（Gemini REST / Anthropic 互換 API）
│   ├── schema.py     # pydantic スキーマと決定的バリデーション
│   └── pipeline.py   # 全体のパイプライン
├── tests/         # 単体テスト
├── README.md      # このファイル
└── report.md      # 技術選定の比較と課題Bの報告
```

## 注意事項

- 社内プロキシ環境（TLS 介入）では `truststore` が自動的にシステム証明書ストアを使用します
- 対象サイトは尊重し、1リクエストごとに遅延を入れ、ページ数・深さに上限を設けています
