#!/usr/bin/env python3
"""
CTX-CARD Generator - Main Module

A Python CLI application for generating CTX-CARD format codebase documentation.
CTX-CARD is a prefix-free, information-dense codebook with edge lists and naming grammar.

Version: 2.1.0
Features:
- AST-based Python code analysis
- Cross-module function call resolution
- DTO detection (@dataclass, pydantic.BaseModel)
- Error taxonomy and API route detection
- Linting rules (PX tags)
- Property and descriptor detection
- Raise analysis (!raises[...])
- Per-package CTX-CARD generation
- Delta generation (Δ)
- Type signature emission (TY:)

Usage:
    python -m ctxcard_gen [options] [root_path]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from .core.ast_analyzer import ASTAnalyzer
from .core.card_renderer import CardRenderer
from .exceptions import CTXCardError, ParseError, ValidationError
from .types import GeneratorConfig


class CTXCardGenerator:
    """Main CTX-CARD generator class."""

    def __init__(self, config: GeneratorConfig):
        self.config = config
        self.analyzer = ASTAnalyzer()
        self.renderer = CardRenderer()

    def generate(self) -> str:
        """Generate CTX-CARD content."""
        # Analyze repository
        scan_result = self.analyzer.analyze_repository(
            self.config.root_path,
            self.config.include_pattern,
            self.config.exclude_pattern,
        )

        # Validate analysis
        self.analyzer.validate_analysis(scan_result)

        # Render CTX-CARD
        card_content = self.renderer.render_card(
            self.config.project_name,
            scan_result.langs,
            "pep8",  # Default standard
            scan_result.modules,
            self.config.emit_type_signatures,
        )

        # Handle delta generation
        if self.config.delta_from:
            delta_content = self.renderer.generate_delta(
                self.config.delta_from, card_content
            )
            card_content += delta_content

        # Validate output
        self.renderer.validate_output(card_content)

        return card_content

    def generate_per_package(self, root_content: str) -> dict[str, str]:
        """Generate per-package CTX-CARD files."""
        # Re-analyze to get fresh scan result
        scan_result = self.analyzer.analyze_repository(
            self.config.root_path,
            self.config.include_pattern,
            self.config.exclude_pattern,
        )

        return self.renderer.render_per_package(
            root_content,
            scan_result.modules,
            scan_result.langs,
            "pep8",
            self.config.project_name,
        )

    def save_output(self, content: str) -> None:
        """Save output to file or stdout."""
        if self.config.stdout_output:
            sys.stdout.write(content)
        else:
            self.config.output_path.write_text(content, encoding="utf-8")
            print(f"Wrote {self.config.output_path}")

    def save_per_package(self, packages: dict[str, str]) -> None:
        """Save per-package CTX-CARD files."""
        output_dir = self.config.output_path.parent
        base_name = self.config.output_path.stem

        for pkg, content in packages.items():
            pkg_path = output_dir / f"{base_name}.{pkg}.md"
            pkg_path.write_text(content, encoding="utf-8")
            print(f"Wrote {pkg_path}")


def main() -> None:
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Generate CTX-CARD v2.1 (raises + PX lints + per-package + delta)."
    )
    parser.add_argument("root", nargs="?", default=".", help="Repository root path")
    parser.add_argument(
        "--proj", default=None, help="Project slug (default: folder name)"
    )
    parser.add_argument("--std", default="pep8", help="Style/standard hint")
    parser.add_argument(
        "--include", default=None, help="Glob include pattern (e.g., '**/*.py')"
    )
    parser.add_argument(
        "--exclude", default=None, help="Glob exclude pattern (e.g., '**/tests/**')"
    )
    parser.add_argument("--out", default="CTXCARD.md", help="Output file path")
    parser.add_argument(
        "--emit-ty", action="store_true", help="Include TY: type signature lines"
    )
    parser.add_argument(
        "--delta-from", default=None, help="Existing CTXCARD to compute Δ against"
    )
    parser.add_argument(
        "--stdout", action="store_true", help="Print to stdout instead of file"
    )
    parser.add_argument(
        "--per-package", action="store_true", help="Generate per-package CTX-CARD files"
    )
    parser.add_argument(
        "--stats", action="store_true", help="Print analysis statistics"
    )

    args = parser.parse_args()

    try:
        # Setup configuration
        root_path = Path(args.root).resolve()
        if not root_path.exists():
            print(f"Error: Root path does not exist: {root_path}", file=sys.stderr)
            sys.exit(1)

        project_name = args.proj or root_path.name
        output_path = Path(args.out)
        delta_from = Path(args.delta_from) if args.delta_from else None

        config = GeneratorConfig(
            project_name=project_name,
            root_path=root_path,
            output_path=output_path,
            include_pattern=args.include,
            exclude_pattern=args.exclude,
            emit_type_signatures=args.emit_ty,
            delta_from=delta_from,
            stdout_output=args.stdout,
            per_package=args.per_package,
        )

        # Generate CTX-CARD
        generator = CTXCardGenerator(config)
        content = generator.generate()

        # Print statistics if requested
        if args.stats:
            analyzer = ASTAnalyzer()
            scan_result = analyzer.analyze_repository(
                root_path, args.include, args.exclude
            )
            stats = analyzer.get_statistics(scan_result)
            print("\nAnalysis Statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
            print()

        # Save main output
        generator.save_output(content)

        # Generate per-package files if requested
        if args.per_package and not args.stdout:
            packages = generator.generate_per_package(content)
            generator.save_per_package(packages)

    except CTXCardError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
