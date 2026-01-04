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

# Backup and create symlink for skills
if [ -d "$CLAUDE_DIR/skills" ] && [ ! -L "$CLAUDE_DIR/skills" ]; then
    echo "Backing up existing skills to skills.bak"
    mv "$CLAUDE_DIR/skills" "$CLAUDE_DIR/skills.bak"
fi

if [ ! -L "$CLAUDE_DIR/skills" ]; then
    ln -s "$SCRIPT_DIR/skills" "$CLAUDE_DIR/skills"
    echo "Created symlink: ~/.claude/skills -> $SCRIPT_DIR/skills"
else
    echo "Symlink already exists: ~/.claude/skills"
fi

# Backup and create symlink for plans
if [ -d "$CLAUDE_DIR/plans" ] && [ ! -L "$CLAUDE_DIR/plans" ]; then
    echo "Backing up existing plans to plans.bak"
    mv "$CLAUDE_DIR/plans" "$CLAUDE_DIR/plans.bak"
fi

if [ ! -L "$CLAUDE_DIR/plans" ]; then
    ln -s "$SCRIPT_DIR/plans" "$CLAUDE_DIR/plans"
    echo "Created symlink: ~/.claude/plans -> $SCRIPT_DIR/plans"
else
    echo "Symlink already exists: ~/.claude/plans"
fi

echo ""
echo "Done! Next steps:"
echo "  1. Run 'claude login' to authenticate (required on each machine)"
echo "  2. Verify with 'ls -la ~/.claude/ | grep -E \"skills|plans\"'"
