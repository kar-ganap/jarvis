from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestGslidesListTool:
    def test_calls_bridge(self, monkeypatch):
        from jarvis.tools.gslides import gslides_list

        monkeypatch.setenv("JARVIS_HTTP_HOST", "localhost")
        monkeypatch.setenv("JARVIS_HTTP_PORT", "9100")

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "results": [{"id": "pres1", "name": "Q4 Review"}]
        }

        with patch("requests.post", return_value=mock_resp) as mock_post:
            result = gslides_list(10)

        mock_post.assert_called_once()
        url = mock_post.call_args[0][0]
        assert "/google/slides/list" in url
        assert "Q4 Review" in result


class TestGslidesReadTool:
    def test_calls_bridge(self, monkeypatch):
        from jarvis.tools.gslides import gslides_read

        monkeypatch.setenv("JARVIS_HTTP_HOST", "localhost")
        monkeypatch.setenv("JARVIS_HTTP_PORT", "9100")

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "id": "pres1",
            "title": "Q4 Review",
            "slides": [{"slide_number": 1, "text": "Hello world"}],
        }

        with patch("requests.post", return_value=mock_resp) as mock_post:
            result = gslides_read("pres1")

        mock_post.assert_called_once()
        url = mock_post.call_args[0][0]
        assert "/google/slides/read" in url
        assert "Q4 Review" in result
        assert "Hello world" in result


class TestGslidesCreateTool:
    def test_calls_bridge(self, monkeypatch):
        from jarvis.tools.gslides import gslides_create

        monkeypatch.setenv("JARVIS_HTTP_HOST", "localhost")
        monkeypatch.setenv("JARVIS_HTTP_PORT", "9100")

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"id": "new-pres", "title": "My Deck"}

        with patch("requests.post", return_value=mock_resp) as mock_post:
            result = gslides_create("My Deck")

        mock_post.assert_called_once()
        url = mock_post.call_args[0][0]
        assert "/google/slides/create" in url
        assert "My Deck" in result


class TestGslidesAddSlideTool:
    def test_calls_bridge(self, monkeypatch):
        from jarvis.tools.gslides import gslides_add_slide

        monkeypatch.setenv("JARVIS_HTTP_HOST", "localhost")
        monkeypatch.setenv("JARVIS_HTTP_PORT", "9100")

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"slide_id": "slide-abc"}

        with patch("requests.post", return_value=mock_resp) as mock_post:
            result = gslides_add_slide("pres1", "New Slide", "Content")

        mock_post.assert_called_once()
        url = mock_post.call_args[0][0]
        assert "/google/slides/add_slide" in url
        assert "slide" in result.lower() or "added" in result.lower()
