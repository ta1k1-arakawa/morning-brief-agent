# Morning Brief Agent Project Context

このファイルは、新しい Codex 会話でもプロジェクトの前提をすぐ復元できるようにするための記録です。
作業を再開するときは、まずこのファイルを読むこと。

## 目的

Morning Brief Agent は、Google Calendar、Gmail、Todoist から当日の予定・メール・タスクを取得し、OpenAI API で「今日やるべきこと」を整理して、毎朝 Slack に通知するパーソナル AI エージェントです。

目的は、予定・メール・タスクが別サービスに分散している状態を解消し、朝の時点で「今日何を優先すべきか」を一目で把握できるようにすることです。

## MVP の範囲

最初の実装では、以下を作ります。

- Slack にテスト通知を送る
- Todoist から今日のタスクを取得する
- Google Calendar から今日の予定を取得する
- Gmail から未読メールの件名・送信者・スニペットを取得する
- OpenAI API で今日の行動サマリーを生成する
- GitHub Actions で毎朝自動実行する

MCP サーバー化や Web アプリ化は、最初の範囲には含めません。

## 作業方針

- `tests/` フォルダは作らない。
- 1ファイルずつ作り、ユーザーがコードを見る。OK なら次に進む。
- まず実用的な MVP を完成させる。
- 外部 API の秘密情報はコードに直接書かない。
- `.env` はローカル用。Git 管理しない。
- GitHub Actions では GitHub Secrets から環境変数を渡す。
- Gmail 本文全文は最初から取得しない。送信者・件名・受信日時・スニペット中心にする。
- OpenAI API や Slack 通知に、過度に詳細な個人情報を渡さない。

## 全体の処理の流れ

```text
GitHub Actions
↓
main.py
↓
collector.py
↓
google_calendar.py / gmail.py / todoist.py
↓
prompt_builder.py
↓
summarizer.py
↓
openai_client.py
↓
slack.py
↓
Slack 通知
```

## 現在のディレクトリ方針

```text
morning-brief-agent/
├─ PROJECT_CONTEXT.md
├─ README.md
├─ pyproject.toml
├─ .env
├─ .gitignore
├─ src/
│  └─ morning_brief/
│     ├─ __init__.py
│     ├─ main.py
│     ├─ config.py
│     ├─ models.py
│     ├─ services/
│     │  ├─ google_calendar.py
│     │  ├─ gmail.py
│     │  ├─ todoist.py
│     │  ├─ openai_client.py
│     │  └─ slack.py
│     ├─ core/
│     │  ├─ collector.py
│     │  ├─ prompt_builder.py
│     │  └─ summarizer.py
│     └─ utils/
│        ├─ datetime_utils.py
│        └─ logging.py
└─ .github/
   └─ workflows/
      └─ daily.yml
```

`tests/` は作らない。

## 実装順序と再開ルール

今後は「作ったファイル」「まだ作っていないファイル」のリストを毎回更新しない。
代わりに、下の順番を固定の実装順序として扱う。

作業を再開するときは、次のルールに従う。

1. この順番を上から確認する。
2. すでに存在するファイルはスキップする。
3. 最初に存在しないファイルが、その日の開始地点。
4. ファイルが存在していても、未完成そうなら中身を読んで続きから直す。
5. 1ファイル作ったら止まり、ユーザーに解説する。

### 実装順序

1. `.gitignore`  
   `.env`、仮想環境、Python キャッシュ、Google 認証トークン、ログなどを Git 管理しないための設定。

2. `.env`  
   ローカル開発用の環境変数ファイル。Git では無視される。

3. `src/morning_brief/__init__.py`  
   `morning_brief` を Python パッケージとして扱うための入口。

4. `src/morning_brief/models.py`  
   `CalendarEvent`、`EmailItem`、`TodoistTask`、`DailyBriefing` など、アプリ内で扱うデータ構造を定義する。

5. `src/morning_brief/config.py`  
   `.env` と `os.environ` の両方から設定を読む。`os.environ` を優先する。

6. `src/morning_brief/core/collector.py`  
   Calendar、Gmail、Todoist から情報を集めて、1つのデータ構造にまとめる。

7. `src/morning_brief/core/prompt_builder.py`  
   予定・メール・タスクを OpenAI に渡すプロンプト文字列に変換する。

8. `src/morning_brief/core/summarizer.py`  
   `PromptBuilder` でプロンプトを作り、`OpenAIClient` に渡してサマリーを生成する。

9. `src/morning_brief/utils/datetime_utils.py`  
   日本時間の今日・明日・Calendar API 用の時刻範囲を作る。

10. `src/morning_brief/utils/logging.py`  
    GitHub Actions やローカル実行で見やすいログ設定をまとめる。

11. `src/morning_brief/services/slack.py`  
    Slack Incoming Webhook にメッセージを送る。

12. `src/morning_brief/services/openai_client.py`  
    OpenAI API にプロンプトを送り、生成されたサマリーを受け取る。

13. `src/morning_brief/services/todoist.py`  
    Todoist API から今日のタスク、期限切れタスク、優先度の高いタスクを取得する。

14. `src/morning_brief/services/google_calendar.py`  
    Google Calendar API から今日・明日の予定を取得する。

15. `src/morning_brief/services/gmail.py`  
    Gmail API から未読メールや重要そうなメールの送信者・件名・受信日時・スニペットを取得する。

16. `src/morning_brief/main.py`  
    アプリ全体の入口。設定読み込み、サービス組み立て、収集、要約、Slack 通知をつなぐ。

17. `pyproject.toml`  
    Python バージョン、依存ライブラリ、formatter/linter などのプロジェクト設定を書く。

18. `README.md`  
    プロジェクト説明、セットアップ方法、環境変数、実行方法、GitHub Actions、セキュリティ方針を書く。

19. `.github/workflows/daily.yml`  
    GitHub Actions で毎朝自動実行する設定を書く。

20. `src/morning_brief/main.py` の `build_services()` 接続  
    実装済みの各サービスを `AppServices` に組み込む。

## 再開時の Codex への指示例

新しい会話で作業を再開するときは、次のように頼むとよい。

```text
PROJECT_CONTEXT.md を読んで、続きから1ファイルずつ実装してください。
tests フォルダは作らないでください。
まず次に作るべきファイルを書いて、そのあと一から分かりやすく解説してください。
```
