import json
from unittest.mock import patch


class TestEvalReport:
    def test_format_text_report(self) -> None:
        from jarvis.evals.models import EvalReport, EvalResult
        from jarvis.evals.report import format_text

        report = EvalReport(
            total=2,
            tool_accuracy=0.5,
            avg_overall_score=0.0,
            results=[
                EvalResult(
                    scenario_id="s1",
                    prompt="Search email",
                    agent_reply="Found it.",
                    tool_calls=[{"tool_name": "gmail_search", "arguments": {}}],
                    expected_tools=["gmail_search"],
                    tool_match=True,
                    substring_match=None,
                    judge_score=None,
                ),
                EvalResult(
                    scenario_id="s2",
                    prompt="Create doc",
                    agent_reply="Done.",
                    tool_calls=[{"tool_name": "wrong_tool", "arguments": {}}],
                    expected_tools=["gdocs_create"],
                    tool_match=False,
                    substring_match=None,
                    judge_score=None,
                ),
            ],
        )
        text = format_text(report)
        assert "2 scenarios" in text
        assert "50.0%" in text
        assert "[PASS] s1" in text
        assert "[FAIL] s2" in text

    def test_format_json_report(self) -> None:
        from jarvis.evals.models import EvalReport, EvalResult
        from jarvis.evals.report import format_json

        report = EvalReport(
            total=1,
            tool_accuracy=1.0,
            avg_overall_score=0.0,
            results=[
                EvalResult(
                    scenario_id="s1",
                    prompt="test",
                    agent_reply="reply",
                    tool_calls=[],
                    expected_tools=[],
                    tool_match=True,
                    substring_match=None,
                    judge_score=None,
                ),
            ],
        )
        result = json.loads(format_json(report))
        assert result["total"] == 1
        assert result["tool_accuracy"] == 1.0


class TestEvalCli:
    def test_main_runs_offline(self) -> None:
        from jarvis.evals.__main__ import main

        with patch("jarvis.evals.__main__.load_scenarios") as mock_load, \
             patch("jarvis.evals.__main__.run_eval") as mock_run, \
             patch("sys.argv", ["evals"]):
            from jarvis.evals.models import EvalReport

            mock_load.return_value = []
            mock_run.return_value = EvalReport(
                total=0, tool_accuracy=1.0, avg_overall_score=0.0, results=[],
            )
            # Should not raise
            try:
                main()
            except SystemExit as e:
                assert e.code == 0

    def test_main_filters_by_tag(self) -> None:
        from jarvis.evals.__main__ import main

        with patch("jarvis.evals.__main__.load_scenarios") as mock_load, \
             patch("jarvis.evals.__main__.run_eval") as mock_run, \
             patch("sys.argv", ["evals", "--tags", "gmail", "--no-judge"]):
            from jarvis.evals.models import EvalReport

            mock_load.return_value = []
            mock_run.return_value = EvalReport(
                total=0, tool_accuracy=1.0, avg_overall_score=0.0, results=[],
            )
            try:
                main()
            except SystemExit as e:
                assert e.code == 0

            # Verify load_scenarios was called with tags
            call_kwargs = mock_load.call_args
            assert call_kwargs.kwargs.get("tags") == ["gmail"] or \
                   (call_kwargs.args and call_kwargs.args[0] is None)
