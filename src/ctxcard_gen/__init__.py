"""
CTX-CARD Generator Package

A Python CLI application for generating CTX-CARD format codebase documentation.
CTX-CARD is a prefix-free, information-dense codebook with edge lists and naming grammar.

Version: 2.1.0
"""

__version__ = "2.1.0"
__author__ = "CTX-CARD Team"
__email__ = "team@ctxcard.dev"

from .core.ast_analyzer import ASTAnalyzer
from .core.call_resolver import CallResolver
from .core.card_renderer import CardRenderer
from .core.scanner import RepoScanner
from .ctxcard_gen import CTXCardGenerator  # pylint: disable=import-error
from .exceptions import CTXCardError, ParseError, ValidationError
from .types import GeneratorConfig, ModuleInfo, ScanResult, Symbol
from .utils.ignore import IgnoreFile, IgnorePattern, load_ignore_file

__all__ = [
    "ASTAnalyzer",
    "CardRenderer",
    "RepoScanner",
    "CallResolver",
    "Symbol",
    "ModuleInfo",
    "ScanResult",
    "GeneratorConfig",
    "CTXCardError",
    "ParseError",
    "ValidationError",
    "CTXCardGenerator",
    "IgnoreFile",
    "IgnorePattern",
    "load_ignore_file",
]
