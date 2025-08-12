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

from .core.ast_analyzer import ASTAnalyzer
from .core.card_renderer import CardRenderer
from .exceptions import CTXCardError
from .types import GeneratorConfig


class CTXCardGenerator:
    """Main CTX-CARD generator class."""

    def __init__(self, config: GeneratorConfig, max_workers: int = 4, cache_size: int = 1000):
        self.config = config
        self.analyzer = ASTAnalyzer(max_workers=max_workers, cache_size=cache_size)
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
        extension = self.config.output_path.suffix

        for pkg, content in packages.items():
            pkg_path = output_dir / f"{base_name}.{pkg}{extension}"
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
    parser.add_argument(
        "--show-ignored", action="store_true", help="Show ignored files and patterns"
    )
    parser.add_argument(
        "--format",
        choices=["md", "ctx"],
        default="md",
        help="Output format: 'md' for .md files, 'ctx' for .ctx files (default: md)"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate CTX-CARD output and report errors/warnings"
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="Maximum parallel workers for large codebases (default: 4)"
    )
    parser.add_argument(
        "--cache-size",
        type=int,
        default=1000,
        help="File cache size for performance optimization (default: 1000)"
    )
    parser.add_argument(
        "--export-format",
        choices=["json", "yaml", "xml", "md"],
        help="Export CTX-CARD to additional format (JSON, YAML, XML, or enhanced Markdown)"
    )
    parser.add_argument(
        "--export-path",
        help="Output path for exported format (default: same directory as main output)"
    )

    args = parser.parse_args()

    try:
        # Setup configuration
        root_path = Path(args.root).resolve()
        if not root_path.exists():
            print(f"Error: Root path does not exist: {root_path}", file=sys.stderr)
            sys.exit(1)

        project_name = args.proj or root_path.name

        # Handle output format
        if args.format == "ctx":
            # Use .ctx extension for CTX-CARD format
            output_path = Path(args.out)
            if output_path.suffix == ".md":
                output_path = output_path.with_suffix(".ctx")
            elif output_path.suffix != ".ctx":
                output_path = output_path.with_suffix(".ctx")
        else:
            # Use .md extension for markdown format
            output_path = Path(args.out)
            if output_path.suffix == ".ctx":
                output_path = output_path.with_suffix(".md")
            elif output_path.suffix != ".md":
                output_path = output_path.with_suffix(".md")

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

        # Generate CTX-CARD with performance options
        generator = CTXCardGenerator(config, max_workers=args.max_workers, cache_size=args.cache_size)  # pylint: disable=line-too-long
        content = generator.generate()

        # Validate output if requested
        if args.validate:
            from ctxcard_gen.utils.validation import get_validation_report  # pylint: disable=import-outside-toplevel
            report = get_validation_report(content)

            if report["errors"]:
                print("\nValidation Errors:")
                for error in report["errors"]:
                    print(f"  ❌ {error}")

            if report["warnings"]:
                print("\nValidation Warnings:")
                for warning in report["warnings"]:
                    print(f"  ⚠️  {warning}")

            if report["valid"] and not report["warnings"]:
                print("\n✅ CTX-CARD validation passed")
            print()

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

        # Show ignored files if requested
        if args.show_ignored:
            from ctxcard_gen.utils.ignore import load_ignore_file  # pylint: disable=import-outside-toplevel
            ignore_file = load_ignore_file(root_path)
            patterns = ignore_file.get_ignored_patterns()

            if patterns:
                print("\nIgnored Patterns:")
                for pattern in patterns:
                    print(f"  {pattern}")
                print()
            else:
                print("\nNo .ctxignore file found or no patterns defined.")
                print()

        # Save main output
        generator.save_output(content)

        # Export to additional format if requested
        if args.export_format:
            from ctxcard_gen.utils.export import (  # pylint: disable=import-outside-toplevel
                export_to_json, export_to_yaml, export_to_xml, export_to_markdown
            )

            # Determine export path
            if args.export_path:
                export_path = Path(args.export_path)
            else:
                export_path = output_path.parent / f"{output_path.stem}.{args.export_format}"

            # Export based on format
            if args.export_format == "json":
                export_to_json(content, export_path)
            elif args.export_format == "yaml":
                export_to_yaml(content, export_path)
            elif args.export_format == "xml":
                export_to_xml(content, export_path)
            elif args.export_format == "md":
                export_to_markdown(content, export_path)

            print(f"Exported to {export_path}")

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
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
