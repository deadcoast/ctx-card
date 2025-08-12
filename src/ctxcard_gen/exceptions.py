"""
Custom exceptions for CTX-CARD generator.

This module defines exception classes used throughout the CTX-CARD generation process.
"""


class CTXCardError(Exception):
    """Base exception for CTX-CARD generator errors."""


class ParseError(CTXCardError):
    """Raised when parsing code files fails."""


class ValidationError(CTXCardError):
    """Raised when CTX-CARD validation fails."""


class ConfigurationError(CTXCardError):
    """Raised when configuration is invalid."""


class FileError(CTXCardError):
    """Raised when file operations fail."""


class ASTError(CTXCardError):
    """Raised when AST analysis fails."""
