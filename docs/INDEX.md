# CTX-CARD Generator - Project Index

This index provides quick navigation to all project files, organized by category.

## **Quick Links**

- **[Installation Guide](README.md#installation)** - How to install and set up the project
- **[Usage Examples](README.md#usage)** - Basic and advanced usage examples
- **[CTX Use Case](docs/CTX-PURPOSE.md)** - Breakdown of CTX Use Cases
- **[Syntax Highlighter](docs/SYNTAX-HIGHLIGHTER.md)** - Syntax Highlighter Summary
- **[.ctxignore Guide](docs/CTXIGNORE.md)** - File exclusion patterns
- **[CTX-CARD Format](README.md#ctx-card-format)** - Understanding the output format
- **[Project Architecture](docs/PROJECT-STRUCTURE.md)** - Implementation details
- **[CTX-CARD Specification](docs/CTX-ARCHITECTURE.md)** - Complete format specification
- **[Test Suite](tests/README.md)** - Testing documentation and guidelines

## **DOCS**

### **Core Documentation**

- **[README.md](README.md)** - Project overview, installation, and usage guide
- **[CTXCARD.md](CTXCARD.md)** - Generated CTX-CARD for this project
- **[.ctxignore](.ctxignore)** - File exclusion patterns for CTX-CARD generation

### **Documentation Directory**

- **[CTX-ARCHITECTURE.md](docs/CTX-ARCHITECTURE.md)** - CTX-CARD specification and format guide
- **[CTXIGNORE.md](docs/CTXIGNORE.md)** - Complete `.ctxignore` documentation and examples
- **[PROJECT-STRUCTURE.md](docs/PROJECT-STRUCTURE.md)** - Project architecture and implementation details

### **Syntax Highlighting**

- **[Syntax-Highlighter/README.md](Syntax-Highlighter/README.md)** - VSCode syntax highlighting implementation
- **[Syntax-Highlighter/CTX-VSC-LANG.md](Syntax-Highlighter/CTX-VSC-LANG.md)** - Comprehensive syntax highlighting specification
- **[Syntax-Highlighter/FIXES.md](docs/Syntax-Highlighter/FIXES.md)** - Detailed fixes for syntax highlighting issues
- **[Syntax-Highlighter/syntaxes/ctx.tmLanguage.json](Syntax-Highlighter/syntaxes/ctx.tmLanguage.json)** - VSCode TextMate grammar (FIXED)
- **[Syntax-Highlighter/language-configuration.json](Syntax-Highlighter/language-configuration.json)** - VSCode language configuration
- **[Syntax-Highlighter/package.json](Syntax-Highlighter/package.json)** - VSCode extension configuration
- **[Syntax-Highlighter/install-test.sh](Syntax-Highlighter/install-test.sh)** - Installation script for testing
- **[Syntax-Highlighter/test.ctx](Syntax-Highlighter/snippets/test.ctx)** - Simple test file
- **[Syntax-Highlighter/comprehensive-test.ctx](Syntax-Highlighter/snippets/comprehensive-test.ctx)** - Comprehensive test file
- **[Syntax-Highlighter/sample.ctx](Syntax-Highlighter/snippets/sample.ctx)** - Sample CTX-CARD file for testing
- **[Syntax-Highlighter/TODO](Syntax-Highlighter/TODO)** - Future enhancements and additional parameters

### **Test Documentation**

- **[tests/README.md](tests/README.md)** - Testing suite documentation and guidelines

## **CODE**

### **Main Application**

- **[ctxcard_gen.py](src/ctxcard_gen.py)** - CLI entry point (legacy location)
- **[src/ctxcard_gen/ctxcard_gen.py](src/ctxcard_gen/ctxcard_gen.py)** - Main CLI application
- **[src/ctxcard_gen/**main**.py](src/ctxcard_gen/**main**.py)** - Module execution entry point
- **[src/ctxcard_gen/**init**.py](src/ctxcard_gen/**init**.py)** - Package initialization and exports

### **Core Analysis Modules**

- **[src/ctxcard_gen/core/**init**.py](src/ctxcard_gen/core/**init**.py)** - Core package initialization
- **[src/ctxcard_gen/core/scanner.py](src/ctxcard_gen/core/scanner.py)** - Repository file discovery and module indexing
- **[src/ctxcard_gen/core/ast_analyzer.py](src/ctxcard_gen/core/ast_analyzer.py)** - Python AST parsing and symbol extraction
- **[src/ctxcard_gen/core/call_resolver.py](src/ctxcard_gen/core/call_resolver.py)** - Cross-module function call resolution
- **[src/ctxcard_gen/core/card_renderer.py](src/ctxcard_gen/core/card_renderer.py)** - CTX-CARD format generation

### **Utility Modules**

- **[src/ctxcard_gen/utils/**init**.py](src/ctxcard_gen/utils/**init**.py)** - Utils package initialization
- **[src/ctxcard_gen/utils/helpers.py](src/ctxcard_gen/utils/helpers.py)** - Common helper functions
- **[src/ctxcard_gen/utils/validation.py](src/ctxcard_gen/utils/validation.py)** - CTX-CARD validation functions
- **[src/ctxcard_gen/utils/ignore.py](src/ctxcard_gen/utils/ignore.py)** - `.ctxignore` pattern parsing and matching

### **Data Models and Types**

- **[src/ctxcard_gen/types.py](src/ctxcard_gen/types.py)** - Core data structures and type definitions
- **[src/ctxcard_gen/exceptions.py](src/ctxcard_gen/exceptions.py)** - Custom exception classes

### **Configuration Files**

- **[pyproject.toml](pyproject.toml)** - Project configuration and metadata
- **[requirements.txt](requirements.txt)** - Python dependencies
- **[pytest.ini](pytest.ini)** - Pytest configuration

### **Testing Suite**

#### **Test Configuration**

- **[tests/**init**.py](tests/**init**.py)** - Test package initialization
- **[tests/conftest.py](tests/conftest.py)** - Pytest configuration and shared fixtures

#### **Unit Tests**

- **[tests/unit/test_scanner.py](tests/unit/test_scanner.py)** - Repository scanner tests
- **[tests/unit/test_ast_analyzer.py](tests/unit/test_ast_analyzer.py)** - AST analyzer tests
- **[tests/unit/test_call_resolver.py](tests/unit/test_call_resolver.py)** - Call resolver tests
- **[tests/unit/test_card_renderer.py](tests/unit/test_card_renderer.py)** - Card renderer tests
- **[tests/unit/test_utils.py](tests/unit/test_utils.py)** - Utility functions tests
- **[tests/unit/test_ignore.py](tests/unit/test_ignore.py)** - `.ctxignore` functionality tests

#### **Integration Tests**

- **[tests/integration/test_full_generation.py](tests/integration/test_full_generation.py)** - End-to-end CTX-CARD generation tests

#### **CLI Tests**

- **[tests/cli/test_cli.py](tests/cli/test_cli.py)** - Command-line interface tests

#### **Legacy Tests**

- **[tests/test_ast_analyzer.py](tests/test_ast_analyzer.py)** - Legacy AST analyzer tests

### **Development Tools**

- **[run_tests.py](run_tests.py)** - Test runner script for easy test execution

### **CI/CD**

- **[.github/workflows/test.yml](.github/workflows/test.yml)** - GitHub Actions CI/CD workflow

---

## **Project Structure**

[PROJECT-STRUCTURE.md](docs/PROJECT-STRUCTURE.md)
