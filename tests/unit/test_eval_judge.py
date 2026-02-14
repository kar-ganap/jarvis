import json
from unittest.mock import MagicMock, patch


class TestJudge:
    def test_score_parses_valid_json(self) -> None:
        from jarvis.evals.judge import score_response

        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock()]
        mock_resp.choices[0].message.content = json.dumps({
            "relevance": 0.9,
            "helpfulness": 0.85,
            "safety": 1.0,
            "overall": 0.9,
            "reasoning": "Good response",
        })

        with patch("jarvis.evals.judge.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_resp
            mock_openai.return_value = mock_client

            score = score_response(
                prompt="Search my email",
                reply="Found 3 emails from GitHub.",
                tools=["gmail_search"],
            )

        assert score.relevance == 0.9
        assert score.helpfulness == 0.85
        assert score.safety == 1.0
        assert score.overall == 0.9
        assert score.reasoning == "Good response"

    def test_score_handles_llm_error(self) -> None:
        from jarvis.evals.judge import score_response

        with patch("jarvis.evals.judge.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = RuntimeError("API down")
            mock_openai.return_value = mock_client

            score = score_response(
                prompt="test",
                reply="test reply",
                tools=[],
            )

        assert score.overall == 0.0
        assert "Judge error" in score.reasoning

    def test_score_without_criteria(self) -> None:
        from jarvis.evals.judge import score_response

        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock()]
        mock_resp.choices[0].message.content = json.dumps({
            "relevance": 0.8,
            "helpfulness": 0.7,
            "safety": 1.0,
            "overall": 0.8,
            "reasoning": "Adequate",
        })

        with patch("jarvis.evals.judge.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_resp
            mock_openai.return_value = mock_client

            score = score_response(
                prompt="Hello",
                reply="Hi there!",
                tools=[],
                criteria="",
            )

        assert score.overall == 0.8
