from unittest.mock import MagicMock


def _make_msg(message_type: str, content: str = "") -> MagicMock:
    """Helper to create a mock Letta message."""
    msg = MagicMock()
    msg.message_type = message_type
    msg.content = content
    return msg


def _make_response(*msgs: MagicMock) -> MagicMock:
    resp = MagicMock()
    resp.messages = list(msgs)
    return resp


class TestExtractAssistantText:
    def test_single_assistant_message(self) -> None:
        from jarvis.agent.response import extract_assistant_text

        response = _make_response(_make_msg("assistant_message", "Hello there!"))
        assert extract_assistant_text(response) == "Hello there!"

    def test_multiple_assistant_messages(self) -> None:
        from jarvis.agent.response import extract_assistant_text

        response = _make_response(
            _make_msg("assistant_message", "First part."),
            _make_msg("tool_call_message"),
            _make_msg("tool_return_message"),
            _make_msg("assistant_message", "Second part."),
        )
        assert extract_assistant_text(response) == "First part.\nSecond part."

    def test_no_assistant_message(self) -> None:
        from jarvis.agent.response import extract_assistant_text

        response = _make_response(
            _make_msg("tool_call_message"),
            _make_msg("tool_return_message"),
        )
        assert extract_assistant_text(response) is None

    def test_skips_empty_content(self) -> None:
        from jarvis.agent.response import extract_assistant_text

        response = _make_response(
            _make_msg("assistant_message", ""),
            _make_msg("assistant_message", "Actual reply."),
        )
        assert extract_assistant_text(response) == "Actual reply."

    def test_mixed_message_types(self) -> None:
        from jarvis.agent.response import extract_assistant_text

        response = _make_response(
            _make_msg("reasoning_message", "thinking..."),
            _make_msg("tool_call_message"),
            _make_msg("assistant_message", "The answer is 42."),
            _make_msg("tool_return_message"),
        )
        assert extract_assistant_text(response) == "The answer is 42."
