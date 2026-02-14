from __future__ import annotations

from pathlib import Path

import yaml

from jarvis.evals.models import EvalScenario

_DEFAULT_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent / "evals" / "golden_set.yaml"
)


def load_scenarios(
    path: Path | None = None,
    tags: list[str] | None = None,
) -> list[EvalScenario]:
    """Load eval scenarios from a YAML file, optionally filtering by tag."""
    path = path or _DEFAULT_PATH
    raw = yaml.safe_load(path.read_text())
    scenarios = [EvalScenario(**s) for s in raw["scenarios"]]
    if tags:
        scenarios = [s for s in scenarios if set(tags) & set(s.tags)]
    return scenarios
