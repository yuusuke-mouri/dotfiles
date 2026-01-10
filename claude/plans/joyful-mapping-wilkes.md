# Slack + Backlog MCP Integration 設計プラン

## 構成

```
┌──────────────────────────────────────────────┐
│              Claude Code                     │
├──────────────────────────────────────────────┤
│  gigi-mcp-server (Python自作・統合サーバー)    │
│  ├─ Slack連携 + ローカルDB (SQLite)          │
│  ├─ Backlog連携                              │
│  └─ 既読管理                                 │
├──────────────────────────────────────────────┤
│  スキル（/slack-tasks, /slack-to-backlog, etc.）
└──────────────────────────────────────────────┘
```

## 作成ファイル

### 1. 環境設定
- `.env.example` - 環境変数テンプレート
- `setup.md` - MCP設定手順

### 2. 統合MCPサーバー (Python)
```
gigi_mcp/
├── server.py          # MCPサーバー本体
├── slack/
│   ├── client.py      # Slack API クライアント
│   └── sync.py        # メッセージ同期処理
├── backlog/
│   └── client.py      # Backlog API クライアント
├── db/
│   ├── models.py      # SQLAlchemy モデル
│   ├── repository.py  # データアクセス層
│   └── migrations/    # DBマイグレーション
└── pyproject.toml
```

### 3. Claude Codeスキル
- `.claude/skills/slack-tasks.md` - タスク抽出
- `.claude/skills/slack-reply.md` - 回答案生成
- `.claude/skills/slack-summary.md` - チャンネル要約
- `.claude/skills/slack-to-backlog.md` - Slack→Backlog課題作成
- `.claude/skills/backlog-status.md` - 担当課題確認
- `.claude/skills/slack-sync.md` - メッセージ同期実行

## 実装ステップ

### Phase 1: 基盤構築
1. `.env.example`作成（Slack + Backlog認証情報）
2. SQLiteデータベース設計・実装
   - messages テーブル（メッセージ蓄積）
   - read_status テーブル（既読管理）
   - sync_history テーブル（同期履歴）
3. Slack連携実装
   - API クライアント
   - メッセージ同期処理
   - 既読マーク機能
4. Backlog連携実装
   - 課題CRUD
   - コメント追加

### Phase 2: MCPサーバー実装
5. MCPサーバー本体（全ツール統合）
6. MCPサーバー設定ガイド作成

### Phase 3: スキル実装
7. 全スキルファイル作成
8. 動作確認

## MCPサーバー仕様

### Slack Tools
| Tool | 説明 |
|------|------|
| `slack_sync` | メッセージをローカルDBに同期（チャンネル指定可） |
| `slack_search` | ローカルDB内のメッセージ検索（オフライン対応） |
| `slack_get_unread` | 未読（未処理）メッセージ一覧取得 |
| `slack_mark_read` | メッセージを既読（処理済み）にマーク |
| `slack_get_channels` | チャンネル一覧取得 |
| `slack_post_message` | メッセージ送信 |
| `slack_get_stats` | メッセージ統計（件数、傾向等） |

### Backlog Tools
| Tool | 説明 |
|------|------|
| `backlog_create_issue` | 課題作成（件名、詳細、担当者、期限） |
| `backlog_update_issue` | 課題更新（ステータス、担当者変更等） |
| `backlog_get_issues` | 課題一覧取得（フィルタ: 担当者、ステータス、期限） |
| `backlog_get_issue` | 課題詳細取得 |
| `backlog_add_comment` | コメント追加（Slackリンク付き対応） |

### 環境変数
```
# Slack
SLACK_BOT_TOKEN=xoxb-...
SLACK_TEAM_ID=T...

# Backlog
BACKLOG_SPACE=xxx
BACKLOG_API_KEY=...

# Local DB
GIGI_DB_PATH=~/.gigi-mcp/data.db
```

## DBスキーマ

### messages
| Column | Type | 説明 |
|--------|------|------|
| id | TEXT | Slack message ts |
| channel_id | TEXT | チャンネルID |
| user_id | TEXT | 送信者ID |
| text | TEXT | メッセージ本文 |
| thread_ts | TEXT | スレッド親ts |
| created_at | DATETIME | 投稿日時 |
| synced_at | DATETIME | 同期日時 |

### read_status
| Column | Type | 説明 |
|--------|------|------|
| message_id | TEXT | メッセージID (FK) |
| is_read | BOOLEAN | 既読フラグ |
| read_at | DATETIME | 既読日時 |

### sync_history
| Column | Type | 説明 |
|--------|------|------|
| id | INTEGER | PK |
| channel_id | TEXT | チャンネルID |
| synced_at | DATETIME | 同期日時 |
| message_count | INTEGER | 同期件数 |

## スキル仕様

### /slack-tasks
- 未読メッセージからタスク・依頼・質問を抽出
- 優先度・期限があれば付記

### /slack-reply
- メンションへの回答案を複数パターン生成

### /slack-summary
- チャンネルの直近メッセージを要約

### /slack-to-backlog
- Slackメッセージを指定してBacklog課題作成
- Slackリンクを課題説明に含める
- 必要に応じてコメントも転記

### /backlog-status
- 自分の担当課題一覧表示
- 期限が近い課題をハイライト
