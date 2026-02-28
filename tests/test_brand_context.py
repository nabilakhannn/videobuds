"""Tests for enriched brand/persona context and creative directives.

Phase 37 — Brand Guideline System Prompt Enhancement.
Verifies that build_brand_context, build_persona_context, and
build_creative_directives produce the expected output for all fields.
"""

import json
import pytest
from types import SimpleNamespace

from app.recipes.base import BaseRecipe


# ---------------------------------------------------------------------------
# Fixtures — brand and persona stubs
# ---------------------------------------------------------------------------

def _make_brand(**overrides):
    """Create a SimpleNamespace brand stub with all fields."""
    defaults = {
        "id": 1,
        "name": "TestBrand",
        "tagline": "Just test it",
        "target_audience": "Gen Z tech enthusiasts",
        "visual_style": "Bold, minimal, neon accents",
        "content_pillars": json.dumps(["Innovation", "Community", "Design"]),
        "never_do": "Never use Comic Sans or clip art",
        "brand_doc": "Full brand guide content here..." * 20,  # ~600 chars
        "colors_json": json.dumps(["#FF5500", "#1A1A2E", "#FFFFFF", "#00D4AA"]),
        "voice_json": json.dumps({
            "tone": "confident and playful",
            "personality": "tech-savvy friend",
            "formality": "casual but smart",
        }),
        "hashtags": json.dumps(["#TestBrand", "#InnovateFast", "#DesignFirst"]),
        "caption_template": "Hook → Value → CTA → {hashtags}",
        "logo_path": "/static/uploads/logo_test.png",
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_persona(**overrides):
    """Create a SimpleNamespace persona stub with all fields."""
    defaults = {
        "id": 1,
        "name": "TechTom",
        "bio": "Senior software engineer and tech content creator with 10 years of experience.",
        "tone": "enthusiastic, knowledgeable",
        "voice_style": "Conversational explainer",
        "target_audience": "Junior developers",
        "industry": "Software Engineering",
        "writing_guidelines": "Use short paragraphs. Include code examples.",
        "sample_phrases": ["Let me break this down", "Here's the thing", "Pro tip"],
        "brand_keywords": ["scalable", "production-ready", "best practice"],
        "avoid_words": ["simply", "obviously", "just"],
        "ai_prompt_summary": "Speaks like a senior dev mentoring a junior — warm, clear, practical.",
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# ===========================================================================
# build_brand_context tests
# ===========================================================================

class TestBuildBrandContext:
    """Tests for the enriched build_brand_context method."""

    def test_returns_empty_for_none(self):
        assert BaseRecipe.build_brand_context(None) == ""

    def test_contains_brand_name(self):
        ctx = BaseRecipe.build_brand_context(_make_brand())
        assert "TestBrand" in ctx

    def test_contains_tagline(self):
        ctx = BaseRecipe.build_brand_context(_make_brand())
        assert "Just test it" in ctx

    def test_contains_target_audience(self):
        ctx = BaseRecipe.build_brand_context(_make_brand())
        assert "Gen Z tech enthusiasts" in ctx

    def test_contains_visual_style(self):
        ctx = BaseRecipe.build_brand_context(_make_brand())
        assert "Bold, minimal, neon accents" in ctx

    def test_contains_content_pillars(self):
        ctx = BaseRecipe.build_brand_context(_make_brand())
        assert "Innovation" in ctx
        assert "Community" in ctx
        assert "Design" in ctx

    def test_contains_never_do(self):
        ctx = BaseRecipe.build_brand_context(_make_brand())
        assert "Comic Sans" in ctx

    def test_contains_brand_doc_preview(self):
        ctx = BaseRecipe.build_brand_context(_make_brand())
        assert "Full brand guide content" in ctx

    # ── NEW fields ──

    def test_contains_colour_palette(self):
        ctx = BaseRecipe.build_brand_context(_make_brand())
        assert "#FF5500" in ctx
        assert "#1A1A2E" in ctx
        assert "Primary" in ctx
        assert "Secondary" in ctx

    def test_contains_colour_enforcement_instruction(self):
        ctx = BaseRecipe.build_brand_context(_make_brand())
        assert "Never replace" in ctx
        assert "brand colours" in ctx

    def test_contains_voice_json(self):
        ctx = BaseRecipe.build_brand_context(_make_brand())
        assert "confident and playful" in ctx
        assert "tech-savvy friend" in ctx

    def test_contains_hashtags(self):
        ctx = BaseRecipe.build_brand_context(_make_brand())
        assert "#TestBrand" in ctx
        assert "#InnovateFast" in ctx

    def test_contains_caption_template(self):
        ctx = BaseRecipe.build_brand_context(_make_brand())
        assert "Hook → Value → CTA" in ctx

    def test_contains_logo_reference(self):
        ctx = BaseRecipe.build_brand_context(_make_brand())
        assert "logo" in ctx.lower()

    def test_skips_empty_colors(self):
        ctx = BaseRecipe.build_brand_context(_make_brand(colors_json="[]"))
        assert "Primary" not in ctx

    def test_skips_null_colors(self):
        ctx = BaseRecipe.build_brand_context(_make_brand(colors_json=None))
        assert "Primary" not in ctx

    def test_skips_empty_voice(self):
        ctx = BaseRecipe.build_brand_context(_make_brand(voice_json="{}"))
        assert "Brand Voice" not in ctx

    def test_skips_null_voice(self):
        ctx = BaseRecipe.build_brand_context(_make_brand(voice_json=None))
        assert "Brand Voice" not in ctx

    def test_skips_empty_hashtags(self):
        ctx = BaseRecipe.build_brand_context(_make_brand(hashtags="[]"))
        assert "Hashtag" not in ctx

    def test_skips_null_hashtags(self):
        ctx = BaseRecipe.build_brand_context(_make_brand(hashtags=None))
        assert "Hashtag" not in ctx

    def test_skips_empty_caption_template(self):
        ctx = BaseRecipe.build_brand_context(_make_brand(caption_template=""))
        assert "Caption Template" not in ctx

    def test_skips_null_logo(self):
        ctx = BaseRecipe.build_brand_context(_make_brand(logo_path=None))
        assert "Logo:" not in ctx

    def test_brand_doc_truncated_at_800(self):
        long_doc = "A" * 1000
        ctx = BaseRecipe.build_brand_context(_make_brand(brand_doc=long_doc))
        # Should have exactly 800 A's plus ellipsis
        assert "A" * 800 in ctx
        assert "…" in ctx

    def test_handles_malformed_colors_json(self):
        """Gracefully handles corrupted JSON in colors_json."""
        ctx = BaseRecipe.build_brand_context(_make_brand(colors_json="not json"))
        # Should not crash — just skip the colour section
        assert "TestBrand" in ctx

    def test_handles_malformed_voice_json(self):
        ctx = BaseRecipe.build_brand_context(_make_brand(voice_json="broken"))
        assert "TestBrand" in ctx

    def test_handles_malformed_hashtags(self):
        ctx = BaseRecipe.build_brand_context(_make_brand(hashtags="{bad}"))
        assert "TestBrand" in ctx

    def test_context_has_delimiters(self):
        ctx = BaseRecipe.build_brand_context(_make_brand())
        assert "═══ BRAND CONTEXT ═══" in ctx
        assert "═══ END BRAND CONTEXT ═══" in ctx

    def test_five_colour_labels(self):
        """All 5 labels appear when 5 colours are provided."""
        five = json.dumps(["#A", "#B", "#C", "#D", "#E"])
        ctx = BaseRecipe.build_brand_context(_make_brand(colors_json=five))
        assert "Primary" in ctx
        assert "Secondary" in ctx
        assert "Tertiary" in ctx
        assert "Accent 1" in ctx
        assert "Accent 2" in ctx

    def test_minimal_brand(self):
        """Brand with only name — still produces a valid block."""
        b = SimpleNamespace(
            name="MinBrand", tagline=None, target_audience=None,
            visual_style=None, content_pillars=None, never_do=None,
            brand_doc=None, colors_json=None, voice_json=None,
            hashtags=None, caption_template=None, logo_path=None,
        )
        ctx = BaseRecipe.build_brand_context(b)
        assert "MinBrand" in ctx
        assert "═══ BRAND CONTEXT ═══" in ctx


# ===========================================================================
# build_persona_context tests
# ===========================================================================

class TestBuildPersonaContext:
    """Tests for the enriched build_persona_context method."""

    def test_returns_empty_for_none(self):
        assert BaseRecipe.build_persona_context(None) == ""

    def test_contains_name(self):
        ctx = BaseRecipe.build_persona_context(_make_persona())
        assert "TechTom" in ctx

    def test_contains_bio(self):
        ctx = BaseRecipe.build_persona_context(_make_persona())
        assert "Senior software engineer" in ctx

    def test_contains_tone(self):
        ctx = BaseRecipe.build_persona_context(_make_persona())
        assert "enthusiastic, knowledgeable" in ctx

    def test_contains_voice_style(self):
        ctx = BaseRecipe.build_persona_context(_make_persona())
        assert "Conversational explainer" in ctx

    def test_contains_target_audience(self):
        ctx = BaseRecipe.build_persona_context(_make_persona())
        assert "Junior developers" in ctx

    def test_contains_industry(self):
        ctx = BaseRecipe.build_persona_context(_make_persona())
        assert "Software Engineering" in ctx

    def test_contains_writing_guidelines(self):
        ctx = BaseRecipe.build_persona_context(_make_persona())
        assert "short paragraphs" in ctx

    def test_contains_sample_phrases(self):
        ctx = BaseRecipe.build_persona_context(_make_persona())
        assert "Let me break this down" in ctx

    def test_contains_brand_keywords(self):
        ctx = BaseRecipe.build_persona_context(_make_persona())
        assert "scalable" in ctx

    def test_contains_avoid_words(self):
        ctx = BaseRecipe.build_persona_context(_make_persona())
        assert "simply" in ctx

    def test_contains_ai_prompt_summary(self):
        ctx = BaseRecipe.build_persona_context(_make_persona())
        assert "senior dev mentoring" in ctx

    def test_contains_voice_enforcement_instruction(self):
        ctx = BaseRecipe.build_persona_context(_make_persona())
        assert "IMPORTANT" in ctx
        assert "tone and style" in ctx

    def test_skips_empty_bio(self):
        ctx = BaseRecipe.build_persona_context(_make_persona(bio=""))
        assert "Bio" not in ctx

    def test_skips_null_bio(self):
        ctx = BaseRecipe.build_persona_context(_make_persona(bio=None))
        assert "Bio" not in ctx

    def test_context_has_delimiters(self):
        ctx = BaseRecipe.build_persona_context(_make_persona())
        assert "═══ PERSONA / VOICE CONTEXT ═══" in ctx
        assert "═══ END PERSONA CONTEXT ═══" in ctx

    def test_minimal_persona(self):
        """Persona with only name — still produces a valid block."""
        p = SimpleNamespace(
            name="MinPerson", bio=None, tone=None, voice_style=None,
            target_audience=None, industry=None, writing_guidelines=None,
            sample_phrases=None, brand_keywords=None, avoid_words=None,
            ai_prompt_summary=None,
        )
        ctx = BaseRecipe.build_persona_context(p)
        assert "MinPerson" in ctx
        assert "IMPORTANT" in ctx


# ===========================================================================
# build_creative_directives tests
# ===========================================================================

class TestBuildCreativeDirectives:
    """Tests for the build_creative_directives method."""

    def test_image_directives(self):
        d = BaseRecipe.build_creative_directives(generation_type="image")
        assert "BRAND FIDELITY" in d
        assert "DIVERSITY" in d
        assert "PROMPT RULES" in d
        assert "IMAGE QUALITY" in d
        assert "VIDEO QUALITY" not in d

    def test_video_directives(self):
        d = BaseRecipe.build_creative_directives(generation_type="video")
        assert "BRAND FIDELITY" in d
        assert "VIDEO QUALITY" in d
        assert "IMAGE QUALITY" not in d

    def test_text_directives_no_image_video(self):
        d = BaseRecipe.build_creative_directives(generation_type="text")
        assert "BRAND FIDELITY" in d
        assert "IMAGE QUALITY" not in d
        assert "VIDEO QUALITY" not in d

    def test_ugc_directives_present_when_requested(self):
        d = BaseRecipe.build_creative_directives(
            generation_type="image", style_hint="ugc"
        )
        assert "UGC AUTHENTICITY" in d
        assert "amateur iPhone" in d

    def test_ugc_directives_absent_by_default(self):
        d = BaseRecipe.build_creative_directives(generation_type="image")
        assert "UGC AUTHENTICITY" not in d

    def test_no_double_quotes_rule(self):
        d = BaseRecipe.build_creative_directives(generation_type="image")
        assert "double quotes" in d.lower()

    def test_product_fidelity_rule(self):
        d = BaseRecipe.build_creative_directives(generation_type="image")
        assert "NEVER alter" in d

    def test_diversity_rule(self):
        d = BaseRecipe.build_creative_directives(generation_type="image")
        assert "diversity" in d.lower()
        assert "21–38" in d or "21-38" in d

    def test_camera_movement_in_video(self):
        d = BaseRecipe.build_creative_directives(generation_type="video")
        assert "camera movement" in d.lower()

    def test_dialogue_rules_in_video(self):
        d = BaseRecipe.build_creative_directives(generation_type="video")
        assert "dialogue" in d.lower()

    def test_has_delimiters(self):
        d = BaseRecipe.build_creative_directives(generation_type="image")
        assert "═══ CREATIVE QUALITY DIRECTIVES ═══" in d
        assert "═══ END CREATIVE DIRECTIVES ═══" in d

    def test_brand_colour_enforcement(self):
        d = BaseRecipe.build_creative_directives(generation_type="image")
        assert "brand colours" in d.lower() or "brand colors" in d.lower()

    def test_ad_copy_brevity_rule(self):
        d = BaseRecipe.build_creative_directives(generation_type="image")
        assert "max 7 words" in d


# ===========================================================================
# Integration tests — verify enriched context flows into recipes
# ===========================================================================

class TestRecipeIntegration:
    """Verify that recipes correctly use the enriched context."""

    def test_image_creator_includes_creative_directives_in_prompt(self):
        """Image creator's _build_assisted_prompt includes creative directives."""
        from app.recipes.image_creator import ImageCreator
        recipe = ImageCreator()
        # Use a mock that captures the prompt sent to Gemini
        captured = []

        def mock_gemini(prompt):
            captured.append(prompt)
            return "A beautiful product shot with warm golden lighting"

        recipe._call_gemini = mock_gemini

        style = {"prompt_fragment": "", "label": "None"}
        platform = {"hint": "", "label": "None"}

        recipe._build_assisted_prompt(
            user_description="Product shot of coffee",
            style=style,
            platform=platform,
            negative_prompt="",
            reference_analysis="",
            brand_ctx="═══ BRAND CONTEXT ═══\nBrand: CoffeeCo\n═══ END ═══",
            persona_ctx="",
            aspect_ratio="1:1",
        )

        assert len(captured) == 1
        prompt = captured[0]
        assert "CREATIVE QUALITY DIRECTIVES" in prompt
        assert "NEVER alter" in prompt
        assert "double quotes" in prompt.lower()

    def test_video_creator_includes_creative_directives_in_prompt(self):
        """Video creator's _build_assisted_prompt includes creative directives."""
        from app.recipes.video_creator import VideoCreator
        recipe = VideoCreator()
        captured = []

        def mock_gemini(prompt):
            captured.append(prompt)
            return "Slow dolly push-in on coffee cup with steam rising"

        recipe._call_gemini = mock_gemini

        style = {"prompt_fragment": "", "label": "None"}
        platform = {"hint": "", "label": "None"}

        recipe._build_assisted_prompt(
            user_description="Coffee reveal video",
            style=style,
            platform=platform,
            reference_analysis="",
            brand_ctx="═══ BRAND CONTEXT ═══\nBrand: CoffeeCo\n═══ END ═══",
            persona_ctx="",
            aspect_ratio="9:16",
            duration="5",
            has_image=False,
        )

        assert len(captured) == 1
        prompt = captured[0]
        assert "CREATIVE QUALITY DIRECTIVES" in prompt
        assert "camera movement" in prompt.lower()
        assert "NEVER alter" in prompt

    def test_ugc_style_triggers_ugc_directives(self):
        """When UGC style is selected, UGC directives are included."""
        from app.recipes.image_creator import ImageCreator
        recipe = ImageCreator()
        captured = []

        def mock_gemini(prompt):
            captured.append(prompt)
            return "Casual iPhone selfie with product"

        recipe._call_gemini = mock_gemini

        style = {"prompt_fragment": "UGC style", "label": "UGC / Authentic"}
        platform = {"hint": "", "label": "None"}

        recipe._build_assisted_prompt(
            user_description="UGC product shot",
            style=style,
            platform=platform,
            negative_prompt="",
            reference_analysis="",
            brand_ctx="",
            persona_ctx="",
            aspect_ratio="9:16",
        )

        assert len(captured) == 1
        assert "UGC AUTHENTICITY" in captured[0]
        assert "amateur iPhone" in captured[0]

    def test_non_ugc_style_excludes_ugc_directives(self):
        """Non-UGC styles don't include UGC directives."""
        from app.recipes.image_creator import ImageCreator
        recipe = ImageCreator()
        captured = []

        def mock_gemini(prompt):
            captured.append(prompt)
            return "Cinematic product reveal"

        recipe._call_gemini = mock_gemini

        style = {"prompt_fragment": "Cinematic", "label": "Cinematic / Epic"}
        platform = {"hint": "", "label": "None"}

        recipe._build_assisted_prompt(
            user_description="Cinematic product shot",
            style=style,
            platform=platform,
            negative_prompt="",
            reference_analysis="",
            brand_ctx="",
            persona_ctx="",
            aspect_ratio="16:9",
        )

        assert len(captured) == 1
        assert "UGC AUTHENTICITY" not in captured[0]
