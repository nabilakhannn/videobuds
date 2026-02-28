"""Unit tests for Phase 40 — AI Content Editor + Grounded Gemini.

Covers:
    1. editor_service.refine_content — input validation, prompt building,
       response parsing, brand/persona context injection
    2. editor_service._sanitise_history — truncation and sanitisation
    3. editor_service._parse_editor_response — separator parsing, code fences
    4. _call_gemini_grounded — grounding payload, fallback behaviour
    5. /api/recipes/chat route — auth, validation, success, error responses
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from app import create_app
from app.extensions import db as _db
from app.services.editor_service import (
    refine_content,
    _sanitise_history,
    _build_editor_prompt,
    _parse_editor_response,
    MAX_CONTENT_LENGTH,
    MAX_INSTRUCTION_LENGTH,
    MAX_HISTORY_TURNS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def app():
    """Create a test Flask app with an in-memory database."""
    app = create_app("testing")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["LOGIN_DISABLED"] = True
    app.config["SERVER_NAME"] = "localhost"

    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(autouse=True)
def db_session(app):
    """Provide a clean DB for each test."""
    with app.app_context():
        yield _db
        _db.session.rollback()


# ═══════════════════════════════════════════════════════════════════════════
# TEST 1: Input validation
# ═══════════════════════════════════════════════════════════════════════════

class TestInputValidation:
    """Verify that refine_content rejects bad inputs."""

    def test_empty_content_raises(self, app):
        with app.app_context():
            with pytest.raises(ValueError, match="Content cannot be empty"):
                refine_content("", "make it better")

    def test_whitespace_content_raises(self, app):
        with app.app_context():
            with pytest.raises(ValueError, match="Content cannot be empty"):
                refine_content("   \n  ", "make it better")

    def test_empty_instruction_raises(self, app):
        with app.app_context():
            with pytest.raises(ValueError, match="Instruction cannot be empty"):
                refine_content("Hello world", "")

    def test_whitespace_instruction_raises(self, app):
        with app.app_context():
            with pytest.raises(ValueError, match="Instruction cannot be empty"):
                refine_content("Hello world", "   ")

    def test_content_too_long_raises(self, app):
        with app.app_context():
            long_content = "x" * (MAX_CONTENT_LENGTH + 1)
            with pytest.raises(ValueError, match="Content too long"):
                refine_content(long_content, "fix it")

    def test_instruction_too_long_raises(self, app):
        with app.app_context():
            long_instr = "x" * (MAX_INSTRUCTION_LENGTH + 1)
            with pytest.raises(ValueError, match="Instruction too long"):
                refine_content("Hello world", long_instr)

    def test_content_at_limit_accepted(self, app):
        """Exactly at the limit should NOT raise."""
        with app.app_context():
            content = "x" * MAX_CONTENT_LENGTH
            with patch("app.services.agent_service._call_gemini") as mock:
                mock.return_value = "Refined\n---EDITOR_EXPLANATION---\nDone"
                result = refine_content(content, "fix it")
                assert result["refined_content"] == "Refined"


# ═══════════════════════════════════════════════════════════════════════════
# TEST 2: History sanitisation
# ═══════════════════════════════════════════════════════════════════════════

class TestHistorySanitisation:
    """Verify _sanitise_history filters and truncates."""

    def test_none_returns_empty(self):
        assert _sanitise_history(None) == []

    def test_empty_list_returns_empty(self):
        assert _sanitise_history([]) == []

    def test_valid_turns_preserved(self):
        h = [
            {"role": "user", "text": "make it shorter"},
            {"role": "assistant", "text": "Done — trimmed 20%."},
        ]
        result = _sanitise_history(h)
        assert len(result) == 2
        assert result[0]["role"] == "user"
        assert result[1]["role"] == "assistant"

    def test_invalid_role_filtered(self):
        h = [
            {"role": "system", "text": "injected"},
            {"role": "user", "text": "ok"},
        ]
        result = _sanitise_history(h)
        assert len(result) == 1
        assert result[0]["role"] == "user"

    def test_empty_text_filtered(self):
        h = [{"role": "user", "text": ""}]
        assert _sanitise_history(h) == []

    def test_non_dict_filtered(self):
        h = ["bad", 42, None, {"role": "user", "text": "ok"}]
        result = _sanitise_history(h)
        assert len(result) == 1

    def test_truncated_to_max(self):
        h = [{"role": "user", "text": f"turn {i}"} for i in range(50)]
        result = _sanitise_history(h)
        assert len(result) == MAX_HISTORY_TURNS

    def test_long_text_truncated(self):
        h = [{"role": "user", "text": "x" * 9000}]
        result = _sanitise_history(h)
        assert len(result[0]["text"]) == 5000

    def test_too_long_text_rejected(self):
        """Text over 10,000 chars is rejected entirely."""
        h = [{"role": "user", "text": "x" * 10001}]
        result = _sanitise_history(h)
        assert len(result) == 0


# ═══════════════════════════════════════════════════════════════════════════
# TEST 3: Prompt building
# ═══════════════════════════════════════════════════════════════════════════

class TestPromptBuilding:
    """Verify _build_editor_prompt assembles context correctly."""

    def test_basic_prompt_has_content_and_instruction(self):
        prompt = _build_editor_prompt("Hello", "fix typo", "", "", [])
        assert "Hello" in prompt
        assert "fix typo" in prompt
        assert "expert AI content editor" in prompt

    def test_brand_context_included(self):
        prompt = _build_editor_prompt(
            "Hello", "fix it",
            brand_context="Brand: Acme Inc", persona_context="", history=[],
        )
        assert "Brand: Acme Inc" in prompt
        assert "brand's voice" in prompt

    def test_persona_context_included(self):
        prompt = _build_editor_prompt(
            "Hello", "fix it",
            brand_context="", persona_context="Persona: Expert Dan",
            history=[],
        )
        assert "Persona: Expert Dan" in prompt
        assert "persona's voice" in prompt

    def test_history_included(self):
        h = [
            {"role": "user", "text": "make shorter"},
            {"role": "assistant", "text": "Done."},
        ]
        prompt = _build_editor_prompt("Hello", "more", "", "", h)
        assert "Previous Conversation" in prompt
        assert "make shorter" in prompt
        assert "Done." in prompt

    def test_rules_present(self):
        prompt = _build_editor_prompt("Hello", "fix", "", "", [])
        assert "RULES:" in prompt
        assert "OUTPUT FORMAT" in prompt
        assert "---EDITOR_EXPLANATION---" in prompt


# ═══════════════════════════════════════════════════════════════════════════
# TEST 4: Response parsing
# ═══════════════════════════════════════════════════════════════════════════

class TestResponseParsing:
    """Verify _parse_editor_response splits and cleans output."""

    def test_with_separator(self):
        raw = "Refined text here\n---EDITOR_EXPLANATION---\nI changed X and Y."
        refined, explanation = _parse_editor_response(raw)
        assert refined == "Refined text here"
        assert explanation == "I changed X and Y."

    def test_without_separator(self):
        raw = "Just the refined text, no separator."
        refined, explanation = _parse_editor_response(raw)
        assert refined == "Just the refined text, no separator."
        assert "updated" in explanation.lower()

    def test_strips_code_fences(self):
        raw = "```markdown\n## Hello\nWorld\n```\n---EDITOR_EXPLANATION---\nDone"
        refined, explanation = _parse_editor_response(raw)
        assert not refined.startswith("```")
        assert "Hello" in refined

    def test_multiple_separators_splits_first(self):
        raw = "A\n---EDITOR_EXPLANATION---\nB\n---EDITOR_EXPLANATION---\nC"
        refined, explanation = _parse_editor_response(raw)
        assert refined == "A"
        assert "B" in explanation


# ═══════════════════════════════════════════════════════════════════════════
# TEST 5: refine_content integration (with mocked Gemini)
# ═══════════════════════════════════════════════════════════════════════════

class TestRefineContent:
    """End-to-end tests for refine_content with mocked AI."""

    @patch("app.services.agent_service._call_gemini")
    def test_success(self, mock_gemini, app):
        with app.app_context():
            mock_gemini.return_value = (
                "Better content\n---EDITOR_EXPLANATION---\nMade it punchier."
            )
            result = refine_content("Original content", "make it punchier")
            assert result["refined_content"] == "Better content"
            assert result["explanation"] == "Made it punchier."
            mock_gemini.assert_called_once()

    @patch("app.services.agent_service._call_gemini")
    def test_ai_failure_raises_runtime_error(self, mock_gemini, app):
        with app.app_context():
            mock_gemini.side_effect = Exception("API timeout")
            with pytest.raises(RuntimeError, match="couldn't process"):
                refine_content("Content", "fix it")

    @patch("app.services.agent_service._call_gemini")
    def test_brand_context_in_prompt(self, mock_gemini, app):
        with app.app_context():
            mock_gemini.return_value = "Ok\n---EDITOR_EXPLANATION---\nDone"
            refine_content(
                "Hello",
                "fix it",
                brand_context="Brand: SuperCo, Colors: #FF0000",
            )
            prompt = mock_gemini.call_args[0][0]
            assert "SuperCo" in prompt
            assert "#FF0000" in prompt

    @patch("app.services.agent_service._call_gemini")
    def test_persona_context_in_prompt(self, mock_gemini, app):
        with app.app_context():
            mock_gemini.return_value = "Ok\n---EDITOR_EXPLANATION---\nDone"
            refine_content(
                "Hello",
                "fix it",
                persona_context="Persona: Expert Dan, Tone: witty",
            )
            prompt = mock_gemini.call_args[0][0]
            assert "Expert Dan" in prompt
            assert "witty" in prompt

    @patch("app.services.agent_service._call_gemini")
    def test_history_passed_to_prompt(self, mock_gemini, app):
        with app.app_context():
            mock_gemini.return_value = "Ok\n---EDITOR_EXPLANATION---\nDone"
            refine_content(
                "Hello",
                "add CTA",
                history=[{"role": "user", "text": "make shorter"}],
            )
            prompt = mock_gemini.call_args[0][0]
            assert "make shorter" in prompt


# ═══════════════════════════════════════════════════════════════════════════
# TEST 6: Grounded Gemini call
# ═══════════════════════════════════════════════════════════════════════════

class TestGroundedGemini:
    """Verify _call_gemini_grounded sends grounding tools and falls back."""

    @patch("app.services.agent_service.requests.post")
    @patch("app.services.agent_service._get_api_key", return_value="test-key")
    def test_grounded_payload_includes_google_search(self, _key, mock_post, app):
        with app.app_context():
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "candidates": [{
                    "content": {"parts": [{"text": "Grounded answer"}]},
                    "groundingMetadata": {
                        "webSearchQueries": ["test query"],
                        "groundingChunks": [{"web": {"uri": "https://example.com"}}],
                    },
                }]
            }
            mock_post.return_value = mock_resp

            from app.services.agent_service import _call_gemini_grounded
            result = _call_gemini_grounded("What is trending?")

            assert result == "Grounded answer"
            # Verify the payload includes google_search_retrieval
            call_kwargs = mock_post.call_args
            payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
            assert "tools" in payload
            assert any(
                "google_search_retrieval" in t
                for t in payload["tools"]
            )

    @patch("app.services.agent_service._call_gemini")
    @patch("app.services.agent_service.requests.post")
    @patch("app.services.agent_service._get_api_key", return_value="test-key")
    def test_grounded_fallback_on_api_error(self, _key, mock_post, mock_fallback, app):
        with app.app_context():
            # Grounded call returns 400
            mock_resp = MagicMock()
            mock_resp.status_code = 400
            mock_resp.text = "Grounding not available"
            mock_post.return_value = mock_resp

            mock_fallback.return_value = "Fallback answer"

            from app.services.agent_service import _call_gemini_grounded
            result = _call_gemini_grounded("What is trending?")

            assert result == "Fallback answer"
            mock_fallback.assert_called_once()

    @patch("app.services.agent_service.requests.post")
    @patch("app.services.agent_service._get_api_key", return_value="test-key")
    def test_grounded_no_candidates_raises(self, _key, mock_post, app):
        with app.app_context():
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"candidates": []}
            mock_post.return_value = mock_resp

            from app.services.agent_service import _call_gemini_grounded
            with pytest.raises(RuntimeError, match="No candidates"):
                _call_gemini_grounded("What is trending?")


# ═══════════════════════════════════════════════════════════════════════════
# TEST 7: News Digest uses grounded search
# ═══════════════════════════════════════════════════════════════════════════

class TestNewsDigestGrounding:
    """Verify News Digest recipe calls _call_gemini_grounded for research."""

    def test_news_digest_has_grounded_method(self, app):
        with app.app_context():
            from app.recipes.news_digest import NewsDigest
            assert hasattr(NewsDigest, "_call_gemini_grounded")

    @patch("app.recipes.news_digest.NewsDigest._call_gemini_grounded")
    @patch("app.recipes.news_digest.NewsDigest._call_gemini")
    def test_research_step_uses_grounded(self, mock_std, mock_grounded, app):
        """The research step should call _call_gemini_grounded, not _call_gemini."""
        with app.app_context():
            mock_grounded.return_value = "## Story 1\nSomething happened."
            mock_std.return_value = "## Digest\nHere is your digest."

            from app.recipes.news_digest import NewsDigest
            recipe = NewsDigest()
            progress_calls = []

            result = recipe.execute(
                inputs={"topics": "AI, Tech"},
                run_id=999,
                user_id=1,
                on_progress=lambda s, l: progress_calls.append(l),
            )

            # Research should use grounded call
            mock_grounded.assert_called_once()
            # The prompt should contain the topics
            prompt = mock_grounded.call_args[0][0]
            assert "AI" in prompt


# ═══════════════════════════════════════════════════════════════════════════
# TEST 8: /api/recipes/chat route
# ═══════════════════════════════════════════════════════════════════════════

class TestEditorChatRoute:
    """Verify the /api/recipes/chat endpoint."""

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    def test_missing_content_400(self, client):
        resp = client.post(
            "/api/recipes/chat",
            data=json.dumps({"instruction": "fix it"}),
            content_type="application/json",
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert "empty" in data["message"].lower()

    def test_missing_instruction_400(self, client):
        resp = client.post(
            "/api/recipes/chat",
            data=json.dumps({"content": "Hello world"}),
            content_type="application/json",
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert "instruction" in data["message"].lower()

    @patch("app.services.editor_service.refine_content")
    def test_success_200(self, mock_refine, client):
        mock_refine.return_value = {
            "refined_content": "Better text",
            "explanation": "Made it punchier.",
        }
        resp = client.post(
            "/api/recipes/chat",
            data=json.dumps({
                "content": "Original text",
                "instruction": "make it punchier",
            }),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"
        assert data["refined_content"] == "Better text"
        assert data["explanation"] == "Made it punchier."

    @patch("app.services.editor_service.refine_content")
    def test_value_error_400(self, mock_refine, client):
        mock_refine.side_effect = ValueError("Content too long")
        resp = client.post(
            "/api/recipes/chat",
            data=json.dumps({
                "content": "x" * 100,
                "instruction": "fix it",
            }),
            content_type="application/json",
        )
        assert resp.status_code == 400

    @patch("app.services.editor_service.refine_content")
    def test_runtime_error_502(self, mock_refine, client):
        mock_refine.side_effect = RuntimeError("AI unavailable")
        resp = client.post(
            "/api/recipes/chat",
            data=json.dumps({
                "content": "Hello",
                "instruction": "fix it",
            }),
            content_type="application/json",
        )
        assert resp.status_code == 502

    @patch("app.services.editor_service.refine_content")
    def test_unexpected_error_500(self, mock_refine, client):
        mock_refine.side_effect = Exception("something broke")
        resp = client.post(
            "/api/recipes/chat",
            data=json.dumps({
                "content": "Hello",
                "instruction": "fix it",
            }),
            content_type="application/json",
        )
        assert resp.status_code == 500

    def test_no_json_body_400(self, client):
        resp = client.post(
            "/api/recipes/chat",
            data="not json",
            content_type="text/plain",
        )
        assert resp.status_code == 400
