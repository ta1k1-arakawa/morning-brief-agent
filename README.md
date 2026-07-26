# Morning Brief Agent

Google Calendar、Gmail、Todoistに分散している情報を集め、OpenAI APIで
「今日やるべきこと」を整理して、毎朝Slackへ通知する個人用エージェントです。

## できること

- Google Calendarから今日の予定を取得する
- Gmailから未読または重要なメールの概要を取得する
- Todoistから今日・期限切れ・高優先度のタスクを取得する
- OpenAI APIで日本語の行動サマリーを作る
- Slack Incoming Webhookへサマリーを送る
- GitHub Actionsで毎朝自動実行する

Gmailの本文全文は取得しません。送信者、件名、受信日時、スニペットだけを
朝のブリーフに利用します。

## 必要なもの

- Python 3.11以上
- OpenAI APIキー
- Slack Incoming Webhook URL
- Todoist APIトークン
- Google Cloudで作成したデスクトップアプリ用OAuthクライアント

Google Cloudでは、Google Calendar APIとGmail APIを有効にしてください。
OAuthクライアントのJSONファイルは、このリポジトリのルートへ
`credentials.json` などの名前で保存します。このファイルはアプリ自体を識別する
ためのものなので、CalendarとGmailで共通のファイルを利用できます。

CalendarとGmailは別々のGoogleアカウントで利用できます。OAuth同意画面が
テスト状態の場合は、両方のアカウントをテストユーザーとして登録してください。

## セットアップ

PowerShellで以下を実行します。

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

次に、リポジトリのルートへ `.env` を作ります。

```dotenv
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5-mini
SLACK_WEBHOOK_URL=
TODOIST_API_TOKEN=
GOOGLE_CLIENT_SECRET_FILE=credentials.json
GOOGLE_CALENDAR_TOKEN_FILE=calendar_token.json
GMAIL_TOKEN_FILE=gmail_token.json
APP_TIMEZONE=Asia/Tokyo
GMAIL_MAX_RESULTS=10
REQUEST_TIMEOUT_SECONDS=30
```

空欄には自分の秘密情報を設定してください。引用符は基本的に不要です。

### 環境変数

| 名前 | 必須 | 内容 | 既定値 |
| --- | --- | --- | --- |
| `OPENAI_API_KEY` | はい | OpenAI APIキー | なし |
| `OPENAI_MODEL` | いいえ | サマリー生成に使うモデル | `gpt-5-mini` |
| `SLACK_WEBHOOK_URL` | はい | Slack Incoming Webhook URL | なし |
| `TODOIST_API_TOKEN` | はい | Todoist APIトークン | なし |
| `GOOGLE_CLIENT_SECRET_FILE` | はい | Google OAuthクライアントJSONのパス | なし |
| `GOOGLE_CALENDAR_TOKEN_FILE` | いいえ | Calendarアカウントの認証トークン保存先 | `calendar_token.json` |
| `GMAIL_TOKEN_FILE` | いいえ | Gmailアカウントの認証トークン保存先 | `gmail_token.json` |
| `APP_TIMEZONE` | いいえ | 日付判定に使うタイムゾーン | `Asia/Tokyo` |
| `GMAIL_MAX_RESULTS` | いいえ | 取得するメールの最大件数 | `10` |
| `REQUEST_TIMEOUT_SECONDS` | いいえ | 外部API通信のタイムアウト秒数 | `30` |

OSの環境変数と `.env` の両方に同じ名前がある場合は、OSの環境変数が
優先されます。

## Googleの初回認証

初回実行時は、CalendarとGmailの認証のためにブラウザが順番に開きます。

1. Calendarで使うGoogleアカウントへログインし、Calendarの読み取り権限を許可する
2. Gmailで使うGoogleアカウントへログインし、Gmailの読み取り権限を許可する

アカウントを選択するときは、サービスごとに正しいアカウントであることを確認して
ください。認証が完了すると、次の2ファイルが作られます。

- `calendar_token.json`
- `gmail_token.json`

2回目以降はそれぞれのトークンファイルを使います。有効期限が切れたアクセス
トークンは、可能な場合に自動更新します。

## 実行方法

仮想環境を有効にして実行します。

```powershell
morning-brief
```

または、Pythonモジュールとして実行できます。

```powershell
python -m morning_brief.main
```

コードを確認するときはRuffを使います。

```powershell
ruff check src
```

## 処理の流れ

```text
Google Calendar ─┐
Gmail ───────────┼─> 情報収集 ─> プロンプト作成 ─> OpenAI ─> Slack
Todoist ─────────┘
```

一部のサービスから取得できなかった場合、その失敗を記録し、取得できた情報で
ブリーフの生成を続けます。

## GitHub Actions

自動実行では `.env` を使わず、GitHubリポジトリの
`Settings > Secrets and variables > Actions` に秘密情報を登録します。

登録するSecretsは次のとおりです。

- `OPENAI_API_KEY`
- `SLACK_WEBHOOK_URL`
- `TODOIST_API_TOKEN`
- `GOOGLE_CLIENT_SECRET_JSON`
- `GOOGLE_CALENDAR_TOKEN_JSON`
- `GMAIL_TOKEN_JSON`

`GOOGLE_CLIENT_SECRET_JSON` にはOAuthクライアントJSON、
`GOOGLE_CALENDAR_TOKEN_JSON` と `GMAIL_TOKEN_JSON` には、ローカルの初回認証で
作成された対応するトークンファイルの内容を登録します。ワークフローは実行時に
一時ファイルへ復元して利用します。

GitHub ActionsのcronはUTC基準です。日本時間で設定するときは、UTCとの時差を
考慮してください。

## セキュリティ

- APIキー、Webhook URL、Google認証JSONをコードへ直接書かないでください。
- `.env`、`credentials.json`、`calendar_token.json`、`gmail_token.json` はGitへ
  コミットしないでください。
- Slackへ送るチャンネルには、必要な人だけがアクセスできるようにしてください。
- Gmail本文を推測したり、取得していない情報を断定したりしません。
- 認証情報を誤って公開した場合は、該当サービスで直ちに無効化・再発行してください。

秘密情報に該当するファイルは `.gitignore` で除外されています。ただし、
コミット前に `git status` を確認する習慣も大切です。
