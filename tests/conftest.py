from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml


@pytest.fixture()
def tmp_config(tmp_path: Path) -> Path:
    """Create a temporary YAML config file with full settings."""
    config = {
        "letta": {
            "base_url": "http://localhost:8283",
        },
        "agent": {
            "name": "test-jarvis",
            "model": "openai/gpt-5.2",
            "embedding": "openai/text-embedding-3-small",
            "context_window_limit": 30000,
        },
        "user": {
            "name": "TestUser",
            "preferred_channel": "cli",
        },
    }
    config_path = tmp_path / "jarvis.yaml"
    config_path.write_text(yaml.dump(config))
    return config_path


@pytest.fixture()
def minimal_config(tmp_path: Path) -> Path:
    """Create a minimal YAML config with only required sections."""
    config = {
        "letta": {},
        "agent": {},
        "user": {},
    }
    config_path = tmp_path / "jarvis.yaml"
    config_path.write_text(yaml.dump(config))
    return config_path


@pytest.fixture()
def test_settings(tmp_config: Path):
    """Load JarvisSettings from the test config fixture."""
    from jarvis.settings import load_settings

    return load_settings(tmp_config)


@pytest.fixture()
def mock_letta_client() -> MagicMock:
    """Mock Letta client with nested agent/tool/message APIs."""
    client = MagicMock()

    # Mock agent object returned by create/list
    mock_agent = MagicMock()
    mock_agent.id = "agent-test-12345"
    mock_agent.name = "test-jarvis"

    # agents.list() returns empty by default (no existing agent)
    client.agents.list.return_value = []
    # agents.create() returns mock agent
    client.agents.create.return_value = mock_agent

    # Mock message response
    mock_assistant_msg = MagicMock()
    mock_assistant_msg.message_type = "assistant_message"
    mock_assistant_msg.content = "Hello! I'm Jarvis, your AI assistant."

    mock_response = MagicMock()
    mock_response.messages = [mock_assistant_msg]

    client.agents.messages.create.return_value = mock_response

    # Mock tool registration — upsert_from_function returns a tool with id/name
    _tool_counter = iter(range(100))

    def _mock_upsert(func):
        idx = next(_tool_counter)
        tool = MagicMock()
        tool.id = f"tool-{func.__name__}-{idx}"
        tool.name = func.__name__
        return tool

    client.tools.upsert_from_function.side_effect = _mock_upsert

    # agents.tools.list() returns empty by default (no tools attached yet)
    client.agents.tools.list.return_value = []

    return client
