from page_analyzer.services import normalize_url, truncate_text, validate_url


class TestNormalizeUrl:
    def test_normalizes_with_trailing_slash(self):
        assert normalize_url("https://example.com/") == "https://example.com"

    def test_normalizes_to_lowercase(self):
        assert normalize_url("https://Example.COM/path") == "https://example.com"

    def test_strips_whitespace(self):
        assert normalize_url("  https://example.com  ") == "https://example.com"

    def test_preserves_scheme(self):
        assert normalize_url("http://example.com") == "http://example.com"

    def test_removes_path(self):
        assert (
            normalize_url("https://example.com/some/path?q=1") == "https://example.com"
        )


class TestValidateUrl:
    def test_valid_url(self):
        is_valid, msg = validate_url("https://example.com")
        assert is_valid is True
        assert msg == ""

    def test_empty_url(self):
        is_valid, msg = validate_url("")
        assert is_valid is False

    def test_url_too_long(self):
        long_url = "https://" + "a" * 300 + ".com"
        is_valid, msg = validate_url(long_url)
        assert is_valid is False
        assert "255" in msg

    def test_invalid_url_no_scheme(self):
        is_valid, msg = validate_url("example.com")
        assert is_valid is False

    def test_invalid_url_text(self):
        is_valid, msg = validate_url("not a url at all")
        assert is_valid is False


class TestTruncateText:
    def test_short_text_unchanged(self):
        assert truncate_text("hello") == "hello"

    def test_long_text_truncated(self):
        result = truncate_text("a" * 300, max_length=200)
        assert len(result) == 203
        assert result.endswith("...")

    def test_none_returns_empty(self):
        assert truncate_text(None) == ""

    def test_exact_length_unchanged(self):
        text = "a" * 200
        assert truncate_text(text) == text

    def test_custom_max_length(self):
        result = truncate_text("hello world", max_length=5)
        assert result == "hello..."
