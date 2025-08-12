# CTX-CARD Generator - Project Index

This index provides quick navigation to all project files, organized by category. It serves as a central map linking to all documentation and corresponding code modules.

## **Quick Links**

- **[Installation Guide](../README.md#installation)** - How to install and set up the project
- **[Usage Examples](../README.md#usage)** - Basic and advanced usage examples
- **[CTX Use Case](CTX-PURPOSE.md)** - Breakdown of CTX Use Cases
- **[Syntax Highlighter](SYNTAX-HIGHLIGHTER.md)** - Syntax Highlighter Summary
- **[.ctxignore Guide](CTXIGNORE.md)** - File exclusion patterns
- **[CTX-CARD Format](../README.md#ctx-card-format)** - Understanding the output format
- **[Project Architecture](PROJECT-STRUCTURE.md)** - Implementation details
- **[CTX-CARD Specification](CTX-ARCHITECTURE.md)** - Complete format specification
- **[Test Suite](../tests/README.md)** - Testing documentation and guidelines

## **DOCUMENTATION**

### **Core Documentation**

- **[README.md](../README.md)** - Project overview, installation, and usage guide
- **[CTXCARD.ctx](../CTXCARD.ctx)** - Generated CTX-CARD in native format
- **[CTXCARD.json](../CTXCARD.json)** - Generated CTX-CARD in JSON format
- **[.ctxignore](../.ctxignore)** - File exclusion patterns for CTX-CARD generation

### **Documentation Directory**

- **[CTX-ARCHITECTURE.md](CTX-ARCHITECTURE.md)** - CTX-CARD specification and format guide
- **[CTX-PURPOSE.md](CTX-PURPOSE.md)** - CTX use cases and purpose breakdown
- **[CTX-IDEOLOGY.md](CTX-IDEOLOGY.md)** - CTX philosophy and design principles
- **[CTXIGNORE.md](CTXIGNORE.md)** - Complete `.ctxignore` documentation and examples
- **[PROJECT-STRUCTURE.md](PROJECT-STRUCTURE.md)** - Project architecture and implementation details
- **[SYNTAX-HIGHLIGHTER.md](SYNTAX-HIGHLIGHTER.md)** - Syntax highlighting implementation guide
- **[FIXES.md](FIXES.md)** - Known issues and fixes documentation

### **AI Specification Documentation**

- **[AI-Spec-Docs/AI-CTX-ARCHITECTURE.md](AI-Spec-Docs/AI-CTX-ARCHITECTURE.md)** - AI-focused CTX-CARD architecture specification
- **[AI-Spec-Docs/AI-CTX-PURPOSE.md](AI-Spec-Docs/AI-CTX-PURPOSE.md)** - AI-focused CTX use cases and purpose

### **Syntax Highlighting**

- **[Syntax-Highlighter/README.md](../Syntax-Highlighter/README.md)** - VSCode syntax highlighting implementation
- **[Syntax-Highlighter/CTX-DICTIONARY.md](../Syntax-Highlighter/CTX-DICTIONARY.md)** - CTX-CARD tag dictionary and definitions
- **[Syntax-Highlighter/package.json](../Syntax-Highlighter/package.json)** - VSCode extension configuration
- **[Syntax-Highlighter/language-configuration.json](../Syntax-Highlighter/language-configuration.json)** - VSCode language configuration
- **[Syntax-Highlighter/install-test.sh](../Syntax-Highlighter/install-test.sh)** - Installation script for testing
- **[Syntax-Highlighter/syntaxes/ctx.tmLanguage.json](../Syntax-Highlighter/syntaxes/ctx.tmLanguage.json)** - VSCode TextMate grammar
- **[Syntax-Highlighter/snippets/test.ctx](../Syntax-Highlighter/snippets/test.ctx)** - Simple test file
- **[Syntax-Highlighter/snippets/comprehensive-test.ctx](../Syntax-Highlighter/snippets/comprehensive-test.ctx)** - Comprehensive test file
- **[Syntax-Highlighter/snippets/sample.ctx](../Syntax-Highlighter/snippets/sample.ctx)** - Sample CTX-CARD file for testing

### **Test Documentation**

- **[tests/README.md](../tests/README.md)** - Testing suite documentation and guidelines

## **CODE**

### **Main Application**

- **[src/ctxcard_gen/ctxcard_gen.py](../src/ctxcard_gen/ctxcard_gen.py)** - Main CLI application with full feature set
- **[src/ctxcard_gen/__main__.py](../src/ctxcard_gen/__main__.py)** - Module execution entry point
- **[src/ctxcard_gen/__init__.py](../src/ctxcard_gen/__init__.py)** - Package initialization and exports

### **Core Analysis Modules**

- **[src/ctxcard_gen/core/__init__.py](../src/ctxcard_gen/core/__init__.py)** - Core package initialization
- **[src/ctxcard_gen/core/scanner.py](../src/ctxcard_gen/core/scanner.py)** - Repository file discovery and module indexing
- **[src/ctxcard_gen/core/ast_analyzer.py](../src/ctxcard_gen/core/ast_analyzer.py)** - Python AST parsing and symbol extraction
- **[src/ctxcard_gen/core/call_resolver.py](../src/ctxcard_gen/core/call_resolver.py)** - Cross-module function call resolution
- **[src/ctxcard_gen/core/card_renderer.py](../src/ctxcard_gen/core/card_renderer.py)** - CTX-CARD format generation

### **Utility Modules**

- **[src/ctxcard_gen/utils/__init__.py](../src/ctxcard_gen/utils/__init__.py)** - Utils package initialization
- **[src/ctxcard_gen/utils/helpers.py](../src/ctxcard_gen/utils/helpers.py)** - Common helper functions
- **[src/ctxcard_gen/utils/validation.py](../src/ctxcard_gen/utils/validation.py)** - CTX-CARD validation functions
- **[src/ctxcard_gen/utils/ignore.py](../src/ctxcard_gen/utils/ignore.py)** - `.ctxignore` pattern parsing and matching
- **[src/ctxcard_gen/utils/export.py](../src/ctxcard_gen/utils/export.py)** - Export to multiple formats (JSON, YAML, XML, Markdown)

### **Data Models and Types**

- **[src/ctxcard_gen/types.py](../src/ctxcard_gen/types.py)** - Core data structures and type definitions
- **[src/ctxcard_gen/exceptions.py](../src/ctxcard_gen/exceptions.py)** - Custom exception classes

### **Configuration Files**

- **[pyproject.toml](../pyproject.toml)** - Project configuration and metadata
- **[requirements.txt](../requirements.txt)** - Python dependencies
- **[pytest.ini](../pytest.ini)** - Pytest configuration
- **[.cursorrules](../.cursorrules)** - Cursor IDE configuration and coding rules

### **Testing Suite**

#### **Test Configuration**

- **[tests/__init__.py](../tests/__init__.py)** - Test package initialization
- **[tests/conftest.py](../tests/conftest.py)** - Pytest configuration and shared fixtures

#### **Unit Tests**

- **[tests/unit/test_scanner.py](../tests/unit/test_scanner.py)** - Repository scanner tests

- **[tests/unit/test_call_resolver.py](../tests/unit/test_call_resolver.py)** - Call resolver tests
- **[tests/unit/test_card_renderer.py](../tests/unit/test_card_renderer.py)** - Card renderer tests
- **[tests/unit/test_utils.py](../tests/unit/test_utils.py)** - Utility functions tests
- **[tests/unit/test_ignore.py](../tests/unit/test_ignore.py)** - `.ctxignore` functionality tests
- **[tests/unit/test_export.py](../tests/unit/test_export.py)** - Export functionality tests
- **[tests/unit/test_validation.py](../tests/unit/test_validation.py)** - Validation functionality tests

#### **Integration Tests**

- **[tests/integration/test_full_generation.py](../tests/integration/test_full_generation.py)** - End-to-end CTX-CARD generation tests

#### **CLI Tests**

- **[tests/cli/test_cli.py](../tests/cli/test_cli.py)** - Command-line interface tests

#### **Legacy Tests**

- **[tests/test_ast_analyzer.py](../tests/test_ast_analyzer.py)** - Legacy AST analyzer tests

### **Development Tools**

- **[run_tests.py](../run_tests.py)** - Test runner script for easy test execution

### **CI/CD**

- **[.github/workflows/test.yml](../.github/workflows/test.yml)** - GitHub Actions CI/CD workflow

## **DEVELOPMENT**

### **Build and Package Files**

- **[src/ctxcard_gen.egg-info/](../src/ctxcard_gen.egg-info/)** - Package metadata (generated)
- **[.pytest_cache/](../.pytest_cache/)** - Pytest cache (generated)
- **[__pycache__/](../__pycache__/)** - Python bytecode cache (generated)
- **[.coverage](../.coverage)** - Coverage report data (generated)
- **[.early.coverage/](../.early.coverage/)** - Early coverage data (generated)

### **IDE and Editor Configuration**

- **[.vscode/](../.vscode/)** - Visual Studio Code configuration
- **[.cursor/](../.cursor/)** - Cursor IDE configuration

### **Environment and Dependencies**

- **[.venv/](../.venv/)** - Python virtual environment (generated)
- **[.git/](../.git/)** - Git repository data

## **PROJECT STRUCTURE**

For detailed project structure information, see **[PROJECT-STRUCTURE.md](PROJECT-STRUCTURE.md)**.

### **Key Directories**

- **`src/ctxcard_gen/`** - Main application source code
- **`tests/`** - Comprehensive test suite
- **`docs/`** - Project documentation
- **`Syntax-Highlighter/`** - VSCode extension for CTX-CARD syntax highlighting
- **`docs/AI-Spec-Docs/`** - AI-focused specification documents

### **Generated Files**

- **`CTXCARD.ctx`** - Generated CTX-CARD in native format
- **`CTXCARD.json`** - Generated CTX-CARD in JSON format

---

## **Getting Started**

1. **Installation**: See [README.md](../README.md#installation)
2. **Quick Start**: See [README.md](../README.md#usage)
3. **Documentation**: Browse the [docs/](.) directory
4. **Testing**: Run `python run_tests.py` or see [tests/README.md](../tests/README.md)
5. **Development**: See [PROJECT-STRUCTURE.md](PROJECT-STRUCTURE.md)

## **Additional Resources**

- **[CTX-CARD Architecture](CTX-ARCHITECTURE.md)** - Complete format specification
- **[CTX Purpose](CTX-PURPOSE.md)** - Use cases and philosophy
- **[Project Structure](PROJECT-STRUCTURE.md)** - Implementation details
- **[Syntax Highlighter](../Syntax-Highlighter/README.md)** - VSCode extension
- **[Test Documentation](../tests/README.md)** - Testing guidelines
