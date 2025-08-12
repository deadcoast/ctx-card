"""
Custom exceptions for CTX-CARD generator.

This module defines exception classes used throughout the CTX-CARD generation process.
"""


class CTXCardError(Exception):
    """Base exception for CTX-CARD generator errors."""

    pass


class ParseError(CTXCardError):
    """Raised when parsing code files fails."""

    pass


class ValidationError(CTXCardError):
    """Raised when CTX-CARD validation fails."""

    pass


class ConfigurationError(CTXCardError):
    """Raised when configuration is invalid."""

    pass


class FileError(CTXCardError):
    """Raised when file operations fail."""

    pass


class ASTError(CTXCardError):
    """Raised when AST analysis fails."""

    pass
