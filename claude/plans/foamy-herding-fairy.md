# マイナポータルAPIアクセスシステム Docker開発環境 設計プラン

## 概要

GOCHIプラットフォームから独立したネットワーク上に、マイナポータルAPI連携用の開発環境を構築する。

## 技術スタック

| 項目 | 選定 |
|------|------|
| 言語 | Python 3.11 |
| フレームワーク | FastAPI |
| HTTPクライアント | httpx (async対応) |
| バリデーション | Pydantic |
| APIドキュメント | 自動生成 (Swagger UI) |
| コンテナ | Docker + docker-compose |

## アーキテクチャ

```
┌─────────────────────────────────────────────────────────────────────┐
│  myna-network (新規作成・独立したネットワーク)                         │
│                                                                     │
│  ┌─────────────┐    ┌─────────────────────┐    ┌─────────────────┐ │
│  │ swagger-ui  │    │  myna-api-gateway   │    │    wiremock     │ │
│  │ :8002       │    │  :8100              │    │    :8090        │ │
│  │             │    │  (FastAPI)          │    │                 │ │
│  │ WireMock    │    │                     │───→│ 自己情報取得API  │ │
│  │ API仕様確認  │    │ ユーザー申告情報     │    │ スタブ          │ │
│  └─────────────┘    │ 確認機能            │    └─────────────────┘ │
│                     │                     │                        │
│  ┌─────────────┐    │ 自動生成Swagger UI  │                        │
│  │ :8100/docs  │←───│ /docs              │                        │
│  └─────────────┘    └─────────────────────┘                        │
│                              ↑                                     │
└──────────────────────────────│─────────────────────────────────────┘
                               │ HTTP API
┌──────────────────────────────│─────────────────────────────────────┐
│  gochimeshi-net (既存)       │                                     │
│                              │                                     │
│  ┌─────────────┐    ┌────────┴────────┐                           │
│  │  api-java   │    │ web-app-client  │                           │
│  │  :8080      │    │ :3010           │                           │
│  └─────────────┘    └─────────────────┘                           │
└─────────────────────────────────────────────────────────────────────┘
```

## ディレクトリ構成

```
/Users/yusukemori/dev/git-2.1steam.com/gochimeshi/
├── myna-api-gateway/                    # 新規作成
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                          # FastAPIエントリーポイント
│   ├── config.py                        # 設定管理
│   ├── routers/
│   │   └── verification.py              # /api/v1/myna/* エンドポイント
│   ├── services/
│   │   ├── myna_portal_api.py           # マイナポータルAPI呼び出し
│   │   └── verification_service.py      # 判定ロジック
│   ├── schemas/
│   │   ├── requests.py                  # リクエストDTO
│   │   └── responses.py                 # レスポンスDTO
│   └── tests/
│       └── test_verification.py         # 単体テスト
│
├── myna-docker/                         # 新規作成
│   ├── docker-compose.yml               # マイナポータル開発環境用
│   ├── docs/                            # OpenAPI仕様（WireMock用）
│   │   └── openapi.yaml
│   └── wiremock/                        # スタブデータ（コピー）
│       ├── stubs/
│       │   ├── mappings/
│       │   └── __files/
│       └── extensions/
│
└── (既存ディレクトリ...)
```

## docker-compose.yml (myna-docker/)

```yaml
version: '3.8'

services:
  # マイナポータルAPIスタブ（WireMock）
  wiremock:
    image: wiremock/wiremock:2.35.0-alpine
    container_name: myna-wiremock
    command: >
      --extensions org.wiremock.webhooks.Webhooks
      --local-response-templating
      --verbose
      --enable-stub-cors
    ports:
      - "8090:8080"
    volumes:
      - ./wiremock/stubs:/home/wiremock
      - ./wiremock/extensions:/var/wiremock/extensions
    networks:
      - myna-network

  # WireMock API仕様確認用 Swagger UI
  swagger-ui:
    image: swaggerapi/swagger-ui:v4.15.5
    container_name: myna-swagger-ui
    ports:
      - "8002:8080"
    volumes:
      - ./docs:/usr/share/nginx/html/docs
    environment:
      - URL=./docs/openapi.yaml
    networks:
      - myna-network

  # マイナポータルAPIアクセスシステム（FastAPI）
  myna-api-gateway:
    build:
      context: ../myna-api-gateway
      dockerfile: Dockerfile
    container_name: myna-api-gateway
    ports:
      - "8100:8000"
    environment:
      - MYNA_PORTAL_API_BASE_URL=http://wiremock:8080
      - MYNA_PORTAL_CLIENT_ID=SP12345678_AB1234
      - MYNA_PORTAL_REDIRECT_URI=https://gochi.online/callback
    volumes:
      - ../myna-api-gateway:/app  # 開発時ホットリロード用
    depends_on:
      - wiremock
    networks:
      - myna-network

networks:
  myna-network:
    driver: bridge
    name: myna-network
```

## Dockerfile (myna-api-gateway/)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 依存関係インストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコピー
COPY . .

# FastAPI起動（開発モード：ホットリロード有効）
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

## requirements.txt

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
httpx==0.26.0
pydantic==2.5.3
pydantic-settings==2.1.0
python-dotenv==1.0.0
pytest==7.4.4
pytest-asyncio==0.23.3
```

## API設計 (myna-api-gateway)

### エンドポイント

| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/api/v1/myna/verify` | ユーザー申告情報確認（メイン） |
| GET | `/api/v1/myna/health` | ヘルスチェック |
| GET | `/docs` | Swagger UI（自動生成） |
| GET | `/redoc` | ReDoc（自動生成） |

### POST /api/v1/myna/verify

**リクエスト:**
```json
{
  "authorization_code": "xxx",
  "redirect_uri": "https://gochi.online/callback"
}
```

**レスポンス（成功）:**
```json
{
  "success": true,
  "verification": {
    "child_welfare_allowance": true,
    "mother_child_facility": false,
    "municipality": "福岡県福岡市"
  },
  "verified_at": "2026-01-08T12:00:00Z"
}
```

**レスポンス（資格なし）:**
```json
{
  "success": true,
  "verification": {
    "child_welfare_allowance": false,
    "mother_child_facility": false,
    "municipality": "福岡県福岡市"
  },
  "verified_at": "2026-01-08T12:00:00Z"
}
```

## 内部処理フロー

```
POST /api/v1/myna/verify
    │
    ▼
┌─────────────────────────────────────────┐
│ 1. OAuthトークン取得                      │
│    POST /oauth/token                     │
│    → access_token 取得                   │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│ 2. 自己情報取得リクエスト                  │
│    POST /request                         │
│    → process_id 取得                     │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│ 3. 結果取得                              │
│    POST /result                          │
│    → selfPersonalData 取得               │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│ 4. 判定ロジック                           │
│    - 児童扶養手当: 支給期間内か？          │
│    - 母子生活支援施設: 保護期間内か？       │
└─────────────────────────────────────────┘
    │
    ▼
  レスポンス返却
```

## 実装ステップ

### Phase 1: 基盤構築
1. [ ] `myna-api-gateway/` ディレクトリ作成
2. [ ] `requirements.txt` 作成
3. [ ] `Dockerfile` 作成
4. [ ] `myna-docker/docker-compose.yml` 作成
5. [ ] WireMockスタブデータをコピー

### Phase 2: FastAPI実装
6. [ ] `main.py` - FastAPIアプリ初期化
7. [ ] `config.py` - 環境変数管理
8. [ ] `schemas/requests.py` - リクエストDTO
9. [ ] `schemas/responses.py` - レスポンスDTO
10. [ ] `services/myna_portal_api.py` - API呼び出しロジック
11. [ ] `services/verification_service.py` - 判定ロジック
12. [ ] `routers/verification.py` - エンドポイント定義

### Phase 3: テスト・検証
13. [ ] docker-compose up で環境起動
14. [ ] `/docs` でSwagger UI確認
15. [ ] curl で `/api/v1/myna/verify` テスト
16. [ ] 単体テスト実行

## 検証方法

```bash
# 1. 環境起動
cd /Users/yusukemori/dev/git-2.1steam.com/gochimeshi/myna-docker
docker-compose up -d

# 2. ログ確認
docker-compose logs -f myna-api-gateway

# 3. Swagger UI確認（ブラウザで開く）
open http://localhost:8100/docs

# 4. ヘルスチェック
curl http://localhost:8100/api/v1/myna/health

# 5. ユーザー申告情報確認テスト
curl -X POST http://localhost:8100/api/v1/myna/verify \
  -H "Content-Type: application/json" \
  -d '{
    "authorization_code": "test_code",
    "redirect_uri": "https://gochi.online/callback"
  }'

# 6. 期待されるレスポンス
# {
#   "success": true,
#   "verification": {
#     "child_welfare_allowance": true,
#     "mother_child_facility": false,
#     "municipality": "福岡県福岡市"
#   },
#   "verified_at": "2026-01-08T12:00:00Z"
# }

# 7. WireMockログ確認
docker-compose logs wiremock

# 8. 停止
docker-compose down
```

## 主要ファイル一覧（作成対象）

| ファイル | 説明 |
|---------|------|
| `myna-api-gateway/main.py` | FastAPIエントリーポイント |
| `myna-api-gateway/config.py` | 設定管理 |
| `myna-api-gateway/requirements.txt` | Python依存関係 |
| `myna-api-gateway/Dockerfile` | コンテナビルド定義 |
| `myna-api-gateway/routers/verification.py` | APIエンドポイント |
| `myna-api-gateway/services/myna_portal_api.py` | マイナポータルAPI呼び出し |
| `myna-api-gateway/services/verification_service.py` | 判定ロジック |
| `myna-api-gateway/schemas/requests.py` | リクエストDTO |
| `myna-api-gateway/schemas/responses.py` | レスポンスDTO |
| `myna-docker/docker-compose.yml` | Docker Compose定義 |
| `myna-docker/wiremock/` | スタブデータ（コピー） |

## 備考

- 既存の gochimeshi-net とは別ネットワーク（myna-network）で構築
- GOCHIプラットフォームからは HTTP API（localhost:8100）でアクセス
- FastAPI自動生成のSwagger UI（localhost:8100/docs）で動作確認可能
- 本番環境では AWS ECS + mTLS 構成が必要（別途設計）
