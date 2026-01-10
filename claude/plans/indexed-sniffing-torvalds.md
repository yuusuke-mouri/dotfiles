# 自己情報取得APIスタブをDockerで試す

## タスク
- Backlog: [GIGI-6909](https://gigi-tokyo.backlog.com/view/GIGI-6909) [Dev] 自己情報取得APIスタブを試す
- 目的: AWS環境構築前にローカルでAPIの動作を確認する

## 使用するスタブ
**標準版（IF001）** - Webアプリからの自己情報取得API

## ディレクトリ
```
/Users/yusukemori/Library/CloudStorage/Dropbox/Gigi/マイナポータルAPI/selfinfo/
└── 【インターフェース仕様書】自己情報取得API/
    └── 自己情報取得APIインターフェース一式/
        └── (4)開発用資材/
            └── (5)スタブ/
                └── mp-api-stubv2/
                    └── mynaportal_api_stub_selfinfo/
                        └── mynaportal_api_stub_selfinfo/  ← ここ
                            ├── docker-compose.yml
                            ├── docs/
                            └── data/
```

## 実行手順

### Step 1: Docker Compose起動
```bash
cd "/Users/yusukemori/Library/CloudStorage/Dropbox/Gigi/マイナポータルAPI/selfinfo/【インターフェース仕様書】自己情報取得API/自己情報取得APIインターフェース一式/(4)開発用資材/(5)スタブ/mp-api-stubv2/mynaportal_api_stub_selfinfo/mynaportal_api_stub_selfinfo"
docker-compose up -d
```

### Step 2: 動作確認
- Swagger UI: http://localhost:8002
- API Server: http://localhost:8090

### Step 3: APIエンドポイントのテスト

| エンドポイント | メソッド | IF番号 | 説明 |
|---------------|---------|--------|------|
| `/oauth/token` | POST | IF001-03 | OAuthトークン取得 |
| `/request` | POST | IF001-04 | 自己情報取得リクエスト |
| `/result` | POST | IF001-06 | 自己情報取得結果 |

### Step 4: 停止
```bash
docker-compose down
```

## 検証内容
1. [ ] Docker Compose が正常に起動するか
2. [ ] Swagger UI (localhost:8002) にアクセスできるか
3. [ ] WireMock API (localhost:8090) が応答するか
4. [ ] 各エンドポイントにリクエストを送信し、スタブ応答を確認

## 参考ドキュメント
- 利用手順書（自己情報取得APIスタブ）.pdf
- スタブマッピング: `data/wiremock/stubs/mappings/`
- レスポンス例: `data/wiremock/stubs/__files/`
