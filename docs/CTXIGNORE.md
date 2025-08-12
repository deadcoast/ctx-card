# .ctxignore File

The `.ctxignore` file allows you to specify patterns for files and directories that should be excluded from CTX-CARD generation. It works similarly to `.gitignore` but is specifically designed for CTX-CARD analysis.

## File Location

Place the `.ctxignore` file in the root directory of your project (the same directory where you run the CTX-CARD generator).

## Pattern Format

The `.ctxignore` file uses glob patterns with the following features:

### Basic Patterns

- `*.py` - Ignore all Python files
- `__pycache__/` - Ignore all `__pycache__` directories
- `*.log` - Ignore all log files
- `temp/` - Ignore the `temp` directory and all its contents

### Wildcards

- `*` - Matches any sequence of characters
- `?` - Matches any single character
- `**` - Matches any number of directories (recursive)

### Character Classes

- `[abc]` - Matches any single character from the set
- `[!abc]` - Matches any single character NOT from the set
- `[a-z]` - Matches any character in the range

### Negation

- `!pattern` - Negate a pattern (include files that would otherwise be ignored)

## Examples

### Basic .ctxignore File

```
# Python cache files
__pycache__/
*.pyc
*.pyo

# Virtual environments
.venv/
venv/
env/

# IDE files
.vscode/
.idea/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db

# Logs and temporary files
*.log
*.tmp
temp/
```

### Using Negation

```
# Ignore all Python files
*.py

# But include important ones
!important.py
!main.py
!config.py
```

### Complex Patterns

```
# Ignore all files in node_modules
node_modules/

# Ignore all TypeScript files except tests
*.ts
!*.test.ts
!*.spec.ts

# Ignore all files in build directories
**/build/
**/dist/

# Ignore specific file types
*.zip
*.tar.gz
*.db
*.sqlite
```

## Integration with CTX-CARD Generator

The `.ctxignore` file is automatically loaded when you run the CTX-CARD generator. Files matching patterns in the `.ctxignore` file will be excluded from:

- Module scanning
- Symbol extraction
- Language detection
- Import analysis
- Call resolution

## CLI Options

### Show Ignored Patterns

To see what patterns are currently being used:

```bash
python -m ctxcard_gen --show-ignored
```

This will display all patterns from the `.ctxignore` file.

### Combining with Include/Exclude

The `.ctxignore` file works in combination with the `--include` and `--exclude` options:

```bash
# Use .ctxignore AND exclude tests
python -m ctxcard_gen --exclude "**/tests/**"

# Use .ctxignore AND only include Python files
python -m ctxcard_gen --include "**/*.py"
```

## Default Patterns

The default `.ctxignore` file includes common patterns for:

- Virtual environments (`.venv/`, `venv/`, `env/`)
- Python cache files (`__pycache__/`, `*.pyc`)
- IDE and editor files (`.vscode/`, `.idea/`, `*.swp`)
- OS generated files (`.DS_Store`, `Thumbs.db`)
- Logs and temporary files (`*.log`, `*.tmp`, `temp/`)
- Build artifacts (`build/`, `dist/`, `*.egg-info/`)
- Node.js dependencies (`node_modules/`)
- Database files (`*.db`, `*.sqlite`)
- Large binary files (`*.zip`, `*.tar.gz`)
- Generated CTX-CARD files (`CTXCARD*.md`)

## Best Practices

1. **Keep it focused**: Only ignore files that are truly not relevant to code analysis
2. **Use comments**: Add comments to explain why certain patterns are ignored
3. **Test patterns**: Use `--show-ignored` to verify your patterns are working
4. **Consider team needs**: Make sure the `.ctxignore` file works for all team members
5. **Version control**: Include the `.ctxignore` file in your repository

## Troubleshooting

### Files Still Being Processed

If files are still being processed despite being in `.ctxignore`:

1. Check the pattern syntax
2. Verify the file path relative to the project root
3. Use `--show-ignored` to see loaded patterns
4. Check for negation patterns that might override your ignore

### Performance Issues

If processing is slow:

1. Ensure large directories (like `node_modules/`) are in `.ctxignore`
2. Add patterns for build artifacts and cache directories
3. Consider using more specific patterns rather than broad ones

## Migration from .gitignore

If you have a `.gitignore` file, you can often copy most patterns to `.ctxignore`. However, consider:

- Removing patterns for files that are relevant to code analysis
- Adding patterns for files that are relevant to Git but not to code analysis
- Testing the results to ensure you're not excluding important code
