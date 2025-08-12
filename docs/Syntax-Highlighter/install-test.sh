#!/bin/bash

# CTX-CARD Syntax Highlighting Test Installation Script

echo "Installing CTX-CARD syntax highlighting for testing..."

# Get VSCode extensions directory
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    VSCODE_EXTENSIONS_DIR="$HOME/.vscode/extensions"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    VSCODE_EXTENSIONS_DIR="$HOME/.vscode/extensions"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    # Windows
    VSCODE_EXTENSIONS_DIR="$APPDATA/Code/User/extensions"
else
    echo "Unknown OS type: $OSTYPE"
    exit 1
fi

# Create extension directory
EXTENSION_DIR="$VSCODE_EXTENSIONS_DIR/ctx-card-syntax-test"
mkdir -p "$EXTENSION_DIR"

# Copy files
cp package.json "$EXTENSION_DIR/"
cp language-configuration.json "$EXTENSION_DIR/"
mkdir -p "$EXTENSION_DIR/syntaxes"
cp syntaxes/ctx.tmLanguage.json "$EXTENSION_DIR/syntaxes/"
mkdir -p "$EXTENSION_DIR/snippets"
cp snippets/ctx.json "$EXTENSION_DIR/snippets/"

echo "Files copied to: $EXTENSION_DIR"
echo ""
echo "To test the syntax highlighting:"
echo "1. Restart VSCode"
echo "2. Open a .ctx file"
echo "3. Check that syntax highlighting works correctly"
echo "4. Test snippets by typing 'ctx-' and pressing Tab"
echo ""
echo "Test files available:"
echo "- test.ctx (simple test)"
echo "- comprehensive-test.ctx (full test)"
echo "- sample.ctx (example file)"
echo ""
echo "Expected highlighting:"
echo "- Tags (ID:, AL:, etc.) should be BLUE"
echo "- Indices (#1, #1.#2) should be LIGHT GREEN"
echo "- Operators (->, =>, |) should be LIGHT GRAY"
echo "- Role tags ({svc,auth}) should be ORANGE"
echo "- Function signatures should be PURPLE"
echo "- Comments should be GREEN"
echo "- Regex patterns should be YELLOW"
echo "- File paths should be highlighted"
echo "- Numbers should be highlighted"
echo ""
echo "Available snippets:"
echo "- ctx-header: Project header"
echo "- ctx-naming: Naming grammar"
echo "- ctx-module: Module definition"
echo "- ctx-symbol: Symbol definition"
echo "- ctx-signature: Function signature"
echo "- ctx-edge: Edge relationship"
echo "- ctx-datatype: Data type"
echo "- ctx-token: Token set"
echo "- ctx-invariant: Invariant"
echo "- ctx-convention: Convention"
echo "- ctx-error: Error taxonomy"
echo "- ctx-api: API contract"
echo "- ctx-prohibited: Prohibited pattern"
echo "- ctx-example: Example"
echo "- ctx-review: Review focus"
echo "- ctx-delta: Delta change"
echo "- ctx-template: Complete template"
