from __future__ import annotations

from unittest.mock import MagicMock

import pytest


class TestMemorySave:
    def test_saves_note_with_category(self):
        from jarvis.memory.handlers import memory_save

        mock_client = MagicMock()

        result = memory_save(mock_client, "agent-1", "buy milk", category="grocery")

        assert result["status"] == "saved"
        mock_client.agents.passages.create.assert_called_once()
        call_kwargs = mock_client.agents.passages.create.call_args[1]
        assert call_kwargs["agent_id"] == "agent-1"
        assert call_kwargs["text"] == "buy milk"
        assert call_kwargs["tags"] == ["grocery"]

    def test_saves_note_without_category(self):
        from jarvis.memory.handlers import memory_save

        mock_client = MagicMock()

        result = memory_save(mock_client, "agent-1", "remember this")

        assert result["status"] == "saved"
        call_kwargs = mock_client.agents.passages.create.call_args[1]
        assert call_kwargs["text"] == "remember this"
        assert call_kwargs["tags"] == []


class TestMemoryRecall:
    def test_recalls_notes(self):
        from jarvis.memory.handlers import memory_recall

        mock_client = MagicMock()
        mock_entry = MagicMock()
        mock_entry.content = "buy milk"
        mock_entry.timestamp = "2026-01-15T10:00:00Z"
        mock_entry.tags = ["grocery"]

        mock_response = MagicMock()
        mock_response.results = [mock_entry]
        mock_client.agents.passages.search.return_value = mock_response

        results = memory_recall(mock_client, "agent-1", "milk")

        assert len(results) == 1
        assert "buy milk" in results[0]["text"]

    def test_recalls_with_category_filter(self):
        from jarvis.memory.handlers import memory_recall

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.results = []
        mock_client.agents.passages.search.return_value = mock_response

        memory_recall(mock_client, "agent-1", "milk", category="grocery")

        mock_client.agents.passages.search.assert_called_once()
        call_kwargs = mock_client.agents.passages.search.call_args[1]
        assert "[grocery]" in call_kwargs["query"]

    def test_recalls_empty_results(self):
        from jarvis.memory.handlers import memory_recall

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.results = []
        mock_client.agents.passages.search.return_value = mock_response

        results = memory_recall(mock_client, "agent-1", "nonexistent")

        assert results == []


class TestCollectUsageStats:
    def test_collects_message_and_tool_stats(self):
        from jarvis.memory.learning import collect_usage_stats

        stats = collect_usage_stats()

        assert "channels" in stats
        assert "tools" in stats
        assert isinstance(stats["channels"], dict)
        assert isinstance(stats["tools"], dict)


class TestBuildUsageSummary:
    def test_builds_summary_from_stats(self):
        from jarvis.memory.learning import build_usage_summary

        stats = {
            "channels": {"cli": 10.0, "slack": 5.0, "whatsapp": 20.0},
            "tools": {"gmail_search": 8.0, "gcal_list_events": 3.0},
        }

        summary = build_usage_summary(stats)

        assert isinstance(summary, str)
        assert "whatsapp" in summary.lower() or "20" in summary
        assert len(summary) > 0


@pytest.mark.asyncio
class TestUpdateHumanBlock:
    async def test_updates_block(self):
        from jarvis.memory.learning import update_human_block

        mock_client = MagicMock()
        mock_block = MagicMock()
        mock_block.label = "human"
        mock_block.id = "block-1"
        mock_block.value = "Name: Kartik\nPreferences: (to be learned over time)"

        mock_client.agents.blocks.list.return_value = [mock_block]

        await update_human_block(mock_client, "agent-1", "Most active on WhatsApp")

        mock_client.blocks.update.assert_called_once()
        call_kwargs = mock_client.blocks.update.call_args[1]
        assert "Most active on WhatsApp" in call_kwargs["value"]


@pytest.mark.asyncio
class TestRunLearningCycle:
    async def test_full_cycle(self):
        from jarvis.memory.learning import run_learning_cycle
        from jarvis.monitoring.metrics import MESSAGE_COUNT

        # Generate some counter data so the cycle doesn't skip
        MESSAGE_COUNT.labels(channel="cli", direction="inbound").inc(5)

        mock_client = MagicMock()
        mock_block = MagicMock()
        mock_block.label = "human"
        mock_block.id = "block-1"
        mock_block.value = "Name: Kartik"

        mock_client.agents.blocks.list.return_value = [mock_block]

        await run_learning_cycle(mock_client, "agent-1")

        # Should have attempted to update the human block
        mock_client.blocks.update.assert_called_once()
