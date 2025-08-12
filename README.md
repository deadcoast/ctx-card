# CTX-CARD Generator

A Python CLI application for generating **CTX-CARD** format codebase documentation. CTX-CARD is a prefix-free, information-dense codebook with edge lists and naming grammar that provides minimal-token, high-information structural and semantic maps of codebases.

## Features

- **AST-based Analysis**: Deep Python code parsing using the `ast` module
- **CTX-CARD v2.1 Compliance**: Full implementation of the CTX-CARD specification
- **Cross-module Call Resolution**: Two-pass analysis for function call graphs
- **Symbol Extraction**: Classes, functions, properties, and modules
- **DTO Detection**: Automatic detection of `@dataclass` and `pydantic.BaseModel`
- **Error Taxonomy**: Custom exception detection and classification
- **API Route Detection**: FastAPI and Flask route decorator parsing
- **Linting Integration**: Built-in code quality checks (PX tags)
- **Property & Descriptor Detection**: Support for `@property`, `@cached_property`, and descriptor classes
- **Raise Analysis**: `!raises[...]` in function signatures
- **Re-export Handling**: `__init__.py` and `__all__` processing
- **Delta Generation**: Diff-based updates for incremental changes
- **Per-package Generation**: Separate CTX-CARD files for each package
- **Type Signature Emission**: Optional `TY:` lines for type information
- **Multi-language Support**: Extensible for TypeScript, Go, and other languages
- **`.ctxignore` Support**: File exclusion patterns similar to `.gitignore`

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/ctxcard/ctxcard-gen.git
cd ctxcard-gen

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

### Development Setup

```bash
# Install development dependencies
pip install -e ".[dev,enhanced,monitoring]"

# Run tests
pytest

# Format code
black src/ tests/
isort src/ tests/

# Lint code
flake8 src/ tests/
```

## Usage

### Basic Usage

```bash
# Generate CTX-CARD for current directory
python -m ctxcard_gen

# Generate for specific directory
python -m ctxcard_gen /path/to/project

# Output to stdout
python -m ctxcard_gen --stdout

# Specify project name
python -m ctxcard_gen --proj my-project
```

### Advanced Options

```bash
# Include only Python files
python -m ctxcard_gen --include "**/*.py"

# Exclude test files
python -m ctxcard_gen --exclude "**/tests/**"

# Include type signatures
python -m ctxcard_gen --emit-ty

# Generate delta against existing CTX-CARD
python -m ctxcard_gen --delta-from CTXCARD.md

# Per-package CTX-CARD files
python -m ctxcard_gen --per-package

# Print analysis statistics
python -m ctxcard_gen --stats

# Show ignored patterns
python -m ctxcard_gen --show-ignored

# Output in .ctx format instead of .md
python -m ctxcard_gen --format ctx

# Validate CTX-CARD output
python -m ctxcard_gen --validate

# Performance tuning for large codebases
python -m ctxcard_gen --max-workers 8 --cache-size 2000

# Export to additional formats
python -m ctxcard_gen --export-format json
python -m ctxcard_gen --export-format yaml
python -m ctxcard_gen --export-format xml
python -m ctxcard_gen --export-format md
```

## .ctxignore File

The `.ctxignore` file allows you to specify patterns for files and directories that should be excluded from CTX-CARD generation. It works similarly to `.gitignore` but is specifically designed for CTX-CARD analysis.

### Instructions

Create a `.ctxignore` file in your project root:

```ctxignore
# Python cache files
__pycache__/
*.pyc

# Virtual environments
.venv/
venv/

# IDE files
.vscode/
.idea/

# Generated files
CTXCARD*.md
```

### Pattern Examples

```ctxignore
# Ignore all Python files
*.py

# But include important ones
!important.py
!main.py

# Ignore test files
**/tests/**
**/*_test.py

# Ignore build artifacts
build/
dist/
*.egg-info/
```

For complete documentation, see [CTXIGNORE.md](docs/CTXIGNORE.md).

## CTX-CARD Format

CTX-CARD is a structured format for representing codebase information:

```yaml
ID: proj|myProject lang|py std|pep8 ts|20241201

AL: cfg=>Configuration svc=>Service repo=>Repository
NM: module | ^[a-z_]+$ | auth_service
NM: class  | ^[A-Z][A-Za-z0-9]+$ | AuthService

MO: #1 | auth/service.py | {svc,auth}
SY: #1.#1 | cls | AuthService
SY: #1.#2 | fn  | AuthService.login
SG: #1.#2 | (UserCreds)->AuthToken !raises[AuthError]
MD: #1.#2 | {classmethod}

ED: #1.#2 -> #2.#1 | calls
IN: login ⇒ requires(valid(creds)) ∧ ensures(token.exp>now)

CN: async fn end with _async
PX: forbid bare except | error-handling
```

### Tag Reference

- **ID**: Project identity and metadata
- **AL**: Prefix-free alias table
- **NM**: Naming grammar with regex patterns
- **MO**: Module index with role tags
- **SY**: Symbol index within modules
- **SG**: Function signatures with raises
- **MD**: Method modifiers (staticmethod, classmethod, property, descriptor)
- **ED**: Edge relationships (imports/calls)
- **IN**: Invariants from docstrings
- **CN**: Coding conventions
- **ER**: Error taxonomy
- **IO**: API contracts
- **DT**: Data transfer objects
- **TK**: Token/enum sets
- **PX**: Prohibited patterns
- **EX**: Canonical examples
- **RV**: Review checklists
- **TY**: Type signatures (optional)
- **Δ**: Delta changes

## Architecture

### Core Components

1. **RepoScanner**: File discovery and module indexing with `.ctxignore` support
2. **ASTAnalyzer**: Python AST parsing and symbol extraction
3. **CallResolver**: Cross-module function call analysis
4. **CardRenderer**: CTX-CARD format generation
5. **IgnoreFile**: `.ctxignore` pattern parsing and matching

### Data Models

- `ModuleInfo`: Repository module representation
- `Symbol`: Code symbol (class, function, property)
- `ScanResult`: Complete repository analysis
- `GeneratorConfig`: Generation configuration
- `IgnoreFile`: `.ctxignore` file handler
- `IgnorePattern`: Individual ignore pattern representation

### Analysis Features

- **Symbol Extraction**: Classes, functions, properties, modules
- **Type Inference**: Type annotations and signatures
- **Call Resolution**: Function call graph analysis
- **Import Analysis**: Import path resolution and re-exports
- **Linting**: Code quality rule violations
- **Route Detection**: FastAPI/Flask route decorators
- **DTO Detection**: @dataclass and pydantic models
- **Raise Analysis**: Exception types in function bodies
- **Property Detection**: @property and @cached_property
- **Descriptor Detection**: Classes with **get**/**set**/**set_name**
- **File Filtering**: `.ctxignore` pattern-based file exclusion

## CTX-CARD Syntax Highlighter (VS Code / Cursor)

This repo ships a TextMate grammar for `.ctx` files.

- Folder: `Syntax-Highlighter/`
- Grammar: `Syntax-Highlighter/syntaxes/ctx.tmLanguage.json`
- Language config: `Syntax-Highlighter/language-configuration.json`
- Snippets: `Syntax-Highlighter/snippets/ctx.json`
- Samples: `Syntax-Highlighter/{test.ctx,sample.ctx,comprehensive-test.ctx}`

### Install via VSIX (recommended)

```bash
cd Syntax-Highlighter
npx @vscode/vsce package --no-yarn
# -> creates Syntax-Highlighter/ctx-card-syntax-1.0.0.vsix
```

Then in VS Code / Cursor:

- Command Palette → “Extensions: Install from VSIX…”
- Choose `Syntax-Highlighter/ctx-card-syntax-1.0.0.vsix`
- Reload when prompted
- Open a `.ctx` file → “Change Language Mode” → select “CTX-CARD” (sticks per‑workspace)

### Quick local install (no VSIX)

```bash
cd Syntax-Highlighter
./install-test.sh
# Installs to ~/.vscode/extensions/ctxcard.ctx-card-syntax-1.0.0
```

## Installation (VSIX recommended)

Build the VSIX:

```bash
cd Syntax-Highlighter
npx @vscode/vsce package --no-yarn
# Produces: ctx-card-syntax-1.0.0.vsix
```

Install in VS Code / Cursor:

- Command Palette → “Extensions: Install from VSIX…”
- Choose `Syntax-Highlighter/ctx-card-syntax-1.0.0.vsix`
- Reload when prompted
- Open a `.ctx` file → “Change Language Mode” → select “CTX-CARD”

Workspace override (to beat ConTeXt auto-detect):

```json
{
  "files.associations": {
    "*.ctx": "ctx",
    "*.ctxc": "ctx",
    "*.ctxcard": "ctx"
  }
}
```

## Paths (rooted)

- Grammar: `Syntax-Highlighter/syntaxes/ctx.tmLanguage.json`
- Language config: `Syntax-Highlighter/language-configuration.json`
- Snippets: `Syntax-Highlighter/snippets/ctx.json`
- Tests: `Syntax-Highlighter/{test.ctx,sample.ctx,comprehensive-test.ctx}`

## Development

### Project Structure

```text
.
├── docs
│   ├── CTX-ARCHITECTURE.md
│   ├── CTXIGNORE.md
│   └── PROJECT_STRUCTURE.md
├── src
│   ├── ctxcard_gen
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── core
│   │   │   ├── __init__.py
│   │   │   ├── ast_analyzer.py
│   │   │   ├── call_resolver.py
│   │   │   ├── card_renderer.py
│   │   │   └── scanner.py
│   │   ├── ctxcard_gen.py
│   │   ├── exceptions.py
│   │   ├── types.py
│   │   └── utils
│   │       ├── __init__.py
│   │       ├── helpers.py
│   │       ├── ignore.py
│   │       └── validation.py
│   └── ctxcard_gen.py
├── CTXCARD.md
├── .ctxignore
├── INDEX.md
├── pyproject.toml
├── pytest.ini
├── README.md
├── requirements.txt
├── run_tests.py
└── tests
    ├── __init__.py
    ├── cli
    │   └── test_cli.py
    ├── conftest.py
    ├── integration
    │   └── test_full_generation.py
    ├── README.md
    ├── test_ast_analyzer.py
    └── unit
        ├── test_call_resolver.py
        ├── test_card_renderer.py
        ├── test_ignore.py
        ├── test_scanner.py
        └── test_utils.py
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/ctxcard_gen

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m "not slow"
```

### Code Quality

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

## Version History

### v2.1.0 (Current)

- **`.ctxignore` Support**: File exclusion patterns similar to `.gitignore`
- **Raise Analysis**: `!raises[...]` in function signatures
- **Enhanced PX Linting**: Bare except, wildcard imports, eval/exec, mutable defaults, print()
- **Per-package Generation**: Separate CTX-CARD files for each package
- **Delta Generation**: Diff-based updates with Δ tags
- **Type Signature Emission**: Optional TY: lines
- **Statistics**: Analysis statistics output
- **`.ctx` Extension Support**: Native CTX-CARD file format
- **Validation System**: Comprehensive CTX-CARD format validation
- **Performance Optimizations**: Parallel processing and caching for large codebases
- **LSP Integration**: Semantic token support for editor integration
- **Enhanced Tag Types**: `DEPS:`, `ENV:`, `SEC:`, `EVT:`, `ASYNC:` for better AI comprehension
- **Export Formats**: JSON, YAML, XML, and enhanced Markdown export
- **Auto-completion**: LSP-compatible completion for indices and references
- **Cross-reference Navigation**: Go-to-definition and find all references

### v2.0.0

- **Cross-module Call Resolution**: Two-pass analysis for function calls
- **Re-export Handling**: `__init__.py` and `__all__` processing
- **Class Method Resolution**: Support for `Class.method()` calls
- **Property Detection**: @property and @cached_property support
- **Descriptor Detection**: Classes with descriptor dunder methods

### v1.5.0

- **Function-level Call Graph**: Cross-module function call resolution
- **DTO Detection**: @dataclass and pydantic.BaseModel support
- **Error Taxonomy**: Custom exception detection
- **API Route Detection**: FastAPI and Flask route parsing
- **Invariants**: Docstring parsing for requires/ensures

### v1.0.0

- **Basic AST Analysis**: Module and symbol extraction
- **Import Resolution**: Module-level import edges
- **CTX-CARD v1 Compliance**: Core format implementation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Development Guidelines

- Follow PEP 8 style guidelines
- Use type hints for all functions
- Write comprehensive docstrings
- Add tests for new features
- Maintain CTX-CARD format compliance
- Update documentation as needed

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- CTX-CARD specification and architecture
- Python AST module for code analysis
- Rich ecosystem of Python development tools

## Support

- **Documentation**: [docs/](docs/)
- **CTX-CARD Specification**: [CTX-ARCHITECTURE.md](docs/CTX-ARCHITECTURE.md)
- **Project Structure**: [PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)
- **`.ctxignore` Guide**: [CTXIGNORE.md](docs/CTXIGNORE.md)
- **Issues**: [GitHub Issues](https://github.com/ctxcard/ctxcard-gen/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ctxcard/ctxcard-gen/discussions)
