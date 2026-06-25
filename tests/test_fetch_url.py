"""Tests for fetch_url tool."""

from unittest.mock import MagicMock, patch

from chatbot.tools.fetch_url import _strip_html, fetch_url, fetch_url_tool


class TestFetchUrlTool:
    """Test the fetch_url tool definition."""

    def test_tool_has_name(self):
        assert fetch_url_tool.name == "fetch_url"

    def test_tool_has_description(self):
        assert "fetch" in fetch_url_tool.description.lower()

    def test_tool_requires_url(self):
        assert "url" in fetch_url_tool.parameters["properties"]
        assert "url" in fetch_url_tool.parameters["required"]


class TestFetchUrl:
    """Test the fetch_url function."""

    @patch("chatbot.tools.fetch_url.subprocess.run")
    def test_fetches_url_successfully(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="<html><body>Hello World</body></html>",
            stderr="",
        )
        result = fetch_url("https://example.com")
        assert "Hello World" in result

    @patch("chatbot.tools.fetch_url.subprocess.run")
    def test_returns_error_on_failure(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Connection refused",
        )
        result = fetch_url("https://example.com")
        assert "Error" in result

    @patch("chatbot.tools.fetch_url.subprocess.run")
    def test_handles_empty_response(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr="",
        )
        result = fetch_url("https://example.com")
        assert "Error" in result

    @patch("chatbot.tools.fetch_url.subprocess.run")
    def test_handles_timeout(self, mock_run):
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired(cmd="curl", timeout=35)
        result = fetch_url("https://example.com")
        assert "timed out" in result

    @patch("chatbot.tools.fetch_url.subprocess.run")
    def test_strips_html(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="<html><body><h1>Title</h1><p>Paragraph</p></body></html>",
            stderr="",
        )
        result = fetch_url("https://example.com")
        assert "Title" in result
        assert "Paragraph" in result
        assert "<h1>" not in result
        assert "<p>" not in result

    @patch("chatbot.tools.fetch_url.subprocess.run")
    def test_truncates_long_content(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="x" * 100000,
            stderr="",
        )
        result = fetch_url("https://example.com")
        assert "truncated" in result
        assert len(result) < 60000

    @patch("chatbot.tools.fetch_url.subprocess.run")
    def test_plain_text_not_stripped(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="This is plain text content",
            stderr="",
        )
        result = fetch_url("https://example.com")
        assert result == "This is plain text content"


class TestStripHtml:
    """Test the HTML stripping function."""

    def test_strips_tags(self):
        html = "<p>Hello <b>world</b></p>"
        result = _strip_html(html)
        assert result == "Hello world"

    def test_removes_scripts(self):
        html = "<html><script>alert('xss')</script><p>Content</p></html>"
        result = _strip_html(html)
        assert "alert" not in result
        assert "Content" in result

    def test_removes_styles(self):
        html = "<html><style>body{color:red}</style><p>Content</p></html>"
        result = _strip_html(html)
        assert "color:red" not in result
        assert "Content" in result

    def test_decodes_entities(self):
        html = "<p>&amp; &lt; &gt; &quot; &#39; &nbsp;</p>"
        result = _strip_html(html)
        assert "&" in result
        assert "<" in result
        assert ">" in result
        assert '"' in result
        assert "'" in result

    def test_converts_br_to_newlines(self):
        html = "Line 1<br>Line 2<br/>Line 3"
        result = _strip_html(html)
        assert "Line 1\nLine 2\nLine 3" in result

    def test_cleans_whitespace(self):
        html = "<p>  Multiple   spaces  </p>"
        result = _strip_html(html)
        assert "  " not in result
