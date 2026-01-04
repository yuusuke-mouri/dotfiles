#!/bin/bash
#
# Dotfiles installer
# Usage: ./install.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installing dotfiles..."
echo ""

# Claude Code
if [ -f "$SCRIPT_DIR/claude/install.sh" ]; then
    echo "=== Claude Code ==="
    "$SCRIPT_DIR/claude/install.sh"
    echo ""
fi

# Add more installers here as needed
# if [ -f "$SCRIPT_DIR/vim/install.sh" ]; then
#     echo "=== Vim ==="
#     "$SCRIPT_DIR/vim/install.sh"
#     echo ""
# fi

echo "All done!"
