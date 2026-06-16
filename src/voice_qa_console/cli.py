"""Command line interface for the voice-agent QA console."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .report import render_text
from .rules import analyze_call


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze voice-agent call events.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="Analyze a JSON call event file.")
    analyze.add_argument("path", type=Path)
    analyze.add_argument("--format", choices=("text", "json"), default="text")
    analyze.add_argument("--latency-threshold-ms", type=int, default=2500)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "analyze":
        payload = json.loads(args.path.read_text(encoding="utf-8"))
        report = analyze_call(payload, latency_threshold_ms=args.latency_threshold_ms)
        if args.format == "json":
            print(json.dumps(report.to_dict(), indent=2))
        else:
            print(render_text(report))
        return 0
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
