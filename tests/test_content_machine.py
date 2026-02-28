"""Unit tests for AI Content Machine recipe — Phase 34D.

Tests cover:
  1. Recipe metadata & registration
  2. Input field definitions
  3. Input validation
  4. Hook analysis prompt construction
  5. Psychology analysis prompt construction
  6. Strategy generation
  7. Template generation
  8. Analysis modes (full, hooks_only, strategy_only)
  9. Brand & persona context injection
 10. Error handling & resilience
 11. Summary card contents
 12. Progress reporting
 13. Constants data integrity
"""

import pytest
from unittest.mock import patch, MagicMock


# ── Helpers ──────────────────────────────────────────────────────────────

def _make_recipe():
    from app.recipes.content_machine import ContentMachine
    return ContentMachine()


def _base_inputs(**overrides):
    """Return minimal valid inputs dict."""
    base = {
        "competitor_content": (
            "Stop scrolling. This one trick changed my morning routine.\n"
            "https://www.instagram.com/p/ABC123/\n"
            "Why nobody is talking about this skincare hack"
        ),
        "analysis_mode": "full",
        "target_platform": "all",
    }
    base.update(overrides)
    return base


_MOCK_HOOK_RESPONSE = (
    "## Hook Analysis\n\n"
    "### Hook 1: Curiosity Gap\n"
    "**Content:** \"Stop scrolling. This one trick changed my morning routine.\"\n"
    "**Type:** Curiosity gap + command hook\n"
    "**Power:** 8/10\n\n"
    "### Hook Formula Cheat Sheet\n"
    "- [Action verb]. This [number] [noun] changed my [aspect]."
)

_MOCK_PSYCH_RESPONSE = (
    "## Emotional Triggers\n\n"
    "- **Curiosity** — desire to know the trick\n"
    "- **FOMO** — fear of missing a life hack\n\n"
    "## Pain Points\n"
    "- Inefficient morning routines\n"
    "- Overwhelm from too much skincare info"
)

_MOCK_STRATEGY_RESPONSE = (
    "## Content Pillars\n\n"
    "1. Morning routine hacks\n"
    "2. Skincare myths debunked\n\n"
    "## 30-Day Quick-Start Plan\n"
    "Week 1: Post daily hooks"
)

_MOCK_TEMPLATE_RESPONSE = (
    "**Template #1: Curiosity Gap Hook**\n"
    "🎯 When to use: Opening a carousel\n"
    "📝 Template:\n"
    "```\nStop scrolling. This [NUMBER] [THING] changed my [ASPECT].\n```\n"
    "💡 Example: Stop scrolling. This 3-step routine changed my skin."
)


def _gemini_router(prompt):
    """Route Gemini calls to appropriate mock responses.

    Uses unique phrases from each analysis method's system prompt
    to disambiguate calls.
    """
    prompt_lower = prompt.lower()
    # Order matters — check most specific first
    if "content creator generating ready-to-use" in prompt_lower:
        return _MOCK_TEMPLATE_RESPONSE
    elif "consumer psychologist" in prompt_lower:
        return _MOCK_PSYCH_RESPONSE
    elif "senior content strategist" in prompt_lower:
        return _MOCK_STRATEGY_RESPONSE
    elif "attention engineering" in prompt_lower:
        return _MOCK_HOOK_RESPONSE
    return "Generic analysis response."


# ══════════════════════════════════════════════════════════════════════════
# 1. Recipe metadata & registration
# ══════════════════════════════════════════════════════════════════════════

class TestRecipeMetadata:
    def test_slug(self):
        r = _make_recipe()
        assert r.slug == "content-machine"

    def test_name(self):
        r = _make_recipe()
        assert r.name == "AI Content Machine"

    def test_category(self):
        r = _make_recipe()
        assert r.category == "research"

    def test_is_active(self):
        r = _make_recipe()
        assert r.is_active is True

    def test_icon(self):
        r = _make_recipe()
        assert r.icon == "🧠"

    def test_cost_is_free(self):
        r = _make_recipe()
        assert "0.00" in r.estimated_cost or "Free" in r.estimated_cost

    def test_registered_in_global_registry(self):
        from app.recipes import get_recipe
        r = get_recipe("content-machine")
        assert r is not None
        assert r.is_active is True

    def test_how_to_use_mentions_hooks(self):
        r = _make_recipe()
        assert "Hook" in r.how_to_use

    def test_how_to_use_mentions_psychology(self):
        r = _make_recipe()
        assert "Psycholog" in r.how_to_use or "psychology" in r.how_to_use.lower()

    def test_how_to_use_mentions_templates(self):
        r = _make_recipe()
        assert "template" in r.how_to_use.lower()


# ══════════════════════════════════════════════════════════════════════════
# 2. Input field definitions
# ══════════════════════════════════════════════════════════════════════════

class TestInputFields:
    def test_field_count(self):
        r = _make_recipe()
        fields = r.get_input_fields()
        assert len(fields) == 5

    def test_field_names(self):
        r = _make_recipe()
        names = [f.name for f in r.get_input_fields()]
        expected = [
            "competitor_content", "audience_comments",
            "analysis_mode", "target_platform", "industry_context",
        ]
        assert names == expected

    def test_competitor_content_required(self):
        r = _make_recipe()
        fields = {f.name: f for f in r.get_input_fields()}
        assert fields["competitor_content"].required is True

    def test_audience_comments_optional(self):
        r = _make_recipe()
        fields = {f.name: f for f in r.get_input_fields()}
        assert fields["audience_comments"].required is False

    def test_industry_context_optional(self):
        r = _make_recipe()
        fields = {f.name: f for f in r.get_input_fields()}
        assert fields["industry_context"].required is False

    def test_analysis_mode_options(self):
        r = _make_recipe()
        fields = {f.name: f for f in r.get_input_fields()}
        modes = [o["value"] for o in fields["analysis_mode"].options]
        assert "full" in modes
        assert "hooks_only" in modes
        assert "strategy_only" in modes

    def test_platform_options(self):
        r = _make_recipe()
        fields = {f.name: f for f in r.get_input_fields()}
        platforms = [o["value"] for o in fields["target_platform"].options]
        assert "all" in platforms
        assert "instagram" in platforms
        assert "tiktok" in platforms
        assert "youtube" in platforms
        assert "linkedin" in platforms
        assert "x_twitter" in platforms

    def test_steps(self):
        r = _make_recipe()
        steps = r.get_steps()
        assert len(steps) == 5
        assert "Analysing hooks" in steps[1]


# ══════════════════════════════════════════════════════════════════════════
# 3. Input validation
# ══════════════════════════════════════════════════════════════════════════

class TestInputValidation:
    def test_empty_content_raises(self):
        r = _make_recipe()
        with pytest.raises(ValueError, match="required"):
            r.execute(_base_inputs(competitor_content=""), run_id=1, user_id=1)

    def test_whitespace_only_raises(self):
        r = _make_recipe()
        with pytest.raises(ValueError, match="required"):
            r.execute(_base_inputs(competitor_content="   \n  "), run_id=1, user_id=1)

    def test_too_long_content_raises(self):
        r = _make_recipe()
        with pytest.raises(ValueError, match="too long"):
            r.execute(
                _base_inputs(competitor_content="x" * 50_001),
                run_id=1, user_id=1,
            )

    def test_exactly_max_length_does_not_raise(self):
        r = _make_recipe()
        with patch.object(r, "_call_gemini", side_effect=_gemini_router):
            result = r.execute(
                _base_inputs(competitor_content="x" * 50_000),
                run_id=1, user_id=1,
            )
        assert result["cost"] == 0.0

    def test_invalid_mode_falls_back(self):
        r = _make_recipe()
        with patch.object(r, "_call_gemini", side_effect=_gemini_router):
            result = r.execute(
                _base_inputs(analysis_mode="nonexistent"),
                run_id=1, user_id=1,
            )
        # Falls back to "full" — should have all 4 analysis outputs + summary
        assert len(result["outputs"]) >= 5

    def test_invalid_platform_falls_back(self):
        r = _make_recipe()
        with patch.object(r, "_call_gemini", side_effect=_gemini_router):
            result = r.execute(
                _base_inputs(target_platform="nonexistent"),
                run_id=1, user_id=1,
            )
        # Falls back to "all"
        summary = result["outputs"][0]
        assert "All Platforms" in summary["value"]


# ══════════════════════════════════════════════════════════════════════════
# 4. Hook analysis
# ══════════════════════════════════════════════════════════════════════════

class TestHookAnalysis:
    def test_hook_output_present_in_full_mode(self):
        r = _make_recipe()
        with patch.object(r, "_call_gemini", side_effect=_gemini_router):
            result = r.execute(_base_inputs(), run_id=1, user_id=1)
        hook_outputs = [
            o for o in result["outputs"]
            if "Hook" in o.get("title", "")
        ]
        assert len(hook_outputs) == 1
        assert "Curiosity Gap" in hook_outputs[0]["value"]

    def test_hook_prompt_includes_content(self):
        r = _make_recipe()
        captured = []

        def capture(prompt):
            captured.append(prompt)
            return _MOCK_HOOK_RESPONSE

        with patch.object(r, "_call_gemini", side_effect=capture):
            r.execute(
                _base_inputs(competitor_content="Test hook content here"),
                run_id=1, user_id=1,
            )
        # First call should be hook analysis
        assert "Test hook content here" in captured[0]

    def test_hook_prompt_includes_platform(self):
        r = _make_recipe()
        captured = []

        def capture(prompt):
            captured.append(prompt)
            return _MOCK_HOOK_RESPONSE

        with patch.object(r, "_call_gemini", side_effect=capture):
            r.execute(
                _base_inputs(target_platform="tiktok"),
                run_id=1, user_id=1,
            )
        assert "TikTok" in captured[0]

    def test_hook_prompt_includes_industry(self):
        r = _make_recipe()
        captured = []

        def capture(prompt):
            captured.append(prompt)
            return _MOCK_HOOK_RESPONSE

        with patch.object(r, "_call_gemini", side_effect=capture):
            r.execute(
                _base_inputs(industry_context="DTC skincare"),
                run_id=1, user_id=1,
            )
        assert "DTC skincare" in captured[0]


# ══════════════════════════════════════════════════════════════════════════
# 5. Psychology analysis
# ══════════════════════════════════════════════════════════════════════════

class TestPsychologyAnalysis:
    def test_psych_output_present(self):
        r = _make_recipe()
        with patch.object(r, "_call_gemini", side_effect=_gemini_router):
            result = r.execute(_base_inputs(), run_id=1, user_id=1)
        psych_outputs = [
            o for o in result["outputs"]
            if "Psycholog" in o.get("title", "")
        ]
        assert len(psych_outputs) == 1

    def test_psych_includes_audience_comments(self):
        r = _make_recipe()
        captured = []

        def capture(prompt):
            captured.append(prompt)
            if "psycholog" in prompt.lower() or "emotional" in prompt.lower():
                return _MOCK_PSYCH_RESPONSE
            return _gemini_router(prompt)

        with patch.object(r, "_call_gemini", side_effect=capture):
            r.execute(
                _base_inputs(audience_comments="This changed my life!"),
                run_id=1, user_id=1,
            )
        # Find the psychology prompt
        psych_prompts = [p for p in captured if "emotional" in p.lower()]
        assert len(psych_prompts) >= 1
        assert "This changed my life!" in psych_prompts[0]

    def test_psych_without_comments(self):
        r = _make_recipe()
        with patch.object(r, "_call_gemini", side_effect=_gemini_router):
            result = r.execute(
                _base_inputs(audience_comments=""),
                run_id=1, user_id=1,
            )
        psych_outputs = [
            o for o in result["outputs"]
            if "Psycholog" in o.get("title", "")
        ]
        assert len(psych_outputs) == 1  # Still produces analysis


# ══════════════════════════════════════════════════════════════════════════
# 6. Strategy generation
# ══════════════════════════════════════════════════════════════════════════

class TestStrategyGeneration:
    def test_strategy_output_present(self):
        r = _make_recipe()
        with patch.object(r, "_call_gemini", side_effect=_gemini_router):
            result = r.execute(_base_inputs(), run_id=1, user_id=1)
        strategy_outputs = [
            o for o in result["outputs"]
            if "Strategy" in o.get("title", "")
        ]
        assert len(strategy_outputs) == 1

    def test_strategy_builds_on_prior_analysis(self):
        r = _make_recipe()
        captured = []

        def capture(prompt):
            captured.append(prompt)
            return _gemini_router(prompt)

        with patch.object(r, "_call_gemini", side_effect=capture):
            r.execute(_base_inputs(), run_id=1, user_id=1)

        # Strategy prompt should reference hook analysis
        strategy_prompts = [p for p in captured if "playbook" in p.lower()]
        assert len(strategy_prompts) >= 1
        assert "HOOK ANALYSIS" in strategy_prompts[0]


# ══════════════════════════════════════════════════════════════════════════
# 7. Template generation
# ══════════════════════════════════════════════════════════════════════════

class TestTemplateGeneration:
    def test_template_output_present(self):
        r = _make_recipe()
        with patch.object(r, "_call_gemini", side_effect=_gemini_router):
            result = r.execute(_base_inputs(), run_id=1, user_id=1)
        template_outputs = [
            o for o in result["outputs"]
            if "Template" in o.get("title", "")
        ]
        assert len(template_outputs) == 1


# ══════════════════════════════════════════════════════════════════════════
# 8. Analysis modes
# ══════════════════════════════════════════════════════════════════════════

class TestAnalysisModes:
    def test_full_mode_has_all_sections(self):
        r = _make_recipe()
        with patch.object(r, "_call_gemini", side_effect=_gemini_router):
            result = r.execute(
                _base_inputs(analysis_mode="full"),
                run_id=1, user_id=1,
            )
        titles = [o.get("title", "") for o in result["outputs"]]
        assert any("Hook" in t for t in titles)
        assert any("Psycholog" in t for t in titles)
        assert any("Strategy" in t for t in titles)
        assert any("Template" in t for t in titles)
        # Summary + 4 sections = 5
        assert len(result["outputs"]) == 5

    def test_hooks_only_mode(self):
        r = _make_recipe()
        with patch.object(r, "_call_gemini", return_value=_MOCK_HOOK_RESPONSE):
            result = r.execute(
                _base_inputs(analysis_mode="hooks_only"),
                run_id=1, user_id=1,
            )
        titles = [o.get("title", "") for o in result["outputs"]]
        assert any("Hook" in t for t in titles)
        assert not any("Psycholog" in t for t in titles)
        assert not any("Strategy" in t for t in titles)
        assert not any("Template" in t for t in titles)
        # Summary + 1 section = 2
        assert len(result["outputs"]) == 2

    def test_strategy_only_mode(self):
        r = _make_recipe()
        with patch.object(r, "_call_gemini", side_effect=_gemini_router):
            result = r.execute(
                _base_inputs(analysis_mode="strategy_only"),
                run_id=1, user_id=1,
            )
        titles = [o.get("title", "") for o in result["outputs"]]
        assert not any("Hook" in t and "Formula" in t for t in titles)
        assert not any("Psycholog" in t for t in titles)
        assert any("Strategy" in t for t in titles)
        assert any("Template" in t for t in titles)
        # Summary + 2 sections = 3
        assert len(result["outputs"]) == 3

    def test_gemini_call_count_full_mode(self):
        r = _make_recipe()
        with patch.object(r, "_call_gemini", side_effect=_gemini_router) as mock:
            r.execute(
                _base_inputs(analysis_mode="full"),
                run_id=1, user_id=1,
            )
        # Full mode: hooks + psychology + strategy + templates = 4 calls
        assert mock.call_count == 4

    def test_gemini_call_count_hooks_only(self):
        r = _make_recipe()
        with patch.object(r, "_call_gemini", return_value=_MOCK_HOOK_RESPONSE) as mock:
            r.execute(
                _base_inputs(analysis_mode="hooks_only"),
                run_id=1, user_id=1,
            )
        assert mock.call_count == 1

    def test_gemini_call_count_strategy_only(self):
        r = _make_recipe()
        with patch.object(r, "_call_gemini", side_effect=_gemini_router) as mock:
            r.execute(
                _base_inputs(analysis_mode="strategy_only"),
                run_id=1, user_id=1,
            )
        assert mock.call_count == 2  # strategy + templates


# ══════════════════════════════════════════════════════════════════════════
# 9. Brand & persona context injection
# ══════════════════════════════════════════════════════════════════════════

class TestBrandPersonaInjection:
    def test_brand_context_in_hook_prompt(self):
        r = _make_recipe()
        captured = []

        def capture(prompt):
            captured.append(prompt)
            return _gemini_router(prompt)

        mock_brand = MagicMock()
        mock_brand.name = "GlowSkin"
        mock_brand.tagline = "Radiant skin, naturally"
        mock_brand.target_audience = "Women 25-45"
        mock_brand.visual_style = "Clean and minimal"
        mock_brand.content_pillars = None
        mock_brand.never_do = None
        mock_brand.brand_doc = None

        with patch.object(r, "_call_gemini", side_effect=capture):
            r.execute(
                _base_inputs(), run_id=1, user_id=1,
                brand=mock_brand,
            )
        # Brand should appear in all prompts
        assert any("GlowSkin" in p for p in captured)

    def test_persona_context_in_prompts(self):
        r = _make_recipe()
        captured = []

        def capture(prompt):
            captured.append(prompt)
            return _gemini_router(prompt)

        mock_persona = MagicMock()
        mock_persona.name = "Bold Expert"
        mock_persona.tone = "Authoritative yet approachable"
        mock_persona.expertise = "Skincare science"
        mock_persona.content_themes = "Myth-busting, education"
        mock_persona.writing_style = None
        mock_persona.avoid = None

        with patch.object(r, "_call_gemini", side_effect=capture):
            r.execute(
                _base_inputs(), run_id=1, user_id=1,
                persona=mock_persona,
            )
        assert any("Bold Expert" in p for p in captured)

    def test_brand_in_summary(self):
        r = _make_recipe()
        mock_brand = MagicMock()
        mock_brand.name = "GlowSkin"
        mock_brand.tagline = None
        mock_brand.target_audience = None
        mock_brand.visual_style = None
        mock_brand.content_pillars = None
        mock_brand.never_do = None
        mock_brand.brand_doc = None

        with patch.object(r, "_call_gemini", side_effect=_gemini_router):
            result = r.execute(
                _base_inputs(), run_id=1, user_id=1,
                brand=mock_brand,
            )
        summary = result["outputs"][0]
        assert "GlowSkin" in summary["value"]

    def test_persona_in_summary(self):
        r = _make_recipe()
        mock_persona = MagicMock()
        mock_persona.name = "Bold Expert"

        with patch.object(r, "_call_gemini", side_effect=_gemini_router):
            result = r.execute(
                _base_inputs(), run_id=1, user_id=1,
                persona=mock_persona,
            )
        summary = result["outputs"][0]
        assert "Bold Expert" in summary["value"]


# ══════════════════════════════════════════════════════════════════════════
# 10. Error handling & resilience
# ══════════════════════════════════════════════════════════════════════════

class TestErrorHandling:
    def test_gemini_failure_in_hooks_returns_warning(self):
        r = _make_recipe()

        def fail_hooks(prompt):
            if "attention engineering" in prompt.lower():
                raise RuntimeError("Gemini rate limit")
            return _gemini_router(prompt)

        with patch.object(r, "_call_gemini", side_effect=fail_hooks):
            result = r.execute(_base_inputs(), run_id=1, user_id=1)

        hook_outputs = [
            o for o in result["outputs"]
            if "Hook" in o.get("title", "")
        ]
        assert len(hook_outputs) == 1
        assert "⚠️" in hook_outputs[0]["value"]
        assert result["cost"] == 0.0

    def test_gemini_failure_in_psychology_returns_warning(self):
        r = _make_recipe()

        def fail_psych(prompt):
            if "consumer psychologist" in prompt.lower():
                raise RuntimeError("Gemini down")
            return _gemini_router(prompt)

        with patch.object(r, "_call_gemini", side_effect=fail_psych):
            result = r.execute(_base_inputs(), run_id=1, user_id=1)

        psych_outputs = [
            o for o in result["outputs"]
            if "Psycholog" in o.get("title", "")
        ]
        assert len(psych_outputs) == 1
        assert "⚠️" in psych_outputs[0]["value"]

    def test_gemini_failure_in_strategy_returns_warning(self):
        r = _make_recipe()

        def fail_strategy(prompt):
            if "senior content strategist" in prompt.lower():
                raise RuntimeError("Token limit exceeded")
            return _gemini_router(prompt)

        with patch.object(r, "_call_gemini", side_effect=fail_strategy):
            result = r.execute(_base_inputs(), run_id=1, user_id=1)

        strategy_outputs = [
            o for o in result["outputs"]
            if "Strategy" in o.get("title", "")
        ]
        assert len(strategy_outputs) == 1
        assert "⚠️" in strategy_outputs[0]["value"]

    def test_all_gemini_failures_still_returns_summary(self):
        r = _make_recipe()
        with patch.object(r, "_call_gemini", side_effect=RuntimeError("All down")):
            result = r.execute(_base_inputs(), run_id=1, user_id=1)

        # Should still have summary + 4 warning outputs
        assert len(result["outputs"]) == 5
        assert result["outputs"][0]["title"] == "Analysis Summary"
        assert result["cost"] == 0.0

    def test_cost_always_zero(self):
        r = _make_recipe()
        with patch.object(r, "_call_gemini", side_effect=_gemini_router):
            result = r.execute(_base_inputs(), run_id=1, user_id=1)
        assert result["cost"] == 0.0


# ══════════════════════════════════════════════════════════════════════════
# 11. Summary card contents
# ══════════════════════════════════════════════════════════════════════════

class TestSummaryCard:
    def test_summary_is_first_output(self):
        r = _make_recipe()
        with patch.object(r, "_call_gemini", side_effect=_gemini_router):
            result = r.execute(_base_inputs(), run_id=1, user_id=1)
        assert result["outputs"][0]["title"] == "Analysis Summary"

    def test_summary_contains_item_count(self):
        r = _make_recipe()
        with patch.object(r, "_call_gemini", side_effect=_gemini_router):
            result = r.execute(_base_inputs(), run_id=1, user_id=1)
        summary = result["outputs"][0]["value"]
        assert "Items Analysed" in summary
        assert "3" in summary  # 3 items in base inputs

    def test_summary_contains_mode(self):
        r = _make_recipe()
        with patch.object(r, "_call_gemini", side_effect=_gemini_router):
            result = r.execute(_base_inputs(), run_id=1, user_id=1)
        summary = result["outputs"][0]["value"]
        assert "Full Analysis" in summary

    def test_summary_contains_platform(self):
        r = _make_recipe()
        with patch.object(r, "_call_gemini", side_effect=_gemini_router):
            result = r.execute(
                _base_inputs(target_platform="tiktok"),
                run_id=1, user_id=1,
            )
        summary = result["outputs"][0]["value"]
        assert "TikTok" in summary

    def test_summary_contains_industry(self):
        r = _make_recipe()
        with patch.object(r, "_call_gemini", side_effect=_gemini_router):
            result = r.execute(
                _base_inputs(industry_context="DTC skincare"),
                run_id=1, user_id=1,
            )
        summary = result["outputs"][0]["value"]
        assert "DTC skincare" in summary

    def test_summary_contains_comment_count(self):
        r = _make_recipe()
        with patch.object(r, "_call_gemini", side_effect=_gemini_router):
            result = r.execute(
                _base_inputs(audience_comments="Comment 1\nComment 2\nComment 3"),
                run_id=1, user_id=1,
            )
        summary = result["outputs"][0]["value"]
        assert "Audience Comments" in summary
        assert "3" in summary

    def test_summary_contains_sections_count(self):
        r = _make_recipe()
        with patch.object(r, "_call_gemini", side_effect=_gemini_router):
            result = r.execute(_base_inputs(), run_id=1, user_id=1)
        summary = result["outputs"][0]["value"]
        assert "Sections Generated" in summary
        assert "4" in summary  # hooks + psych + strategy + templates


# ══════════════════════════════════════════════════════════════════════════
# 12. Progress reporting
# ══════════════════════════════════════════════════════════════════════════

class TestProgressReporting:
    def test_progress_callbacks_full_mode(self):
        r = _make_recipe()
        progress_calls = []

        def capture(step, label):
            progress_calls.append((step, label))

        with patch.object(r, "_call_gemini", side_effect=_gemini_router):
            r.execute(
                _base_inputs(), run_id=1, user_id=1,
                on_progress=capture,
            )

        steps = [p[0] for p in progress_calls]
        assert 0 in steps  # Parsing
        assert 1 in steps  # Hooks
        assert 2 in steps  # Psychology
        assert 3 in steps  # Strategy
        assert 4 in steps  # Templates

    def test_progress_mentions_item_count(self):
        r = _make_recipe()
        labels = []

        def capture(step, label):
            labels.append(label)

        with patch.object(r, "_call_gemini", side_effect=_gemini_router):
            r.execute(
                _base_inputs(), run_id=1, user_id=1,
                on_progress=capture,
            )

        hook_labels = [l for l in labels if "3" in l and "item" in l.lower()]
        assert len(hook_labels) >= 1

    def test_progress_hooks_only_mode(self):
        r = _make_recipe()
        progress_calls = []

        def capture(step, label):
            progress_calls.append((step, label))

        with patch.object(r, "_call_gemini", return_value=_MOCK_HOOK_RESPONSE):
            r.execute(
                _base_inputs(analysis_mode="hooks_only"),
                run_id=1, user_id=1,
                on_progress=capture,
            )

        steps = [p[0] for p in progress_calls]
        assert 0 in steps
        assert 1 in steps
        assert 2 not in steps  # Psychology skipped
        assert 3 not in steps  # Strategy skipped


# ══════════════════════════════════════════════════════════════════════════
# 13. Constants data integrity
# ══════════════════════════════════════════════════════════════════════════

class TestConstants:
    def test_analysis_modes_have_required_keys(self):
        from app.recipes.content_machine import _ANALYSIS_MODES
        for key, mode in _ANALYSIS_MODES.items():
            assert "label" in mode, f"Mode '{key}' missing 'label'"
            assert "steps" in mode, f"Mode '{key}' missing 'steps'"
            assert isinstance(mode["steps"], list)

    def test_platform_targets_are_strings(self):
        from app.recipes.content_machine import _PLATFORM_TARGETS
        for key, label in _PLATFORM_TARGETS.items():
            assert isinstance(label, str)
            assert len(label) > 0

    def test_full_mode_has_all_steps(self):
        from app.recipes.content_machine import _ANALYSIS_MODES
        full = _ANALYSIS_MODES["full"]
        assert "hooks" in full["steps"]
        assert "psychology" in full["steps"]
        assert "strategy" in full["steps"]
        assert "templates" in full["steps"]

    def test_hooks_only_has_just_hooks(self):
        from app.recipes.content_machine import _ANALYSIS_MODES
        hooks = _ANALYSIS_MODES["hooks_only"]
        assert hooks["steps"] == ["hooks"]

    def test_strategy_only_has_strategy_and_templates(self):
        from app.recipes.content_machine import _ANALYSIS_MODES
        strat = _ANALYSIS_MODES["strategy_only"]
        assert "strategy" in strat["steps"]
        assert "templates" in strat["steps"]
        assert "hooks" not in strat["steps"]


# ══════════════════════════════════════════════════════════════════════════
# 14. Content item parsing
# ══════════════════════════════════════════════════════════════════════════

class TestContentParsing:
    def test_newlines_split_into_items(self):
        r = _make_recipe()
        with patch.object(r, "_call_gemini", side_effect=_gemini_router):
            result = r.execute(
                _base_inputs(competitor_content="Item 1\nItem 2\n\nItem 3"),
                run_id=1, user_id=1,
            )
        summary = result["outputs"][0]["value"]
        assert "3" in summary  # 3 items (blank line filtered)

    def test_single_item(self):
        r = _make_recipe()
        with patch.object(r, "_call_gemini", side_effect=_gemini_router):
            result = r.execute(
                _base_inputs(competitor_content="Just one hook here"),
                run_id=1, user_id=1,
            )
        summary = result["outputs"][0]["value"]
        assert "1" in summary
