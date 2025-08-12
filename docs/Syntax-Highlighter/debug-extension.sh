#!/bin/bash

echo "=== CTX-CARD Syntax Highlighter Debug Script ==="
echo ""

echo "1. Checking installed extensions..."
ls -la ~/.vscode/extensions/ | grep ctx
echo ""

echo "2. Checking extension files..."
echo "ctx-card-syntax-test:"
ls -la ~/.vscode/extensions/ctx-card-syntax-test/
echo ""

echo "ctx-minimal-test:"
ls -la ~/.vscode/extensions/ctx-minimal-test/
echo ""

echo "ctx-card-syntax-dev:"
ls -la ~/.vscode/extensions/ctx-card-syntax-dev/
echo ""

echo "3. Checking grammar file syntax..."
if command -v jq &> /dev/null; then
    echo "Validating JSON syntax..."
    jq empty ~/.vscode/extensions/ctx-card-syntax-test/syntaxes/ctx.tmLanguage.json 2>/dev/null && echo "✅ JSON syntax is valid" || echo "❌ JSON syntax error"
else
    echo "jq not available, skipping JSON validation"
fi
echo ""

echo "4. Checking Cursor IDE cache..."
ls -la ~/Library/Application\ Support/Cursor/User/workspaceStorage/ | head -5
echo ""

echo "5. Testing with VSCode..."
echo "Opening test file in VSCode..."
code docs/Syntax-Highlighter/extension-dev/test.ctx &
echo ""

echo "6. Manual testing steps:"
echo "   a) Restart Cursor IDE completely"
echo "   b) Open test.ctx file"
echo "   c) Press Cmd+Shift+P and type 'Change Language Mode'"
echo "   d) Select 'CTX-CARD' or 'ctx'"
echo "   e) Check if syntax highlighting appears"
echo ""

echo "7. If still not working:"
echo "   - Try opening the file in regular VSCode instead of Cursor"
echo "   - Check if Cursor has extension loading disabled"
echo "   - Try creating a new workspace and testing there"
echo ""

echo "8. Test files available:"
echo "   - docs/Syntax-Highlighter/extension-dev/test.ctx"
echo "   - docs/Syntax-Highlighter/minimal-test/minimal-test.ctx"
echo "   - docs/Syntax-Highlighter/comprehensive-test.ctx"
echo ""

echo "=== Debug Complete ==="
