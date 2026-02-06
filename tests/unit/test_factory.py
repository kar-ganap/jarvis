from unittest.mock import MagicMock


class TestGetOrCreateAgent:
    def test_creates_new_when_none_exists(
        self, mock_letta_client: MagicMock, test_settings
    ) -> None:
        from jarvis.agent.factory import get_or_create_agent

        mock_letta_client.agents.list.return_value = []

        agent = get_or_create_agent(mock_letta_client, test_settings)

        mock_letta_client.agents.create.assert_called_once()
        assert agent.id == "agent-test-12345"

    def test_returns_existing_agent(
        self, mock_letta_client: MagicMock, test_settings
    ) -> None:
        from jarvis.agent.factory import get_or_create_agent

        existing_agent = MagicMock()
        existing_agent.id = "agent-existing-99999"
        existing_agent.name = "test-jarvis"
        mock_letta_client.agents.list.return_value = [existing_agent]

        agent = get_or_create_agent(mock_letta_client, test_settings)

        mock_letta_client.agents.create.assert_not_called()
        assert agent.id == "agent-existing-99999"

    def test_passes_settings_to_create(
        self, mock_letta_client: MagicMock, test_settings
    ) -> None:
        from jarvis.agent.factory import get_or_create_agent

        mock_letta_client.agents.list.return_value = []

        get_or_create_agent(mock_letta_client, test_settings)

        call_kwargs = mock_letta_client.agents.create.call_args.kwargs
        assert call_kwargs["model"] == "openai/gpt-5.2"
        assert call_kwargs["embedding"] == "openai/text-embedding-3-small"
        assert call_kwargs["context_window_limit"] == 30000
        assert call_kwargs["name"] == "test-jarvis"
