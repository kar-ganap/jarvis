"""Entry point: python -m jarvis.evals"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from jarvis.evals.loader import load_scenarios
from jarvis.evals.report import format_json, format_text
from jarvis.evals.runner import run_eval


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Jarvis agent evaluations")
    parser.add_argument("--tags", nargs="*", help="Filter scenarios by tag")
    parser.add_argument(
        "--format", choices=["text", "json"], default="text", dest="output_format",
    )
    parser.add_argument(
        "--no-judge", action="store_true", help="Skip LLM judge scoring",
    )
    parser.add_argument("--golden-set", help="Path to golden set YAML")
    parser.add_argument(
        "--agent-id", help="Letta agent ID (enables online mode)",
    )
    parser.add_argument(
        "--letta-url", default="http://localhost:8283",
        help="Letta server URL (default: http://localhost:8283)",
    )
    args = parser.parse_args()

    golden_path = Path(args.golden_set) if args.golden_set else None
    scenarios = load_scenarios(path=golden_path, tags=args.tags)

    client = None
    if args.agent_id:
        from letta_client import Letta

        client = Letta(base_url=args.letta_url)

    report = run_eval(
        scenarios,
        client=client,
        agent_id=args.agent_id or "",
        use_judge=not args.no_judge,
    )

    if args.output_format == "json":
        print(format_json(report))
    else:
        print(format_text(report))

    sys.exit(0 if report.tool_accuracy >= 0.8 else 1)


if __name__ == "__main__":
    main()
