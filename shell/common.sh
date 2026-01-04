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
# Note: brew shellenv should be in .zprofile for login shells
if [[ -d /opt/homebrew/bin ]] && [[ ":$PATH:" != *":/opt/homebrew/bin:"* ]]; then
  export PATH="/opt/homebrew/bin:$PATH"
fi

# === asdf ===
# Skip if already loaded (e.g., from .zprofile)
if [[ -z "$ASDF_DIR" ]] && [[ -f /opt/homebrew/opt/asdf/libexec/asdf.sh ]]; then
  . /opt/homebrew/opt/asdf/libexec/asdf.sh
fi

# === Java ===
if [[ -x /usr/libexec/java_home ]]; then
  export JAVA_HOME=$(/usr/libexec/java_home -v 17 2>/dev/null)
  if [[ -n "$JAVA_HOME" ]]; then
    export PATH=$JAVA_HOME/bin:$PATH
  fi
fi

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

    # MySQL client
    if [[ -d /opt/homebrew/opt/mysql-client/bin ]]; then
      export PATH="/opt/homebrew/opt/mysql-client/bin:$PATH"
    fi

    # Windsurf
    if [[ -d "$HOME/.codeium/windsurf/bin" ]]; then
      export PATH="$HOME/.codeium/windsurf/bin:$PATH"
    fi

    # Antigravity
    if [[ -d "$HOME/.antigravity/antigravity/bin" ]]; then
      export PATH="$HOME/.antigravity/antigravity/bin:$PATH"
    fi

    # Kiro
    if [[ "$TERM_PROGRAM" == "kiro" ]]; then
      [[ -f "$(kiro --locate-shell-integration-path zsh 2>/dev/null)" ]] && . "$(kiro --locate-shell-integration-path zsh)"
    fi

    # OrbStack
    [[ -f ~/.orbstack/shell/init.zsh ]] && source ~/.orbstack/shell/init.zsh 2>/dev/null
    ;;
esac
