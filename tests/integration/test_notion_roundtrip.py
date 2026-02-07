from __future__ import annotations

import os

import pytest

NOTION_API_KEY = os.environ.get("NOTION_API_KEY", "")
pytestmark = pytest.mark.skipif(
    not NOTION_API_KEY, reason="NOTION_API_KEY not set"
)


class TestNotionIntegration:
    def test_search_returns_results(self):
        from jarvis.notion.handlers import notion_search

        results = notion_search("test", max_results=3)
        assert isinstance(results, list)

    def test_create_and_read_page(self):
        """Create a page, then read it back to verify content."""
        from jarvis.notion.handlers import (
            notion_create_page,
            notion_read_page,
            notion_search,
        )

        # Find a parent page to create under (search for anything)
        search_results = notion_search("", max_results=1)
        if not search_results:
            pytest.skip("No accessible Notion pages found")

        parent_id = search_results[0]["id"]
        created = notion_create_page(
            parent_id, "Jarvis Test Page", "Integration test content"
        )
        assert "id" in created

        # Read it back
        page = notion_read_page(created["id"])
        assert page["title"] == "Jarvis Test Page"
        assert "Integration test content" in page["content"]
