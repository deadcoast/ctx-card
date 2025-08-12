#!/bin/bash

# CTX-CARD Syntax Highlighting Test Installation Script

echo "Installing CTX-CARD syntax highlighting for testing..."

# Get VSCode/Cursor extensions directory
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS: prefer Cursor if present, else VSCode
    if [[ -d "$HOME/Library/Application Support/Cursor/User/globalStorage/extensions" ]]; then
        VSCODE_EXTENSIONS_DIR="$HOME/Library/Application Support/Cursor/User/globalStorage/extensions"
    else
        VSCODE_EXTENSIONS_DIR="$HOME/.vscode/extensions"
    fi
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

# Resolve script directory for reliable file paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Determine publisher.name-version so VS Code registers it
PUBLISHER=$(node -e 'try{console.log(require(process.argv[1]).publisher||"ctxcard")}catch(e){console.log("ctxcard")}' "$SCRIPT_DIR/package.json")
NAME=$(node -e 'try{console.log(require(process.argv[1]).name||"ctx-card-syntax")}catch(e){console.log("ctx-card-syntax")}' "$SCRIPT_DIR/package.json")
VERSION=$(node -e 'try{console.log(require(process.argv[1]).version||"1.0.0")}catch(e){console.log("1.0.0")}' "$SCRIPT_DIR/package.json")

EXTENSION_DIR="$VSCODE_EXTENSIONS_DIR/${PUBLISHER}.${NAME}-${VERSION}"
rm -rf "$EXTENSION_DIR"
mkdir -p "$EXTENSION_DIR/syntaxes" "$EXTENSION_DIR/snippets"

# Copy files
cp "$SCRIPT_DIR/package.json" "$EXTENSION_DIR/"
cp "$SCRIPT_DIR/language-configuration.json" "$EXTENSION_DIR/"
cp "$SCRIPT_DIR/syntaxes/ctx.tmLanguage.json" "$EXTENSION_DIR/syntaxes/"
cp "$SCRIPT_DIR/snippets/ctx.json" "$EXTENSION_DIR/snippets/"

echo "Files copied to: $EXTENSION_DIR"
echo ""
echo "Note: If using Cursor, ensure experimental extension loading is enabled."
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
