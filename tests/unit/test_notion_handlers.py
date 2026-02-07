from __future__ import annotations

from unittest.mock import MagicMock, patch


def _mock_notion_client():
    """Create a mock Notion client."""
    return MagicMock()


class TestNotionSearch:
    def test_returns_results(self):
        from jarvis.notion.handlers import notion_search

        mock_client = _mock_notion_client()
        mock_client.search.return_value = {
            "results": [
                {
                    "id": "page-1",
                    "object": "page",
                    "url": "https://notion.so/page-1",
                    "properties": {
                        "Name": {
                            "type": "title",
                            "title": [{"plain_text": "Meeting Notes"}],
                        }
                    },
                },
            ],
        }

        with patch("jarvis.notion.handlers._notion_client", return_value=mock_client):
            results = notion_search("meeting", max_results=5)

        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0]["id"] == "page-1"
        assert results[0]["title"] == "Meeting Notes"


class TestNotionReadPage:
    def test_reads_page_content(self):
        from jarvis.notion.handlers import notion_read_page

        mock_client = _mock_notion_client()
        mock_client.pages.retrieve.return_value = {
            "id": "page-1",
            "properties": {
                "Name": {
                    "type": "title",
                    "title": [{"plain_text": "My Page"}],
                }
            },
        }
        mock_client.blocks.children.list.return_value = {
            "results": [
                {
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"plain_text": "Hello world"}]
                    },
                },
                {
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"plain_text": "Section"}]
                    },
                },
            ],
            "has_more": False,
        }

        with patch("jarvis.notion.handlers._notion_client", return_value=mock_client):
            result = notion_read_page("page-1")

        assert result["id"] == "page-1"
        assert result["title"] == "My Page"
        assert "Hello world" in result["content"]
        assert "Section" in result["content"]


class TestNotionCreatePage:
    def test_creates_page(self):
        from jarvis.notion.handlers import notion_create_page

        mock_client = _mock_notion_client()
        mock_client.pages.create.return_value = {
            "id": "new-page",
            "url": "https://notion.so/new-page",
        }

        with patch("jarvis.notion.handlers._notion_client", return_value=mock_client):
            result = notion_create_page("parent-1", "Test Page", "Some content")

        assert result["id"] == "new-page"
        mock_client.pages.create.assert_called_once()
        call_kwargs = mock_client.pages.create.call_args[1]
        assert call_kwargs["parent"]["page_id"] == "parent-1"


class TestNotionAppendBlocks:
    def test_appends_content(self):
        from jarvis.notion.handlers import notion_append_blocks

        mock_client = _mock_notion_client()
        mock_client.blocks.children.append.return_value = {
            "results": [{"id": "block-1"}, {"id": "block-2"}]
        }

        with patch("jarvis.notion.handlers._notion_client", return_value=mock_client):
            result = notion_append_blocks("page-1", "Line 1\n\nLine 2")

        assert result["block_count"] == 2
        mock_client.blocks.children.append.assert_called_once()


class TestNotionQueryDatabase:
    def test_queries_with_filter(self):
        from jarvis.notion.handlers import notion_query_database

        mock_client = _mock_notion_client()
        mock_client.databases.query.return_value = {
            "results": [
                {
                    "id": "row-1",
                    "properties": {
                        "Name": {
                            "title": [{"plain_text": "Task 1"}]
                        },
                        "Status": {
                            "select": {"name": "Done"}
                        },
                    },
                },
            ],
            "has_more": False,
        }

        filter_json = '{"property": "Status", "select": {"equals": "Done"}}'
        with patch("jarvis.notion.handlers._notion_client", return_value=mock_client):
            results = notion_query_database("db-1", filter_json)

        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0]["id"] == "row-1"
