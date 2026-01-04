#!/bin/bash
#
# Git configuration installer
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="$HOME/.gitconfig"
GITIGNORE_TARGET="$HOME/.gitignore_global"
LOCAL_CONFIG="$HOME/.gitconfig.local"

echo "Installing git configuration..."

# Backup and symlink gitconfig
if [ -f "$TARGET" ] && [ ! -L "$TARGET" ]; then
    BACKUP="${TARGET}.backup.$(date +%Y%m%d%H%M%S)"
    echo "Backing up existing $TARGET to $BACKUP"
    mv "$TARGET" "$BACKUP"
fi

if [ ! -L "$TARGET" ]; then
    ln -s "$SCRIPT_DIR/gitconfig" "$TARGET"
    echo "Created symlink: $TARGET -> $SCRIPT_DIR/gitconfig"
else
    echo "Symlink already exists: $TARGET"
fi

# Backup and symlink gitignore_global
if [ -f "$GITIGNORE_TARGET" ] && [ ! -L "$GITIGNORE_TARGET" ]; then
    BACKUP="${GITIGNORE_TARGET}.backup.$(date +%Y%m%d%H%M%S)"
    echo "Backing up existing $GITIGNORE_TARGET to $BACKUP"
    mv "$GITIGNORE_TARGET" "$BACKUP"
fi

if [ ! -L "$GITIGNORE_TARGET" ]; then
    ln -s "$SCRIPT_DIR/.gitignore_global" "$GITIGNORE_TARGET"
    echo "Created symlink: $GITIGNORE_TARGET -> $SCRIPT_DIR/.gitignore_global"
else
    echo "Symlink already exists: $GITIGNORE_TARGET"
fi

# Create local config if it doesn't exist
if [ ! -f "$LOCAL_CONFIG" ]; then
    echo "Creating $LOCAL_CONFIG for machine-specific settings..."
    cat > "$LOCAL_CONFIG" << 'EOF'
# Machine-specific git configuration
# This file is not tracked by dotfiles

[user]
    email = yuusuke.ap@gmail.com

[commit]
    template = ~/.stCommitMsg
EOF
    echo "Created $LOCAL_CONFIG"
else
    echo "$LOCAL_CONFIG already exists"
fi

echo "Git configuration installed!"
