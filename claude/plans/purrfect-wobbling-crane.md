# dotfiles シェル設定管理計画

## 現状

### WSL (Ubuntu)
- シェル: bash
- `.bashrc` に以下のカスタマイズ:
  - nvm (Node.js バージョン管理)
  - Google Cloud SDK
  - SDKMAN (Java バージョン管理)
  - Playwright 設定

### macOS
- シェル: zsh（macOS Catalina 以降のデフォルト）
- 設定: 未確認

---

## シェル統一について

### 選択肢

| 方針 | メリット | デメリット |
|-----|---------|-----------|
| **A: 各OSのデフォルトを維持** | 設定がシンプル、OS最適化 | 2種類の設定を管理 |
| **B: zsh に統一** | モダン、macOS標準 | WSLでzshインストール必要 |
| **C: bash に統一** | どこでも動く | macOSで非標準 |

### 推奨: A（各OSのデフォルトを維持）

**理由**:
1. OS のデフォルトシェルは最も安定
2. 共通部分は別ファイルに切り出せば管理可能
3. シェル変更はトラブルの元になりやすい

---

## 最終構成

```
~/dotfiles/
├── install.sh              # メインインストーラー
├── shell/
│   ├── install.sh          # シェル設定インストーラー
│   ├── common.sh           # 共通設定（エイリアス、関数、PATH等）
│   ├── bashrc              # bash 用設定
│   └── zshrc               # zsh 用設定
├── git/
│   ├── install.sh          # Git 設定インストーラー
│   └── gitconfig           # Git 共通設定
└── claude/
    └── ...                 # 既存
```

### 設計方針

1. **共通設定を `common.sh` に集約**
   - エイリアス（ll, la など）
   - 環境変数（PATH, EDITOR など）
   - 共通関数

2. **シェル固有設定は分離**
   - bashrc: bash 固有の設定
   - zshrc: zsh 固有の設定（プロンプト、補完など）

3. **OS 固有の設定は条件分岐**
   ```bash
   case "$(uname -s)" in
     Linux*)  # WSL/Linux 固有設定 ;;
     Darwin*) # macOS 固有設定 ;;
   esac
   ```

---

## 管理対象ファイル

### 推奨

| ファイル | 管理 | 理由 |
|---------|-----|------|
| `.bashrc` / `.zshrc` | ○ | シェル設定の本体 |
| `.gitconfig` | ○ | Git 設定（共通で使う） |
| `.vimrc` | △ | 使用している場合 |
| `.tmux.conf` | △ | 使用している場合 |

### 管理しない

| ファイル | 理由 |
|---------|------|
| `.ssh/` | 機密情報、マシン固有の鍵 |
| `.gcp/` | 認証情報 |
| `.nvm/`, `.sdkman/` | ツール自体（設定のみ管理） |

---

## 実装ステップ

### Shell
1. [ ] `~/dotfiles/shell/` ディレクトリ作成
2. [ ] `common.sh` に共通設定を抽出
3. [ ] `bashrc` を作成（WSL用）
4. [ ] `zshrc` を作成（macOS用、後で macOS から取得）
5. [ ] `shell/install.sh` を作成

### Git
6. [ ] `~/dotfiles/git/` ディレクトリ作成
7. [ ] 現在の `.gitconfig` から共通設定を抽出
8. [ ] `git/install.sh` を作成

### 仕上げ
9. [ ] メインの `install.sh` を更新
10. [ ] WSL でテスト
11. [ ] コミット＆プッシュ
12. [ ] macOS で clone & install テスト

---

## common.sh の内容案

```bash
# ~/dotfiles/shell/common.sh
# 共通シェル設定（bash/zsh 両方で読み込まれる）

# === エイリアス ===
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias ..='cd ..'
alias ...='cd ../..'

# === 環境変数 ===
export EDITOR=vim
export LANG=en_US.UTF-8

# === PATH ===
# Homebrew (macOS)
if [[ -d /opt/homebrew/bin ]]; then
  export PATH="/opt/homebrew/bin:$PATH"
fi

# === nvm ===
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# === SDKMAN ===
export SDKMAN_DIR="$HOME/.sdkman"
[[ -s "$HOME/.sdkman/bin/sdkman-init.sh" ]] && source "$HOME/.sdkman/bin/sdkman-init.sh"

# === OS 固有 ===
case "$(uname -s)" in
  Linux*)
    # WSL/Linux 固有
    alias grep='grep --color=auto'
    export PLAYWRIGHT_BROWSERS_PATH=$HOME/.cache/ms-playwright
    ;;
  Darwin*)
    # macOS 固有
    alias ls='ls -G'  # macOS の ls は --color ではなく -G
    ;;
esac
```

---

## 決定事項

- シェル方針: 各OSのデフォルト維持（WSL=bash, macOS=zsh）
- macOS: カスタマイズあり（要確認）
- .gitconfig: 管理する

---

## .gitconfig 管理方針

共通設定を dotfiles で管理し、マシン固有設定は `~/.gitconfig.local` で分離：

```gitconfig
# ~/dotfiles/git/gitconfig
[user]
    name = Your Name
    # email はマシンごとに設定（仕事/個人で異なる場合）
[core]
    editor = vim
[alias]
    st = status
    co = checkout
    br = branch
    ci = commit
[include]
    path = ~/.gitconfig.local  # マシン固有設定
```

```gitconfig
# ~/.gitconfig.local (Git管理しない、各マシンで作成)
[user]
    email = your-email@example.com
[credential]
    helper = osxkeychain  # macOS の場合
```
