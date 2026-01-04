# ~/.claude 複数マシン管理のベストプラクティス

## 現状分析

### ディレクトリ構成と分類

| ディレクトリ | サイズ | 同期すべきか | 理由 |
|------------|--------|-------------|------|
| `.credentials.json` | 433B | **絶対NG** | OAuth トークン（機密情報） |
| `statsig/` | 44KB | NG | マシン固有のセッションID |
| `session-env/` | 24KB | NG | セッション状態 |
| `ide/` | 12KB | NG | ロックファイル |
| `shell-snapshots/` | 500KB | NG | 環境変数（パス含む） |
| `debug/` | 3MB | NG | デバッグログ（パス含む） |
| `telemetry/` | 4KB | NG | テレメトリ |
| `projects/` | 45MB | △ 要検討 | 会話履歴（パス情報含む） |
| `skills/` | 25MB | **推奨** | カスタムスキル |
| `plans/` | 12KB | **推奨** | 計画ファイル |
| `todos/` | 548KB | 任意 | タスク管理 |
| `history.jsonl` | 204KB | 任意 | 会話履歴 |
| `file-history/` | 1.1MB | 任意 | ファイル版履歴 |
| `stats-cache.json` | 4KB | 任意 | 統計キャッシュ |
| `plugins/` | 2.9MB | △ 設定のみ | プラグイン |

---

## Subagent 使用時の考慮事項

### 影響を受けるディレクトリ

| ディレクトリ | Subagent による変化 | 同期の重要度 |
|------------|-------------------|-------------|
| `skills/` | Subagent が参照・活用 | **さらに重要に** |
| `plans/` | Subagent が計画を生成・参照 | **重要度上昇** |
| `todos/` | タスク量が増加 | 変わらず（ローカルで十分） |
| `debug/` | ログ量が増加 | 変わらず（同期不要） |
| `projects/` | 会話コンテキスト増加 | 変わらず（容量増大のみ） |

### 結論
- **skills/** の同期価値が最も高い（複数マシンで同じ skill を使える）
- **plans/** は subagent との連携で価値上昇の可能性
- その他のディレクトリは基本方針変わらず

---

## 推奨アプローチ: ハイブリッド管理

### 戦略概要

```
┌─────────────────────────────────────────────────────────────┐
│                    ~/.claude 管理戦略                        │
├─────────────────────────────────────────────────────────────┤
│  Tier 1: Git 管理（バージョン管理が重要）                      │
│    └── skills/                                              │
│                                                             │
│  Tier 2: クラウド同期（リアルタイム共有が便利）                 │
│    └── plans/, todos/, history.jsonl                        │
│                                                             │
│  Tier 3: ローカル専用（同期しない）                           │
│    └── .credentials.json, statsig/, debug/, etc.            │
│                                                             │
│  Tier 4: 選択的アーカイブ（必要に応じて）                      │
│    └── projects/, file-history/                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 実装方法の詳細比較

### Option 比較サマリー

| 項目 | Option A: Git+Symlink | Option B: chezmoi | Option C: Git直下 |
|-----|----------------------|-------------------|------------------|
| **初期セットアップ** | 中（symlink作成） | 高（ツール学習） | 低（git initのみ） |
| **日常運用** | 低（pull/push） | 低（apply/update） | 低（pull/push） |
| **新マシン追加** | 中（clone+symlink） | 低（init --apply） | 低（cloneのみ） |
| **機密情報分離** | 完全分離 | 暗号化可能 | .gitignore依存 |
| **競合リスク** | 低（分離） | 低（マージ機能） | 中（混在） |
| **学習コスト** | 低 | 高 | 低 |
| **将来の拡張性** | 中 | 高 | 低 |

---

### Option A: Git + Symbolic Links（推奨）

**運用の流れ**:
```
日常作業:
  1. skill 編集 → 自動的に ~/dotfiles/claude 内が更新
  2. 適宜 git commit && git push

別マシンで:
  1. git pull
  2. 自動的に ~/.claude/skills に反映（symlink経由）
```

**メリット**:
- skills のバージョン管理が可能（ロールバック可）
- 機密情報が物理的に別ディレクトリ（誤コミットしにくい）
- Claude Code の更新で ~/.claude 構造が変わっても影響を受けにくい

**デメリット**:
- 初回セットアップで symlink 作成が必要
- Windows では管理者権限または開発者モードが必要

**構成**:
```
~/dotfiles/claude/          # Git 管理
├── skills/
│   └── note-writer/
├── plans/                  # オプション
└── .gitignore

~/.claude/                  # Claude Code 管理
├── skills -> ~/dotfiles/claude/skills    # symlink
├── plans -> ~/dotfiles/claude/plans      # symlink（オプション）
├── .credentials.json       # ローカル専用（Git外）
└── ...                     # その他ローカル
```

**セットアップ手順**:
```bash
# 1. dotfiles リポジトリ作成
mkdir -p ~/dotfiles/claude
cd ~/dotfiles/claude
git init

# 2. skills を移動してシンボリックリンク作成
mv ~/.claude/skills ~/dotfiles/claude/
ln -s ~/dotfiles/claude/skills ~/.claude/skills

# 3. plans も管理する場合（オプション）
mv ~/.claude/plans ~/dotfiles/claude/
ln -s ~/dotfiles/claude/plans ~/.claude/plans

# 4. .gitignore 作成
cat << 'EOF' > .gitignore
# 機密情報は絶対に含めない
*.credentials*
*.token*

# 大きなバイナリファイル（必要に応じて）
# skills/*/corpus/**/*.png
# skills/*/corpus/**/*.jpg
EOF

# 5. コミット＆プッシュ
git add .
git commit -m "Initial: Claude Code skills"
git remote add origin <your-private-repo>
git push -u origin main
```

**別マシンでのセットアップ**:
```bash
# 1. リポジトリクローン
git clone <your-private-repo> ~/dotfiles/claude

# 2. 既存の skills があれば退避
[ -d ~/.claude/skills ] && mv ~/.claude/skills ~/.claude/skills.bak

# 3. シンボリックリンク作成
ln -s ~/dotfiles/claude/skills ~/.claude/skills
ln -s ~/dotfiles/claude/plans ~/.claude/plans  # オプション

# 4. Claude 認証（各マシンで必要）
claude login
```

**日常運用コマンド**:
```bash
# 変更を同期（編集後）
cd ~/dotfiles/claude && git add . && git commit -m "Update skills" && git push

# 他マシンの変更を取得
cd ~/dotfiles/claude && git pull
```

---

### Option B: chezmoi（高度な管理）

**運用の流れ**:
```
日常作業:
  1. ~/.claude/skills を直接編集
  2. chezmoi re-add ~/.claude/skills（変更を取り込み）
  3. chezmoi git push

別マシンで:
  1. chezmoi update（自動で pull + apply）
```

**メリット**:
- テンプレート機能でマシン固有の設定に対応可能
- 暗号化サポート（age/gpg）
- `chezmoi diff` で適用前に差分確認可能
- 複数 dotfiles を一元管理（.bashrc, .gitconfig 等と一緒に）

**デメリット**:
- 学習コストが高い
- chezmoi のインストールが各マシンで必要
- 単に skills だけ管理するにはオーバースペック

**こんな人におすすめ**:
- 既に chezmoi で dotfiles を管理している
- 複数の設定ファイルを一元管理したい
- マシンごとに微妙に設定を変えたい

**セットアップ手順**:
```bash
# 1. インストール
sh -c "$(curl -fsLS get.chezmoi.io)"

# 2. 初期化（GitHub リポジトリと連携）
chezmoi init --apply <github-username>/dotfiles

# 3. skills を管理対象に追加
chezmoi add ~/.claude/skills

# 4. plans を暗号化して追加（機密性が高い場合）
chezmoi add --encrypt ~/.claude/plans

# 5. プッシュ
chezmoi git add .
chezmoi git commit -m "Add Claude Code config"
chezmoi git push
```

**別マシンでのセットアップ**:
```bash
# 1コマンドで完了
chezmoi init --apply <github-username>/dotfiles
```

**日常運用コマンド**:
```bash
# 変更を取り込んでプッシュ
chezmoi re-add ~/.claude/skills
chezmoi git add . && chezmoi git commit -m "Update" && chezmoi git push

# 他マシンの変更を取得して適用
chezmoi update
```

---

### Option C: ~/.claude 直下で Git 管理（シンプル）

**運用の流れ**:
```
日常作業:
  1. ~/.claude 内を直接編集
  2. git add . && git commit && git push

別マシンで:
  1. git pull
```

**メリット**:
- 最もシンプル（追加ツール不要）
- symlink 不要で Windows でも簡単
- 構成がわかりやすい

**デメリット**:
- .gitignore の管理ミスで機密情報をコミットするリスク
- Claude Code の更新で新ファイルが追加された場合、.gitignore の更新が必要
- git status にノイズが多い（無視ファイルが多数）

**こんな人におすすめ**:
- とにかくシンプルに始めたい
- symlink の管理が面倒
- Git だけで完結させたい

**セットアップ手順**:
```bash
cd ~/.claude
git init

# 包括的な .gitignore を作成
cat << 'EOF' > .gitignore
# ===== 絶対に除外（機密情報）=====
.credentials.json
stats-cache.json
history.jsonl

# ===== セッション固有（同期不要）=====
session-env/
shell-snapshots/
debug/
ide/
telemetry/
statsig/
todos/

# ===== 大容量（オプションで除外）=====
projects/
file-history/

# ===== プラグイン（marketplace から再取得可能）=====
plugins/marketplaces/
plugins/repos/
plugins/known_marketplaces.json

# ===== 管理対象（コメントアウトしない）=====
# skills/        ← 同期される
# plans/         ← 同期される
# plugins/config.json
# plugins/installed_plugins.json
EOF

git add .
git commit -m "Initial commit: Claude Code config"
git remote add origin <your-private-repo>
git push -u origin main
```

**別マシンでのセットアップ**:
```bash
# 既存の .claude があればバックアップ
[ -d ~/.claude ] && mv ~/.claude ~/.claude.bak

# クローン
git clone <your-private-repo> ~/.claude

# 認証（各マシンで必要）
claude login
```

**日常運用コマンド**:
```bash
# 変更を同期
cd ~/.claude && git add . && git commit -m "Update" && git push

# 他マシンの変更を取得
cd ~/.claude && git pull
```

**注意**: 新しいマシンでは `.credentials.json` が存在しないため `claude login` が必要

---

## セキュリティ考慮事項

### 絶対にやってはいけないこと

1. **`.credentials.json` を同期・コミットしない**
   - OAuth トークンが漏洩するとアカウント乗っ取りのリスク

2. **`debug/` を公開リポジトリにプッシュしない**
   - 会話履歴にコード・認証情報が含まれる可能性

3. **`history.jsonl` を公開しない**
   - プロジェクトパス・ユーザー名が露出

### 推奨プラクティス

1. **プライベートリポジトリを使用**
   ```bash
   # GitHub で private repo を作成
   gh repo create claude-skills --private
   ```

2. **pre-commit フックで機密ファイルをブロック**
   ```bash
   # .git/hooks/pre-commit
   #!/bin/bash
   if git diff --cached --name-only | grep -qE '\.credentials|\.token'; then
     echo "ERROR: Attempting to commit credentials"
     exit 1
   fi
   ```

3. **定期的な監査**
   ```bash
   # 機密情報が含まれていないか確認
   git log --all --full-history -- "*.credentials*"
   ```

---

## マシン間の認証設定

各マシンで個別に認証が必要:

```bash
# 新しいマシンで
claude login

# または API キー使用
export ANTHROPIC_API_KEY="sk-..."
```

認証情報は OS のキーチェーンや secret manager で管理することを推奨:
- macOS: Keychain Access
- Linux: libsecret / GNOME Keyring
- Windows: Credential Manager

---

## 同期競合の回避

### 同時編集のリスク

`skills/` や `plans/` を複数マシンで同時編集すると競合が発生する可能性。

### 対策

1. **Git の場合**: プル→編集→プッシュの習慣化
   ```bash
   cd ~/dotfiles/claude && git pull
   # 作業後
   git add . && git commit -m "Update" && git push
   ```

2. **クラウド同期の場合**: Dropbox/OneDrive の競合ファイル機能に依存

3. **作業マシンの明確化**: メインマシンを決め、他は読み取り専用として運用

---

## 推奨構成まとめ

| 用途 | 推奨方法 | 理由 |
|------|---------|------|
| skills/ | Git（private repo） | バージョン管理、ロールバック可能 |
| plans/ | Git または クラウド | 軽量、頻繁に更新 |
| todos/ | ローカル or クラウド | セッション固有、同期メリット低 |
| credentials | ローカル専用 | セキュリティ必須 |
| projects/ | ローカル + 定期バックアップ | 大容量、パス依存 |

---

## 私の推奨: Option A（Git + Symlink）

### 理由

1. **安全性**: 機密情報が物理的に別ディレクトリなので誤コミットのリスクが最小
2. **運用の楽さ**: 日常は `git pull/push` だけ。skill 編集は通常通り
3. **将来の柔軟性**: Claude Code の構造変更に影響されにくい
4. **Subagent 対応**: skills の同期が確実で、どのマシンでも同じ skill を使える

### Option C を選ぶべきケース

- Windows メインで symlink が面倒
- 既存の dotfiles 管理がなく、シンプルに始めたい
- 1台のマシンでしか使わない可能性が高い

### Option B を選ぶべきケース

- 既に chezmoi で dotfiles を管理している
- 複数の設定ファイルを一元管理したい
- マシンごとの設定差分を細かく管理したい

---

## 実装ステップ（Option A の場合）

1. [ ] `~/dotfiles/claude` ディレクトリ作成
2. [ ] `~/.claude/skills` を移動
3. [ ] シンボリックリンク作成
4. [ ] .gitignore 設定
5. [ ] プライベートリポジトリにプッシュ
6. [ ] 別マシンでクローン＆シンボリックリンク設定
7. [ ] pre-commit フック設定（オプション）

## 実装ステップ（Option C の場合）

1. [ ] `~/.claude` で `git init`
2. [ ] 包括的な .gitignore 作成
3. [ ] プライベートリポジトリにプッシュ
4. [ ] 別マシンでクローン
5. [ ] `claude login` で認証
