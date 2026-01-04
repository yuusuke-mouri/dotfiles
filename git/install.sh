#!/bin/bash
#
# Git configuration installer
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="$HOME/.gitconfig"
LOCAL_CONFIG="$HOME/.gitconfig.local"

echo "Installing git configuration..."

# Backup existing config if it's not a symlink
if [ -f "$TARGET" ] && [ ! -L "$TARGET" ]; then
    BACKUP="${TARGET}.backup.$(date +%Y%m%d%H%M%S)"
    echo "Backing up existing $TARGET to $BACKUP"
    mv "$TARGET" "$BACKUP"
fi

# Create symlink
if [ ! -L "$TARGET" ]; then
    ln -s "$SCRIPT_DIR/gitconfig" "$TARGET"
    echo "Created symlink: $TARGET -> $SCRIPT_DIR/gitconfig"
else
    echo "Symlink already exists: $TARGET"
fi

# Create local config if it doesn't exist
if [ ! -f "$LOCAL_CONFIG" ]; then
    echo "Creating $LOCAL_CONFIG for machine-specific settings..."
    cat > "$LOCAL_CONFIG" << 'EOF'
# Machine-specific git configuration
# This file is not tracked by dotfiles

[user]
    email = your-email@example.com

# Uncomment for macOS:
# [credential]
#     helper = osxkeychain

# Uncomment for Linux:
# [credential]
#     helper = store
EOF
    echo "Please edit $LOCAL_CONFIG to set your email and credentials"
else
    echo "$LOCAL_CONFIG already exists"
fi

echo "Git configuration installed!"
