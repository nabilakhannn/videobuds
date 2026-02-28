"""Unit tests for app/filters.py — simple_md and fromjson Jinja filters."""

import pytest
from app.filters import simple_md, fromjson


# ── fromjson ───────────────────────────────────────────────────────────────

class TestFromjson:
    def test_valid_list(self):
        assert fromjson('["a","b"]') == ["a", "b"]

    def test_valid_dict(self):
        assert fromjson('{"k": 1}') == {"k": 1}

    def test_empty_string(self):
        assert fromjson("") == []

    def test_none(self):
        assert fromjson(None) == []

    def test_invalid_json(self):
        assert fromjson("{broken") == []

    def test_number_string(self):
        # Valid JSON but unusual — should still parse
        assert fromjson("42") == 42


# ── simple_md ──────────────────────────────────────────────────────────────

class TestSimpleMd:
    def test_empty_string(self):
        assert simple_md("") == ""

    def test_none(self):
        assert simple_md(None) == ""

    def test_plain_text(self):
        result = simple_md("Hello world")
        assert "Hello world" in result
        assert result.startswith('<p class="mb-2">')
        assert result.endswith("</p>")

    def test_bold(self):
        result = simple_md("This is **bold** text")
        assert "<strong" in result
        assert "bold" in result

    def test_italic(self):
        result = simple_md("This is *italic* text")
        assert "<em>" in result
        assert "italic" in result

    def test_h2(self):
        result = simple_md("## My Header")
        assert "<h2" in result
        assert "My Header" in result

    def test_h3(self):
        result = simple_md("### Sub Header")
        assert "<h3" in result
        assert "Sub Header" in result

    def test_unordered_list_dash(self):
        result = simple_md("- Item one\n- Item two")
        assert result.count("<li") == 2
        assert "list-disc" in result

    def test_unordered_list_star(self):
        result = simple_md("* Bullet one\n* Bullet two")
        assert result.count("<li") == 2

    def test_numbered_list_dot(self):
        result = simple_md("1. First\n2. Second")
        assert result.count("<li") == 2
        assert "list-decimal" in result

    def test_numbered_list_paren(self):
        result = simple_md("1) First\n2) Second")
        assert result.count("<li") == 2

    def test_paragraph_break(self):
        result = simple_md("Para one\n\nPara two")
        assert "</p><p" in result

    def test_line_break(self):
        result = simple_md("Line one\nLine two")
        assert "<br>" in result

    def test_xss_prevention(self):
        """Ensure HTML in input is escaped (security critical)."""
        result = simple_md('<script>alert("xss")</script>')
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_xss_bold_injection(self):
        """Ensure XSS inside bold markers is still escaped."""
        result = simple_md('**<img src=x onerror=alert(1)>**')
        assert "<img" not in result
        assert "&lt;img" in result


# ── Integration: filter registration ──────────────────────────────────────

class TestRegisterFilters:
    def test_filters_registered_on_app(self):
        """Verify register_filters adds both filters to the Jinja env."""
        from app import create_app
        app = create_app("testing")
        assert "simple_md" in app.jinja_env.filters
        assert "fromjson" in app.jinja_env.filters

    def test_simple_md_filter_works_in_template(self):
        """End-to-end: render a template string using the simple_md filter.

        Note: templates use ``| simple_md | safe`` to render raw HTML.
        IMPORTANT: Must use ``create_app("testing")`` — never ``"default"`` —
        because ``create_app("default")`` binds the SQLAlchemy engine to the
        production ``videobuds.db`` file, which can cause data loss if
        ``db.drop_all()`` is called later in the test session.
        """
        from app import create_app
        app = create_app("testing")
        with app.app_context():
            rendered = app.jinja_env.from_string(
                '{{ text | simple_md | safe }}'
            ).render(text="**Hello**")
            assert "<strong" in rendered
            assert "Hello" in rendered
