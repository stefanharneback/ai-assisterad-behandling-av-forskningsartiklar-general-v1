from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from article_analysis_general import __version__
from article_analysis_general.ingest.discovery import discover_articles


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="article-analysis-general")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("doctor", help="Check that the M0 package can be imported.")

    discover_parser = subparsers.add_parser("discover", help="Discover PDF files and print article stubs as JSON.")
    discover_parser.add_argument("--corpus", default="Forskning", help="Path to a local PDF corpus.")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "doctor":
        print(json.dumps({"status": "ok", "version": __version__}, ensure_ascii=False))
        return 0

    if args.command == "discover":
        articles = discover_articles(Path(args.corpus))
        print(json.dumps([article.model_dump() for article in articles], ensure_ascii=False, indent=2))
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

