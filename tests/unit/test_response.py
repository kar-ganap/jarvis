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


def _make_tool_call_msg(tool_name: str, arguments: str = "{}") -> MagicMock:
    """Helper to create a mock Letta tool_call_message."""
    msg = MagicMock()
    msg.message_type = "tool_call_message"
    msg.tool_call = MagicMock()
    msg.tool_call.name = tool_name
    msg.tool_call.arguments = arguments
    msg.tool_call.tool_call_id = f"tc_{tool_name}"
    return msg


class TestExtractToolCalls:
    def test_extracts_single_tool_call(self) -> None:
        from jarvis.agent.response import extract_tool_calls

        response = _make_response(
            _make_tool_call_msg("gmail_search", '{"query": "test"}'),
            _make_msg("assistant_message", "Found 3 emails."),
        )
        result = extract_tool_calls(response)
        assert len(result) == 1
        assert result[0]["tool_name"] == "gmail_search"
        assert result[0]["arguments"] == {"query": "test"}

    def test_extracts_multiple_tool_calls(self) -> None:
        from jarvis.agent.response import extract_tool_calls

        response = _make_response(
            _make_tool_call_msg("gmail_search", '{"query": "test"}'),
            _make_msg("assistant_message", "Searching..."),
            _make_tool_call_msg("gmail_read", '{"message_id": "123"}'),
        )
        result = extract_tool_calls(response)
        assert len(result) == 2
        assert result[0]["tool_name"] == "gmail_search"
        assert result[1]["tool_name"] == "gmail_read"

    def test_no_tool_calls_returns_empty(self) -> None:
        from jarvis.agent.response import extract_tool_calls

        response = _make_response(
            _make_msg("assistant_message", "Hello!"),
        )
        result = extract_tool_calls(response)
        assert result == []

    def test_handles_malformed_arguments(self) -> None:
        from jarvis.agent.response import extract_tool_calls

        response = _make_response(
            _make_tool_call_msg("shell_exec", "not valid json"),
        )
        result = extract_tool_calls(response)
        assert len(result) == 1
        assert result[0]["tool_name"] == "shell_exec"
        assert result[0]["arguments"] == "not valid json"
