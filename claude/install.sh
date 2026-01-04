#!/bin/bash
#
# Claude Code dotfiles installer
# Usage: ./install.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="$HOME/.claude"

echo "Installing Claude Code dotfiles..."

# Create ~/.claude if it doesn't exist
mkdir -p "$CLAUDE_DIR"

# Directories to symlink
DIRS="skills plans commands agents hooks"

for dir in $DIRS; do
    # Backup existing directory if it's not a symlink
    if [ -d "$CLAUDE_DIR/$dir" ] && [ ! -L "$CLAUDE_DIR/$dir" ]; then
        echo "Backing up existing $dir to $dir.bak"
        mv "$CLAUDE_DIR/$dir" "$CLAUDE_DIR/$dir.bak"
    fi

    # Create symlink if it doesn't exist
    if [ ! -L "$CLAUDE_DIR/$dir" ]; then
        ln -s "$SCRIPT_DIR/$dir" "$CLAUDE_DIR/$dir"
        echo "Created symlink: ~/.claude/$dir"
    else
        echo "Symlink already exists: ~/.claude/$dir"
    fi
done

echo ""
echo "Done! Run 'claude login' to authenticate (required on each machine)"
