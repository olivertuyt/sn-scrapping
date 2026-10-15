# レポート: 技術選定と比較

## 1. 課題の概要

- 課題A: 10社の上場企業の公式サイトをクロールし、生成AIで「本社住所・代表者名・資本金・設立年月」を抽出
- 課題B（任意）: アンチボット対策が施されたサイトからのデータ取得の試行

## 2. 比較したアプローチ

| # | アプローチ | 構成 |
|---|---|---|
| A | **Python + httpx/BeautifulSoup + 生成AI構造化抽出（採用）** | httpx(非同期不要の同期HTTP) + lxml/BeautifulSoup + Gemini REST `generateContent` API（無料枠のある Gemini 3.1 Flash-Lite） |
| B | Python + Playwright + LangChain | 実ブラウザ自動化 + LLMチェーンフレームワーク |
| C | TypeScript + Firecrawl + Vercel AI SDK | 商用クロールAPI + サーバレスLLM |
| D | Dify / n8n（ノーコード） | GUIワークフロー上でクロールと抽出を定義 |

## 3. 評価（コスト / スピード / 品質・完全性）

| 観点 | A: Python+httpx+BS4+生成AI（採用） | B: Playwright+LangChain | C: Firecrawl+Vercel AI SDK | D: Dify / n8n |
|---|---|---|---|---|
| **コスト** | 無料OSSのみ＋Gemini 3.1 Flash-Lite の無料枠を利用。インフラ不要（ローカル実行）。無料枠の上限は Google の料金表に従う。 | OSSだが Chromium バイナリと Playwright ランタイムが必要。LangChain は抽象レイヤーが過剰。 | Firecrawl は従量課金（10社でも数千円規模）＋Vercel デプロイが必要。 | SaaS課金または自己ホスト運用コスト。9時間の課題には準備が重い。 |
| **スピード** | 開発: パイプラインが単純（seed→fetch→rank→LLM→validate）で数時間で実装可能。実行: 10社×30ページを数分で完了。 | 開発: ブラウザ自動化の安定化に時間を取られる。実行: ページあたり数秒のレンダリング待ちで遅い。 | 開発: API仕様の確認のみで速い。実行: 外部API往復で速いが件数制限に依存。 | 開発: GUIでの設定と試行錯誤。実行: ワークフロー実行は速いがデバッグが困難。 |
| **品質・完全性** | URL正規化・ドメインポリシー・ランキングを自前実装でき、証拠（evidence）と出典URLの検証を決定的に行える。40項目すべてに根拠を持たせられる。 | JSレンダリングが必要なサイトでは高い。ただし本課題の10社はすべて静的HTTPで取得可能だったため、差はなかった。 | 抽出品質はLLM次第だが、evidence検証や月推定禁止などの独自ルールを組み込む自由度が低い。 | カスタムバリデーション（月推定禁止、複数代表者の明示など）の実装が困難。 |

## 4. 採用理由（まとめ）

1. **HTTPファーストで十分だった**: 10社すべて静的HTMLで必要情報に到達でき、
   ブラウザ自動化（Playwright）は不要だった。実装・実行・保守のすべてが軽い。
2. **検証可能性**: 「抽出値は必ず出典URLと引用（evidence）付き」「設立月は年のみから推定しない」
   「複数候補は黙って1つに絞らない」という課題上の厳格な要件は、
   自前の決定的バリデーション（src/schema.py）でのみ保証できる。
3. **コスト**: 追加インフラなし。Gemini 3.1 Flash-Lite の無料枠を使用し、APIキーは環境変数から渡す。
   無料枠の上限は Google の [Gemini API 料金表](https://ai.google.dev/gemini-api/docs/pricing) に従う。
4. **LangChain 等のフレームワーク不採用**: 本課題は「クロール→抽出→検証」の線形パイプラインであり、
   チェーン・エージェント・RAG の機能は不要。依存を増やすだけだと判断。

### 実行環境での技術的発見

- 社内プロキシ（Zscaler）による TLS 介入のため、Python 標準の CA バンドル（certifi）では
  検証失敗。`truststore` で Windows システム証明書ストアを使用して解決。
- プロフィール候補から公式の沿革ページをたどり、同一ドメインの年代別ページも候補に追加する。
  ニッスイはプロフィールに年のみが記載されていたため、会社Q&Aの「1943年3月31日」を出典付きで採用した。
  年代別の沿革にある別会社の設立記録を現在の会社の設立日として流用しない。

## 5. 課題B（任意）: アンチボット対策サイト

対象: https://vn.indeed.com/jobs?q=remote （2026-10-15 に実施）

### アンチボット対策の調査結果

vn.indeed.com は **Cloudflare** によるボット防御を使用している。

| 観測 | 証拠 |
|---|---|
| WAF ベンダー | 応答ヘッダー `Server: cloudflare`、`CF-RAY: a4abf472ab6efd2c-SIN` |
| ボット管理 Cookie | `Set-Cookie: __cf_bm=...; Domain=indeed.com`（30分有効のボット判定 Cookie） |
| JS チャレンジ | 403 ページ（title: `Blocked - Indeed.com`）が `/cdn-cgi/challenge-platform/scripts/jsd/main.js` を読み込み、`window.__CF$cv$params` を設定 — ブラウザでの JavaScript 実行を要求するチャレンジ |

### 試行した手法と結果

| # | 手法 | 結果 |
|---|---|---|
| 1 | 平易な UA（`python-httpx/...`）で直接 GET | **HTTP 403**（Cloudflare チャレンジ。本文 25,740 バイト、title `Blocked - Indeed.com`、`__cf_bm` cookie） |
| 2 | ブラウザ風 UA（Chrome/131）で GET | **HTTP 403**（Cloudflare、CF-Ray と `__cf_bm` cookie。本文 27,708 バイトにチャレンジパスあり） |
| 3 | 平易な UA + ブラウザ風 Accept ヘッダー（`Accept: text/html`、`Accept-Language: ja`） | **HTTP 403**（同じ Cloudflare チャレンジ、本文 25,740 バイト。ヘッダー変更では取得できない） |
| 4 | HTTP取得失敗後、JavaScriptを実行する隔離ブラウザで対象URLを開く | **取得成功**。2026-10-15付の検索結果ページ（タイトル表示「3,000+ Remote Jobs」）に15件の求人カードが表示された。見えた全カードと先頭求人の詳細を `result/indeed_remote_page1.json` に保存した。CAPTCHA は表示されず、解答や認証情報の入力は行っていない。 |

### ブラウザ取得結果のサンプル

- 求人: **NHÂN VIÊN CHĂM SÓC KHÁCH HÀNG REMOTE NHÀ**（Truyền Thông Và Giải Trí CM Việt Nam、ベトナム）
- 検索カードの給与: `15,000,000 VNĐ - 20,000,000 VNĐ a year`
- 詳細説明中の給与: `Lương: 15000K - 20000K VND một tháng`
- 同じ求人内で給与の期間が「年」と「月」で食い違っていたため、どちらかに統一せず両方をJSONに記録した。
- 15件すべてのカードに見えたタイトル、会社・勤務地表示、給与、バッジ、説明抜粋と、先頭求人の詳細パネルを `result/indeed_remote_page1.json` に記録した。
- `result/indeed_remote_sample.json` は先頭求人だけの短いサンプル。今回の2ファイルは2026-10-15の観測結果で、全3,000件超の収集結果ではない。

### 結論

- HTTP クライアントによる3回の取得試行はすべて Cloudflare の 403 チャレンジページを返した。
  応答ヘッダー、bot cookie、チャレンジ用 JavaScript の参照から Cloudflare の WAF / bot 管理を確認した。
- HTTP 失敗後に隔離ブラウザで同じユーザー指定URLを開くと、検索結果と選択求人の詳細が表示された。
  これは通常のブラウザ実行経路で確認した結果であり、CAPTCHA の解答、ログイン、アクセス制御の回避は行っていない。
- よって課題Bでは、静的HTTP取得は遮断される一方、今回のブラウザ経路では少なくとも検索結果の1ページ目を取得できた。
  全検索結果の一括取得やページネーションの収集は実施していない。

## 6. 生成AIの利用履歴

ChatGPTで行った課題翻訳・計画会話の共有リンクは `prompts/01_requirement_analysis.txt`、
ローカルで取得できたCodexの質問と回答は `prompts/07_codex_conversation_transcript.txt` に記載した。
抽出時のシステムプロンプトは `prompts/05_extraction_system_prompt.txt`、Gemini連携と実行記録は
`prompts/06_gemini_integration_and_execution.txt` にある。APIキーは記録していない。
Claude Code/GLMの実装セッションについては `prompts/03_claude_code_implementation_sessions.txt` に
使用した全プロンプトと作業要約がある（利用者確認済み）。ただしAIの回答履歴または共有リンクは
まだ取得できていない。
