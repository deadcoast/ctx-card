# CTX-CARD Generator Project Structure

## Overview

This document outlines the current project structure for the CTX-CARD generator, optimized for maintainability, testability, and CTX-CARD format compliance.

## Implementation Status

### **Completed Features**

- **Core Analysis**: AST parsing, symbol extraction, call resolution
- **CTX-CARD Generation**: Full v2.1 specification compliance
- **File Filtering**: `.ctxignore` pattern support
- **Testing Suite**: 145 comprehensive tests (unit, integration, CLI)
- **CLI Interface**: Command-line tool with multiple options
- **Documentation**: Complete documentation suite
- **CI/CD**: GitHub Actions workflow
- **File Extension Support**: Native `.ctx` format with `--format ctx` option
- **Validation System**: Comprehensive CTX-CARD format validation
- **Performance Optimizations**: Parallel processing and caching for large codebases
- **Enhanced Tag Types**: `DEPS:`, `ENV:`, `SEC:`, `EVT:`, `ASYNC:` for better AI comprehension
- **LSP Integration**: Semantic token support for editor integration

### **Current Version**

- **Version**: v2.1.0
- **Status**: Production ready
- **Test Coverage**: 145/145 tests passing
- **Documentation**: Complete and up-to-date

## Directory Structure

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

## Module Organization

### Core Modules (`src/ctxcard_gen/core/`)

#### `ast_analyzer.py`

- **Purpose**: Python AST parsing and symbol extraction
- **Key Classes**:
  - `ASTAnalyzer`: Main AST analysis engine
  - `SymbolExtractor`: Symbol extraction logic
  - `TypeInferrer`: Type annotation analysis
- **Responsibilities**:
  - Parse Python source files
  - Extract classes, functions, properties
  - Analyze type annotations
  - Detect decorators and modifiers
  - Collect function calls and imports

#### `card_renderer.py`

- **Purpose**: CTX-CARD format generation
- **Key Classes**:
  - `CardRenderer`: Main rendering engine
  - `TagGenerator`: Individual tag generation
  - `FormatValidator`: Output validation
- **Responsibilities**:
  - Generate CTX-CARD format output
  - Ensure ASCII-only output
  - Validate prefix-free aliases
  - Generate proper indices
  - Handle delta generation

#### `scanner.py`

- **Purpose**: Repository file discovery and module indexing
- **Key Classes**:
  - `RepoScanner`: Repository scanning engine
  - `FileDiscoverer`: File system traversal
  - `ModuleIndexer`: Module indexing logic
- **Responsibilities**:
  - Discover code files
  - Build module indices
  - Detect language types
  - Assign role tags
  - Handle glob patterns
  - Apply `.ctxignore` file exclusions

#### `call_resolver.py`

- **Purpose**: Cross-module function call resolution
- **Key Classes**:
  - `CallResolver`: Call resolution engine
  - `ImportResolver`: Import path resolution
  - `EdgeBuilder`: Edge relationship construction
- **Responsibilities**:
  - Resolve function calls across modules
  - Map import aliases to actual paths
  - Build call graph edges
  - Handle re-exports
  - Validate call targets

### Utility Modules (`src/ctxcard_gen/utils/`)

#### `helpers.py`

- **Purpose**: Common helper functions
- **Functions**:
  - `today_stamp()`: Generate timestamp
  - `relpath()`: Relative path conversion
  - `is_probably_binary()`: Binary file detection
  - `ascii_only()`: ASCII conversion
  - `file_to_dotted()`: Path to dotted notation
  - `ann_to_str()`: Type annotation conversion

#### `ignore.py`

- **Purpose**: `.ctxignore` pattern parsing and matching
- **Key Classes**:
  - `IgnorePattern`: Individual ignore pattern representation
  - `IgnoreFile`: `.ctxignore` file handler
- **Functions**:
  - `load_ignore_file()`: Load and parse `.ctxignore` file
  - `should_ignore()`: Check if path matches ignore patterns
  - `_glob_to_regex()`: Convert glob patterns to regex

#### `validation.py`

- **Purpose**: CTX-CARD validation
- **Functions**:
  - `validate_prefix_free()`: Alias validation
  - `validate_regex_patterns()`: Regex validation
  - `validate_indices()`: Index validation
  - `validate_edges()`: Edge validation

### CLI Interface (`src/ctxcard_gen/ctxcard_gen.py`)

#### Command-Line Options

- **Basic Usage**: `python -m ctxcard_gen [path]`
- **Output Options**: `--stdout`, `--per-package`, `--format ctx`
- **Filtering**: `--include`, `--exclude`, `--show-ignored`
- **Analysis**: `--emit-ty`, `--delta-from`, `--stats`
- **Project**: `--proj`, `--lang`
- **Validation**: `--validate` for CTX-CARD format validation
- **Performance**: `--max-workers N`, `--cache-size N` for large codebases

#### Entry Points

- **Module Execution**: `python -m ctxcard_gen`
- **Direct Script**: `python src/ctxcard_gen/ctxcard_gen.py`
- **Package Installation**: `ctxcard_gen` command (after pip install)

### Data Models (`src/ctxcard_gen/types.py`)

#### Core Data Classes

```python
@dataclass
class Symbol:
    mid: int
    sid: int
    kind: str
    name: str
    signature: Optional[str] = None
    modifiers: Set[str] = field(default_factory=set)
    raises: List[str] = field(default_factory=list)

@dataclass
class ModuleInfo:
    id: int
    path: str
    dotted: str
    role_tags: Set[str] = field(default_factory=set)
    symbols: List[Symbol] = field(default_factory=list)
    imports_paths: Set[str] = field(default_factory=set)
    calls: List[Tuple[int, Tuple[int, int]]] = field(default_factory=list)
    fn_to_sid: Dict[str, int] = field(default_factory=dict)
    prop_to_sid: Dict[str, int] = field(default_factory=dict)

@dataclass
class ScanResult:
    modules: Dict[str, ModuleInfo]
    langs: List[str]
```

## Configuration Management

### Environment Variables

```bash
# Development
CTXCARD_DEBUG=true
CTXCARD_LOG_LEVEL=DEBUG

# Performance
CTXCARD_MAX_FILE_SIZE=10485760  # 10MB
CTXCARD_PARALLEL_WORKERS=4

# Output
CTXCARD_OUTPUT_FORMAT=markdown
CTXCARD_INCLUDE_COMMENTS=false
```

### Configuration Files

- `pyproject.toml`: Project metadata and tool configuration
- `.ctxignore`: File exclusion patterns
- `pytest.ini`: Test configuration

## Testing Strategy

### Test Organization

- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test complete workflows
- **Performance Tests**: Test with large codebases
- **Regression Tests**: Test against known issues

### Test Data

- **Sample Projects**: Various Python project structures
- **Expected Outputs**: Known good CTX-CARD outputs
- **Edge Cases**: Malformed code, binary files, etc.

### Test Coverage Goals

- **Core Modules**: 95% coverage
- **Utility Modules**: 90% coverage
- **Integration**: 85% coverage
- **Overall**: 90% coverage

### Current Test Status

- **Total Tests**: 145 tests passing
- **Test Categories**: Unit, Integration, CLI
- **Coverage**: Comprehensive coverage of all modules

## Development Workflow

### Code Quality Tools

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **pytest**: Testing
- **coverage**: Coverage reporting

### Development Commands

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
flake8 src/ tests/

# Run tests
pytest

# Run tests with coverage
pytest --cov=src/ctxcard_gen
```

### CI/CD Pipeline

1. **Code Quality**: Format, lint, type check
2. **Testing**: Unit and integration tests (145 tests)
3. **Coverage**: Coverage reporting
4. **Documentation**: Build and validate docs
5. **Release**: Tag and publish

### GitHub Actions

- **Workflow**: `.github/workflows/test.yml`
- **Triggers**: Push to main, pull requests
- **Python Versions**: 3.8, 3.9, 3.10, 3.11
- **Test Matrix**: Unit, integration, CLI tests

## Performance Considerations

### Optimization Strategies

- **Lazy Loading**: Load files only when needed
- **Parallel Processing**: Process multiple files concurrently with configurable workers
- **File Caching**: LRU cache for file content to reduce I/O overhead
- **Memory Management**: Efficient data structures and configurable cache sizes
- **Streaming**: Process large files in chunks
- **Performance Tuning**: CLI options for `--max-workers` and `--cache-size`

### Performance Features

- **Automatic Parallelization**: Uses parallel processing for codebases with >50 files
- **Configurable Workers**: `--max-workers N` option for performance tuning
- **File Content Caching**: `--cache-size N` option for memory management
- **Thread-Safe Operations**: Proper locking for concurrent file processing
- **Memory Efficiency**: LRU cache with configurable size limits

### Monitoring

- **Performance Metrics**: Parsing speed, memory usage
- **Error Tracking**: Parse errors, validation failures
- **Usage Statistics**: Most common patterns, edge cases

## Security Considerations

### Input Validation

- **File Paths**: Validate and sanitize file paths
- **File Types**: Detect and handle binary files
- **File Sizes**: Limit maximum file sizes
- **Encoding**: Handle various file encodings

### Output Sanitization

- **ASCII Only**: Ensure output is ASCII-only
- **Path Escaping**: Properly escape file paths
- **Content Filtering**: Filter sensitive information

## Current Features

### Analysis Capabilities

- **AST Parsing**: Complete Python AST analysis
- **Symbol Extraction**: Classes, functions, properties, modules
- **Call Resolution**: Cross-module function call graphs
- **Import Analysis**: Import path resolution and re-exports
- **Type Inference**: Type annotations and signatures
- **Decorator Detection**: @property, @cached_property, @dataclass
- **Route Detection**: FastAPI/Flask route decorators
- **DTO Detection**: @dataclass and pydantic models
- **Error Detection**: Custom exception classes
- **Linting**: Code quality rule violations (PX tags)
- **Raise Analysis**: Exception types in function bodies
- **Re-export Processing**: **init**.py and **all** handling

### CTX-CARD Features

- **Format Compliance**: Full CTX-CARD v2.1 specification
- **Tag Support**: All required tags (ID, AL, NM, MO, SY, SG, ED, etc.)
- **Enhanced Tags**: `DEPS:`, `ENV:`, `SEC:`, `EVT:`, `ASYNC:` for comprehensive AI comprehension
- **Delta Generation**: Diff-based updates with DELTA tags
- **Per-package Output**: Separate CTX-CARD files per package
- **Type Signatures**: Optional TY: line emission
- **Statistics**: Analysis statistics output
- **ASCII Output**: Guaranteed ASCII-only output
- **Validation**: Prefix-free alias validation and comprehensive format validation
- **File Format**: Support for both `.md` and `.ctx` extensions

### File Management

- **`.ctxignore` Support**: File exclusion patterns
- **Glob Patterns**: Wildcard and negation support
- **Character Classes**: Advanced pattern matching
- **Recursive Matching**: `**` directory traversal
- **Integration**: Seamless integration with scanning

## Extension Points

### Language Support

- **TypeScript**: Add TypeScript parser
- **Go**: Add Go AST parser
- **Java**: Add Java parser
- **C++**: Add C++ parser

### Output Formats

- **JSON**: JSON output format
- **YAML**: YAML output format
- **XML**: XML output format
- **Custom**: Plugin-based output formats

### Analysis Extensions

- **Complexity Metrics**: Cyclomatic complexity
- **Dependency Analysis**: Deep dependency graphs
- **Security Scanning**: Security vulnerability detection
- **Performance Analysis**: Performance bottleneck detection

## Validation and Quality Assurance

### CTX-CARD Validation

- **Structure Validation**: Validates required tags and format compliance
- **ASCII Compliance**: Ensures output meets CTX-CARD ASCII-only requirement
- **Cross-Reference Validation**: Validates index references and edge relationships
- **Semantic Token Generation**: LSP-compatible token generation for editor integration
- **Comprehensive Reports**: Detailed validation reports with errors and warnings

### Validation Features

- **`--validate` Option**: CLI flag for output validation
- **Real-time Validation**: Validation during generation process
- **Error Reporting**: Detailed error messages with line numbers
- **Warning System**: Non-critical issues reported as warnings
- **LSP Integration**: Semantic tokens for advanced editor support

### Quality Metrics

- **Format Compliance**: Ensures CTX-CARD specification adherence
- **Token Efficiency**: Validates information density requirements
- **Cross-Reference Integrity**: Checks index and edge consistency
- **Naming Convention Compliance**: Validates regex pattern adherence
