#!/bin/bash
#
# Dotfiles installer
# Usage: ./install.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installing dotfiles..."
echo ""

# Shell configuration
if [ -f "$SCRIPT_DIR/shell/install.sh" ]; then
    echo "=== Shell ==="
    "$SCRIPT_DIR/shell/install.sh"
    echo ""
fi

# Git configuration
if [ -f "$SCRIPT_DIR/git/install.sh" ]; then
    echo "=== Git ==="
    "$SCRIPT_DIR/git/install.sh"
    echo ""
fi

# Claude Code
if [ -f "$SCRIPT_DIR/claude/install.sh" ]; then
    echo "=== Claude Code ==="
    "$SCRIPT_DIR/claude/install.sh"
    echo ""
fi

echo "All done!"
echo ""
echo "Next steps:"
echo "  1. Restart your shell or run: source ~/.bashrc (or ~/.zshrc)"
echo "  2. Edit ~/.gitconfig.local to set your email"
echo "  3. Run 'claude login' to authenticate Claude Code"
