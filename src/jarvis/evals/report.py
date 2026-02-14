from __future__ import annotations

import json

from jarvis.evals.models import EvalReport


def format_text(report: EvalReport) -> str:
    """Format an EvalReport as human-readable text."""
    lines = [
        f"Eval Report: {report.total} scenarios",
        f"Tool accuracy: {report.tool_accuracy:.1%}",
        f"Avg judge score: {report.avg_overall_score:.2f}",
        "",
    ]
    for r in report.results:
        status = "PASS" if r.tool_match else "FAIL"
        score = f" (judge: {r.judge_score.overall:.2f})" if r.judge_score else ""
        lines.append(f"  [{status}] {r.scenario_id}{score}")
        if r.error:
            lines.append(f"         ERROR: {r.error}")
    return "\n".join(lines)


def format_json(report: EvalReport) -> str:
    """Format an EvalReport as JSON."""
    return json.dumps(report.model_dump(), indent=2, default=str)
