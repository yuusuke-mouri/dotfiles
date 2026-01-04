# dotfiles

My personal configuration files for WSL (bash) and macOS (zsh).

## Setup on a new machine

```bash
git clone git@github.com:yuusuke-mouri/dotfiles.git ~/dotfiles
cd ~/dotfiles
./install.sh
```

## Structure

```
~/dotfiles/
├── install.sh          # Main installer
├── shell/
│   ├── install.sh      # Shell config installer
│   ├── common.sh       # Shared settings (both bash/zsh)
│   ├── bashrc          # Bash config (WSL/Linux)
│   └── zshrc           # Zsh config (macOS)
├── git/
│   ├── install.sh      # Git config installer
│   └── gitconfig       # Git shared settings
└── claude/
    ├── install.sh      # Claude Code installer
    ├── skills/         # Custom skills
    └── plans/          # Planning documents
```

## Machine-specific settings

These files are created locally and not tracked:

- `~/.bashrc.local` or `~/.zshrc.local` - Shell overrides
- `~/.gitconfig.local` - Git email and credentials

## Daily usage

```bash
# After editing dotfiles
cd ~/dotfiles
git add . && git commit -m "Update" && git push

# On another machine
cd ~/dotfiles && git pull
```
