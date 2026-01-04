#!/bin/bash
#
# Shell configuration installer
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installing shell configuration..."

# Detect OS and set appropriate rc file
case "$(uname -s)" in
  Linux*)
    RC_FILE="bashrc"
    TARGET="$HOME/.bashrc"
    ;;
  Darwin*)
    RC_FILE="zshrc"
    TARGET="$HOME/.zshrc"
    ;;
  *)
    echo "Unknown OS, skipping shell config"
    exit 0
    ;;
esac

# Backup existing config if it's not a symlink
if [ -f "$TARGET" ] && [ ! -L "$TARGET" ]; then
    BACKUP="${TARGET}.backup.$(date +%Y%m%d%H%M%S)"
    echo "Backing up existing $TARGET to $BACKUP"
    mv "$TARGET" "$BACKUP"
fi

# Create symlink
if [ ! -L "$TARGET" ]; then
    ln -s "$SCRIPT_DIR/$RC_FILE" "$TARGET"
    echo "Created symlink: $TARGET -> $SCRIPT_DIR/$RC_FILE"
else
    echo "Symlink already exists: $TARGET"
fi

echo "Shell configuration installed!"
