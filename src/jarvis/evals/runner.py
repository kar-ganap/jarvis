from __future__ import annotations

import os
from typing import Any

import structlog

from jarvis.agent.response import extract_assistant_text, extract_tool_calls
from jarvis.evals._mock import MockLettaClient, make_mock_response
from jarvis.evals.models import EvalReport, EvalResult, EvalScenario

log = structlog.get_logger()


def run_scenario(
    scenario: EvalScenario,
    client: Any,  # noqa: ANN401
    agent_id: str,
    use_judge: bool = True,
) -> EvalResult:
    """Run a single eval scenario and return the result."""
    try:
        response = client.agents.messages.create(
            agent_id=agent_id,
            messages=[{"role": "user", "content": scenario.prompt}],
        )
        reply = extract_assistant_text(response)
        tool_calls = extract_tool_calls(response)
        called_tools = [tc["tool_name"] for tc in tool_calls]

        # Subset match: expected tools must all be present (agent may call extras)
        tool_match = set(scenario.expected_tools) <= set(called_tools)
        substring_match: bool | None = None
        if scenario.expected_substring:
            substring_match = (
                scenario.expected_substring.lower() in (reply or "").lower()
            )

        judge_score = None
        if use_judge and os.environ.get("OPENAI_API_KEY"):
            from jarvis.evals.judge import score_response

            judge_score = score_response(
                prompt=scenario.prompt,
                reply=reply or "",
                tools=called_tools,
                criteria=scenario.quality_criteria,
            )

        return EvalResult(
            scenario_id=scenario.id,
            prompt=scenario.prompt,
            agent_reply=reply,
            tool_calls=tool_calls,
            expected_tools=scenario.expected_tools,
            tool_match=tool_match,
            substring_match=substring_match,
            judge_score=judge_score,
        )
    except Exception as exc:
        return EvalResult(
            scenario_id=scenario.id,
            prompt=scenario.prompt,
            agent_reply=None,
            tool_calls=[],
            expected_tools=scenario.expected_tools,
            tool_match=False,
            substring_match=None,
            judge_score=None,
            error=str(exc),
        )


def run_eval(
    scenarios: list[EvalScenario],
    client: Any = None,  # noqa: ANN401
    agent_id: str = "",
    use_judge: bool = True,
) -> EvalReport:
    """Run all scenarios and produce an EvalReport."""
    mock_mode = False
    if client is None:
        client = MockLettaClient()
        mock_mode = True

    # Reset conversation history so each eval run starts clean
    if not mock_mode and agent_id:
        try:
            import httpx

            url = f"{client.base_url}/v1/agents/{agent_id}/reset-messages"
            httpx.patch(str(url), json={}, timeout=30)
            log.info("eval.messages_reset", agent_id=agent_id)
        except Exception as exc:
            log.warning("eval.reset_failed", error=str(exc))

    results: list[EvalResult] = []
    for scenario in scenarios:
        if mock_mode:
            client.set_response(
                make_mock_response(scenario.expected_tools),
            )
        result = run_scenario(scenario, client, agent_id, use_judge)
        results.append(result)
        log.info("eval.scenario_done", id=scenario.id, tool_match=result.tool_match)

    tool_matches = sum(1 for r in results if r.tool_match)
    tool_accuracy = tool_matches / len(results) if results else 0.0

    judge_scores = [r.judge_score.overall for r in results if r.judge_score]
    avg_score = sum(judge_scores) / len(judge_scores) if judge_scores else 0.0

    return EvalReport(
        total=len(results),
        tool_accuracy=tool_accuracy,
        avg_overall_score=avg_score,
        results=results,
    )
