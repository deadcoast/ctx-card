#!/bin/bash

echo "Installing minimal CTX-CARD syntax highlighting test..."

# Get VSCode extensions directory
VSCODE_EXTENSIONS_DIR="$HOME/.vscode/extensions"

# Create extension directory
EXTENSION_DIR="$VSCODE_EXTENSIONS_DIR/ctx-minimal-test"
mkdir -p "$EXTENSION_DIR"

# Copy files
cp package.json "$EXTENSION_DIR/"
mkdir -p "$EXTENSION_DIR/syntaxes"
cp syntaxes/ctx.tmLanguage.json "$EXTENSION_DIR/syntaxes/"

echo "Minimal test files copied to: $EXTENSION_DIR"
echo ""
echo "To test:"
echo "1. Restart Cursor IDE"
echo "2. Open minimal-test.ctx"
echo "3. Check if basic highlighting works:"
echo "   - Comments should be GREEN"
echo "   - Tags (ID:, AL:, etc.) should be BLUE"
echo "   - Indices (#1, #1.#1) should be LIGHT GREEN"
echo ""
echo "If this minimal test works, we know the issue is with the complex grammar."
echo "If it doesn't work, the issue is with Cursor IDE configuration."
