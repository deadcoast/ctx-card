# CTX-CARD Syntax Highlighting Implementation

## Overview

This directory contains the VSCode syntax highlighting implementation for CTX-CARD (`.ctx`) files. CTX-CARD is a prefix-free, information-dense codebook format designed for AI agent context and codebase documentation.

## Files

### **Core Implementation**

- **[CTX-VSC-LANG.md](CTX-VSC-LANG.md)** - Comprehensive specification and design document
- **[syntaxes/ctx.tmLanguage.json](syntaxes/ctx.tmLanguage.json)** - VSCode TextMate grammar for syntax highlighting
- **[language-configuration.json](language-configuration.json)** - VSCode language configuration
- **[package.json](package.json)** - VSCode extension configuration
- **[install-test.sh](install-test.sh)** - Installation script for testing
- **[sample.ctx](sample.ctx)** - Sample CTX-CARD file for testing syntax highlighting
- **[test.ctx](test.ctx)** - Simple test file
- **[comprehensive-test.ctx](comprehensive-test.ctx)** - Comprehensive test file

### **Planning and Documentation**

- **[TODO](TODO)** - Comprehensive TODO list for future enhancements and additional parameters

## File Extension

- **Primary**: `.ctx`
- **Fallback**: `.ctxc` (if `.ctx` conflicts with other applications)

## Implementation Status

### **Completed**

- [x] VSCode TextMate grammar specification (FIXED)
- [x] Language configuration for editor behavior
- [x] Comprehensive syntax highlighting rules (CORRECTED)
- [x] Sample files for testing
- [x] Installation script for testing
- [x] Documentation and planning

### **In Progress**

- [ ] VSCode extension packaging
- [ ] Marketplace publication
- [ ] GitHub syntax highlighting integration

### **Planned**

- [ ] Language Server Protocol (LSP) implementation
- [ ] Advanced editor features
- [ ] Integration with other IDEs
- [ ] Community ecosystem development

## Syntax Highlighting Features

### **Supported Elements**

#### **Tags (Keywords)**

- All CTX-CARD tags: `ID:`, `AL:`, `NM:`, `MO:`, `SY:`, `SG:`, `MD:`, `ED:`, `TY:`, `IN:`, `CN:`, `ER:`, `IO:`, `DT:`, `TK:`, `PX:`, `EX:`, `RV:`, `DELTA:`

#### **Indices (Numbers)**

- Module indices: `#1`, `#2`, `#3`
- Symbol indices: `#1.#1`, `#1.#2`, `#2.#1`

#### **Relationships (Operators)**

- Arrows: `->`, `⇒`, `→`
- Pipes: `|`
- Aliases: `=>`
- Logical operators: `∧`, `∨`, `¬`, `→`, `↔`

#### **Patterns (Strings)**

- Role tags: `{svc,auth,api}`
- Regex patterns: `^[a-z_]+$`
- Quoted strings: `"string"`, `'string'`

#### **Function Signatures (Meta)**

- Signatures: `(UserCreds)->AuthToken`
- Raises: `!raises[AuthError,ValidationError]`

#### **Comments**

- Line comments: `# comment`

#### **File Paths**

- Code files: `auth/service.py`, `utils/helpers.py`

## Color Theme Integration

### **Default Color Mapping**

| Element             | Color                   | Scope                          |
| ------------------- | ----------------------- | ------------------------------ |
| Tags                | `#569CD6` (Blue)        | `keyword.control.ctx`          |
| Indices             | `#B5CEA8` (Light Green) | `constant.numeric.ctx`         |
| Relationships       | `#D4D4D4` (Light Gray)  | `keyword.operator.*.ctx`       |
| Role Tags           | `#CE9178` (Orange)      | `string.quoted.role-tags.ctx`  |
| Function Signatures | `#C586C0` (Purple)      | `meta.function.signature.ctx`  |
| Regex Patterns      | `#D7BA7D` (Yellow)      | `string.regex.ctx`             |
| Comments            | `#6A9955` (Green)       | `comment.line.number-sign.ctx` |

## Installation and Usage

### **Quick Test Installation**

```bash
# Run the installation script
cd docs/Syntax-Highlighter
./install-test.sh
```

### **Manual Installation**

1. **Copy Extension Files**

   ```bash
   # Copy to VSCode extensions directory
   cp -r docs/Syntax-Highlighter ~/.vscode/extensions/ctx-card-syntax-test/
   ```

2. **Restart VSCode**

   ```bash
   # Restart VSCode to load the extension
   code .
   ```

3. **Test Syntax Highlighting**
   ```bash
   # Open a test file
   code docs/Syntax-Highlighter/comprehensive-test.ctx
   ```

### **VSCode Extension (Future)**

```bash
# Install from marketplace (when published)
code --install-extension ctxcard.ctx-syntax
```

## Testing

### **Test the Syntax Highlighting**

1. **Open Sample File**

   ```bash
   code docs/Syntax-Highlighter/sample.ctx
   ```

2. **Verify Highlighting**

   - Tags should be blue
   - Indices should be light green
   - Role tags should be orange
   - Function signatures should be purple
   - Comments should be green

3. **Test Features**
   - Comment toggling: `Ctrl+/` (or `Cmd+/`)
   - Auto-closing brackets: `{`, `[`, `(`
   - Folding: Click on tag lines to fold sections

## Development

### **Adding New Tags**

1. **Update Grammar**

   ```json
   // In ctx.tmLanguage.json
   "match": "^(ID|AL|NM|MO|SY|SG|MD|ED|TY|IN|CN|ER|IO|DT|TK|PX|EX|RV|DELTA|NEWTAG):"
   ```

2. **Update Documentation**

   - Add to CTX-VSC-LANG.md
   - Update sample.ctx with examples

3. **Test**
   - Verify highlighting works
   - Check color theme integration

### **Extending Patterns**

1. **Add New Pattern Type**

   ```json
   // In ctx.tmLanguage.json repository
   "newpattern": {
     "patterns": [
       {
         "name": "string.newpattern.ctx",
         "match": "your-regex-pattern"
       }
     ]
   }
   ```

2. **Include in Main Patterns**
   ```json
   "patterns": [
     {
       "include": "#newpattern"
     }
   ]
   ```

## Integration with CTX-CARD Generator

### **File Extension Support**

The CTX-CARD generator should be updated to support `.ctx` extension:

```python
# In card_renderer.py
def render_card(self, ...) -> str:
    # Add --format ctx option
    if format == "ctx":
        return self._render_ctx_format(...)
    else:
        return self._render_markdown_format(...)
```

### **CLI Enhancement**

```bash
# Generate .ctx file
python -m ctxcard_gen --format ctx

# Generate .ctxc file (fallback)
python -m ctxcard_gen --format ctxc
```

## Future Enhancements

### **Language Server Protocol (LSP)**

- Semantic token support
- Code actions for tag generation
- Validation and error reporting
- Auto-completion for indices

### **Advanced Features**

- CTX-CARD diff highlighting
- Delta section folding
- Cross-reference navigation
- Schema validation

### **Integration Features**

- GitHub syntax highlighting
- Documentation site integration
- IDE plugin compatibility
- Custom theme support

## Contributing

### **Development Guidelines**

1. **Follow VSCode Standards**

   - Use TextMate grammar format
   - Follow scope naming conventions
   - Test with multiple color themes

2. **Documentation**

   - Update CTX-VSC-LANG.md for changes
   - Add examples to sample.ctx
   - Update TODO.md for new features

3. **Testing**
   - Test with sample files
   - Verify color theme compatibility
   - Check editor behavior

### **Submitting Changes**

1. **Create Feature Branch**

   ```bash
   git checkout -b feature/syntax-enhancement
   ```

2. **Make Changes**

   - Update grammar files
   - Add tests
   - Update documentation

3. **Submit Pull Request**
   - Include description of changes
   - Add screenshots if visual changes
   - Reference related issues

## Resources

### **VSCode Documentation**

- [TextMate Grammar](https://code.visualstudio.com/api/language-extensions/syntax-highlight-guide)
- [Language Configuration](https://code.visualstudio.com/api/language-extensions/language-configuration-guide)
- [Extension Development](https://code.visualstudio.com/api)

### **CTX-CARD Documentation**

- [CTX-ARCHITECTURE.md](../CTX-ARCHITECTURE.md) - CTX-CARD specification
- [PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md) - Project architecture
- [README.md](../../README.md) - Main project documentation

### **Community**

- [VSCode Marketplace](https://marketplace.visualstudio.com/)
- [GitHub Issues](https://github.com/ctxcard/ctxcard-gen/issues)
- [Discussions](https://github.com/ctxcard/ctxcard-gen/discussions)
