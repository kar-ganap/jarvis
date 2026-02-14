from unittest.mock import MagicMock


class TestMockLettaClient:
    def test_returns_canned_response(self) -> None:
        from jarvis.evals._mock import MockLettaClient, make_mock_response

        client = MockLettaClient()
        resp = make_mock_response(["gmail_search"])
        client.set_response(resp)

        result = client.agents.messages.create(
            agent_id="test", messages=[{"role": "user", "content": "hi"}],
        )
        # Should have a tool_call_message
        tc_msgs = [m for m in result.messages if m.message_type == "tool_call_message"]
        assert len(tc_msgs) == 1
        assert tc_msgs[0].tool_call.name == "gmail_search"

    def test_returns_assistant_text(self) -> None:
        from jarvis.evals._mock import make_mock_response

        resp = make_mock_response(["shell_exec"], reply_text="Command executed.")
        assist_msgs = [
            m for m in resp.messages if m.message_type == "assistant_message"
        ]
        assert len(assist_msgs) == 1
        assert assist_msgs[0].content == "Command executed."


class TestEvalRunner:
    def test_run_single_scenario_mock(self) -> None:
        from jarvis.evals.models import EvalScenario
        from jarvis.evals.runner import run_eval

        scenarios = [
            EvalScenario(
                id="test1",
                prompt="Search email",
                expected_tools=["gmail_search"],
                tags=["gmail"],
            ),
        ]
        report = run_eval(scenarios, use_judge=False)
        assert report.total == 1
        assert report.tool_accuracy == 1.0
        assert report.results[0].tool_match is True

    def test_run_reports_tool_accuracy(self) -> None:
        from jarvis.evals._mock import MockLettaClient, make_mock_response
        from jarvis.evals.models import EvalScenario
        from jarvis.evals.runner import run_eval

        scenarios = [
            EvalScenario(id="s1", prompt="p1", expected_tools=["tool_a"], tags=[]),
            EvalScenario(id="s2", prompt="p2", expected_tools=["tool_b"], tags=[]),
            EvalScenario(id="s3", prompt="p3", expected_tools=["tool_c"], tags=[]),
        ]

        # Use a custom client where s2 returns wrong tool
        client = MockLettaClient()
        responses = [
            make_mock_response(["tool_a"]),
            make_mock_response(["wrong_tool"]),  # mismatch
            make_mock_response(["tool_c"]),
        ]

        call_count = 0
        original_create = client.agents.messages.create

        def side_effect(**kwargs: object) -> MagicMock:
            nonlocal call_count
            client.set_response(responses[call_count])
            call_count += 1
            return original_create(**kwargs)

        client.agents.messages.create = side_effect

        report = run_eval(scenarios, client=client, use_judge=False)
        assert report.total == 3
        assert abs(report.tool_accuracy - 2 / 3) < 0.01

    def test_run_skips_judge_when_no_api_key(self, monkeypatch: object) -> None:
        from jarvis.evals.models import EvalScenario
        from jarvis.evals.runner import run_eval

        monkeypatch.delenv("OPENAI_API_KEY", raising=False)  # type: ignore[union-attr]

        scenarios = [
            EvalScenario(
                id="test1",
                prompt="Hello",
                expected_tools=[],
                tags=["chat"],
            ),
        ]
        report = run_eval(scenarios, use_judge=True)
        assert report.results[0].judge_score is None
