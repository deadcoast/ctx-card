"""
AST analyzer for CTX-CARD generator.

This module coordinates AST parsing and analysis across the CTX-CARD generation process.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from ..exceptions import ASTError
from ..types import ScanResult
from .call_resolver import CallResolver
from .scanner import RepoScanner


class ASTAnalyzer:
    """Coordinates AST analysis and call resolution."""

    def __init__(self, max_workers: int = 4, cache_size: int = 1000):
        """
        Initialize the AST analyzer.
        
        Args:
            max_workers: Maximum number of parallel workers for file processing
            cache_size: Maximum size of file content cache
        """
        self.scanner = RepoScanner(max_workers=max_workers, cache_size=cache_size)
        self.call_resolver = CallResolver()

    def analyze_repository(
        self, root: Path, include_glob: Optional[str], exclude_glob: Optional[str]
    ) -> ScanResult:
        """
        Perform complete AST analysis of a repository.

        This is a two-pass process:
        1. Pass A: Scan repository and extract symbols
        2. Pass B: Resolve cross-module function calls

        Args:
            root: Repository root path
            include_glob: Glob pattern for files to include
            exclude_glob: Glob pattern for files to exclude

        Returns:
            Complete scan result with all analysis
        """
        # Pass A: Initial scanning and symbol extraction
        scan_result = self.scanner.scan_repository(root, include_glob, exclude_glob)

        # Pass B: Cross-module call resolution
        self.extract_calls(root, scan_result)
        
        # Process re-exports
        self.call_resolver.process_reexports(scan_result.modules)

        return scan_result

    def extract_calls(self, root: Path, scan_result: ScanResult) -> None:
        """
        Extract cross-module function calls (Pass B).

        Args:
            root: Repository root path
            scan_result: Scan result from Pass A
        """
        self.call_resolver.extract_calls(root, scan_result)

    def validate_analysis(self, scan_result: ScanResult) -> None:
        """
        Validate the analysis results.

        Args:
            scan_result: Scan result to validate

        Raises:
            ASTError: If validation fails
        """
        # Basic validation checks
        if not scan_result.modules:
            raise ASTError("No modules found in repository")

        # Check for duplicate module IDs
        module_ids = [mi.id for mi in scan_result.modules.values()]
        if len(module_ids) != len(set(module_ids)):
            raise ASTError("Duplicate module IDs found")

        # Check for duplicate symbol IDs within modules
        for mi in scan_result.modules.values():
            symbol_ids = [s.sid for s in mi.symbols]
            if len(symbol_ids) != len(set(symbol_ids)):
                raise ASTError(f"Duplicate symbol IDs found in module {mi.path}")

    def get_statistics(self, scan_result: ScanResult) -> Dict[str, int]:
        """
        Get statistics about the analysis.

        Args:
            scan_result: Scan result to analyze

        Returns:
            Dictionary of statistics
        """
        total_symbols = sum(len(mi.symbols) for mi in scan_result.modules.values())
        total_calls = sum(len(mi.calls) for mi in scan_result.modules.values())
        total_imports = sum(
            len(mi.imports_paths) for mi in scan_result.modules.values()
        )
        total_dtos = sum(len(mi.dts) for mi in scan_result.modules.values())
        total_errors = sum(len(mi.errors) for mi in scan_result.modules.values())
        total_routes = sum(len(mi.routes) for mi in scan_result.modules.values())
        total_px = sum(len(mi.px) for mi in scan_result.modules.values())

        return {
            "modules": len(scan_result.modules),
            "symbols": total_symbols,
            "calls": total_calls,
            "imports": total_imports,
            "dtos": total_dtos,
            "errors": total_errors,
            "routes": total_routes,
            "lint_violations": total_px,
            "languages": len(scan_result.langs),
        }
