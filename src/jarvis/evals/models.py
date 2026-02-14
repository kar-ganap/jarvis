from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class EvalScenario(BaseModel):
    id: str
    prompt: str
    expected_tools: list[str]
    expected_substring: str = ""
    quality_criteria: str = ""
    tags: list[str] = []


class JudgeScore(BaseModel):
    relevance: float
    helpfulness: float
    safety: float
    overall: float
    reasoning: str


class EvalResult(BaseModel):
    scenario_id: str
    prompt: str
    agent_reply: str | None
    tool_calls: list[dict[str, Any]]
    expected_tools: list[str]
    tool_match: bool
    substring_match: bool | None
    judge_score: JudgeScore | None
    error: str | None = None


class EvalReport(BaseModel):
    total: int
    tool_accuracy: float
    avg_overall_score: float
    results: list[EvalResult]
