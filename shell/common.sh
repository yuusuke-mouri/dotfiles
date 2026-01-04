#!/bin/bash
# ~/dotfiles/shell/common.sh
# Shared shell configuration (sourced by both bash and zsh)

# === Aliases ===
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias ..='cd ..'
alias ...='cd ../..'

# === Environment Variables ===
export EDITOR=vim
export LANG=en_US.UTF-8

# === PATH ===
# Homebrew (macOS Apple Silicon)
if [[ -d /opt/homebrew/bin ]]; then
  export PATH="/opt/homebrew/bin:$PATH"
fi

# === nvm ===
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"

# === SDKMAN (must be at end) ===
export SDKMAN_DIR="$HOME/.sdkman"
[[ -s "$HOME/.sdkman/bin/sdkman-init.sh" ]] && source "$HOME/.sdkman/bin/sdkman-init.sh"

# === OS Specific ===
case "$(uname -s)" in
  Linux*)
    # WSL/Linux specific
    alias grep='grep --color=auto'
    alias fgrep='fgrep --color=auto'
    alias egrep='egrep --color=auto'
    export PLAYWRIGHT_BROWSERS_PATH=$HOME/.cache/ms-playwright
    export PLAYWRIGHT_BROWSER=chromium

    # Google Cloud SDK
    if [ -f "$HOME/google-cloud-sdk/path.bash.inc" ]; then
      source "$HOME/google-cloud-sdk/path.bash.inc"
    fi
    if [ -f "$HOME/google-cloud-sdk/completion.bash.inc" ]; then
      source "$HOME/google-cloud-sdk/completion.bash.inc"
    fi
    ;;
  Darwin*)
    # macOS specific
    alias ls='ls -G'
    ;;
esac
