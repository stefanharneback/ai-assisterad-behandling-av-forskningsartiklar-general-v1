from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from article_analysis_general import __version__
from article_analysis_general.ingest.discovery import discover_articles
from article_analysis_general.output.inventory import INVENTORY_FILENAME, write_inventory
from article_analysis_general.store.run import write_run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="article-analysis-general")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("doctor", help="Check that the M0 package can be imported.")

    discover_parser = subparsers.add_parser("discover", help="Discover PDF files and print article stubs as JSON.")
    discover_parser.add_argument("--corpus", default="Forskning", help="Path to a local PDF corpus.")

    ingest_parser = subparsers.add_parser(
        "ingest", help="Discover PDFs and write canonical article records and a run manifest."
    )
    ingest_parser.add_argument("--corpus", default="Forskning", help="Path to a local PDF corpus.")
    ingest_parser.add_argument("--out", default="runs", help="Base directory for run output folders.")

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

    if args.command == "ingest":
        base_dir = Path(args.out)
        articles = discover_articles(Path(args.corpus))
        manifest = write_run(articles, corpus=args.corpus, base_dir=base_dir)
        run_dir = base_dir / manifest.run_id
        write_inventory(articles, run_dir / INVENTORY_FILENAME)
        summary = {
            "run_id": manifest.run_id,
            "run_dir": str(run_dir),
            "article_count": manifest.article_count,
            "source_count": manifest.source_count,
            "text_layer_counts": manifest.text_layer_counts,
            "inventory": str(run_dir / INVENTORY_FILENAME),
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

