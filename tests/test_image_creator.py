"""Unit tests for the enhanced Image Creator recipe.

Tests cover all 6 enhancements:
  A. AI Prompt Assistant (assisted mode, Gemini crafts prompt)
  B. Reference Image Upload (vision analysis)
  C. Style Presets (Product Shot, Social Graphic, Lifestyle, etc.)
  D. Platform Selector (auto aspect ratio, composition hints)
  E. Negative Prompt (exclusion field)
  F. Brand Photo Library (auto-pull brand reference images)

Plus:
  - Input field validation & defaults
  - Model mapping and fallback
  - Aspect ratio validation
  - Image count validation
  - Brand/persona context injection
  - execute() happy path (mocked)
  - execute() error handling
  - Summary card contents
  - Progress callbacks
  - Security: empty prompt rejection
"""

import pytest
from unittest.mock import patch, MagicMock, call

from app.recipes.image_creator import (
    ImageCreator,
    _MODEL_MAP,
    _VALID_RATIOS,
    _VALID_COUNTS,
    _STYLE_PRESETS,
    _PLATFORM_MAP,
)

# Patch targets — these are imported inside execute() so we mock at the source
_PATCH_GEN = "tools.create_image.generate_ugc_image"
_PATCH_COST = "tools.config.get_cost"
_PATCH_GEMINI = "app.recipes.image_creator.ImageCreator._call_gemini"
_PATCH_VISION = "app.recipes.image_creator.ImageCreator._call_gemini_vision"


# ─────────────────────────── Fixtures ────────────────────────────

@pytest.fixture
def recipe():
    return ImageCreator()


@pytest.fixture
def mock_brand():
    brand = MagicMock()
    brand.name = "TestBrand"
    brand.tagline = "Test tagline"
    brand.target_audience = "Young professionals"
    brand.visual_style = "Modern minimalist"
    brand.content_pillars = '["innovation", "design"]'
    brand.never_do = "No clip art"
    brand.brand_doc = "Brand guidelines doc"
    brand.colors_json = '["#FF5500", "#333333"]'
    return brand


@pytest.fixture
def mock_persona():
    persona = MagicMock()
    persona.name = "ProVoice"
    persona.tone = "professional"
    persona.voice_style = "Confident and knowledgeable"
    persona.target_audience = "Tech leaders"
    persona.industry = "SaaS"
    persona.writing_guidelines = "Be concise"
    persona.sample_phrases = ["Let's dive in", "Game changer"]
    persona.brand_keywords = ["innovative", "scalable"]
    persona.avoid_words = ["synergy", "leverage"]
    persona.ai_prompt_summary = "A confident tech leader"
    return persona


def _make_success_result(index=1):
    return {
        "status": "success",
        "result_url": f"/api/outputs/img_{index}.png",
        "task_id": None,
    }


def _make_error_result():
    return {"status": "error", "error": "Provider down"}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. INPUT FIELDS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestInputFields:
    def test_has_creation_mode_field(self, recipe):
        fields = recipe.get_input_fields()
        names = [f.name for f in fields]
        assert "creation_mode" in names

    def test_creation_mode_default_is_assisted(self, recipe):
        fields = recipe.get_input_fields()
        mode_field = next(f for f in fields if f.name == "creation_mode")
        assert mode_field.default == "assisted"

    def test_has_reference_image_field(self, recipe):
        fields = recipe.get_input_fields()
        names = [f.name for f in fields]
        assert "reference_image" in names

    def test_reference_image_is_file_type(self, recipe):
        fields = recipe.get_input_fields()
        ref = next(f for f in fields if f.name == "reference_image")
        assert ref.field_type == "file"
        assert ref.required is False

    def test_has_style_preset_field(self, recipe):
        fields = recipe.get_input_fields()
        names = [f.name for f in fields]
        assert "style_preset" in names

    def test_style_preset_options_match_constants(self, recipe):
        fields = recipe.get_input_fields()
        style = next(f for f in fields if f.name == "style_preset")
        option_values = {o["value"] for o in style.options}
        assert option_values == set(_STYLE_PRESETS.keys())

    def test_has_platform_field(self, recipe):
        fields = recipe.get_input_fields()
        names = [f.name for f in fields]
        assert "platform" in names

    def test_platform_options_match_constants(self, recipe):
        fields = recipe.get_input_fields()
        plat = next(f for f in fields if f.name == "platform")
        option_values = {o["value"] for o in plat.options}
        assert option_values == set(_PLATFORM_MAP.keys())

    def test_has_negative_prompt_field(self, recipe):
        fields = recipe.get_input_fields()
        names = [f.name for f in fields]
        assert "negative_prompt" in names

    def test_negative_prompt_is_optional(self, recipe):
        fields = recipe.get_input_fields()
        neg = next(f for f in fields if f.name == "negative_prompt")
        assert neg.required is False

    def test_field_count(self, recipe):
        """Should have 9 input fields total."""
        fields = recipe.get_input_fields()
        assert len(fields) == 9

    def test_prompt_is_required(self, recipe):
        fields = recipe.get_input_fields()
        prompt = next(f for f in fields if f.name == "prompt")
        assert prompt.required is True

    def test_step_count(self, recipe):
        assert len(recipe.get_steps()) == 4


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. STYLE PRESETS (Feature C)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestStylePresets:
    def test_none_preset_has_empty_fragment(self):
        assert _STYLE_PRESETS["none"]["prompt_fragment"] == ""

    def test_all_presets_have_label(self):
        for key, preset in _STYLE_PRESETS.items():
            assert "label" in preset, f"Preset '{key}' missing label"
            assert len(preset["label"]) > 0

    def test_all_presets_have_prompt_fragment(self):
        for key, preset in _STYLE_PRESETS.items():
            assert "prompt_fragment" in preset, f"Preset '{key}' missing prompt_fragment"

    def test_product_shot_mentions_studio(self):
        frag = _STYLE_PRESETS["product_shot"]["prompt_fragment"].lower()
        assert "studio" in frag or "product" in frag

    def test_lifestyle_mentions_natural(self):
        frag = _STYLE_PRESETS["lifestyle"]["prompt_fragment"].lower()
        assert "lifestyle" in frag or "natural" in frag

    def test_preset_count(self):
        assert len(_STYLE_PRESETS) == 8  # none + 7 styles


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. PLATFORM SELECTOR (Feature D)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestPlatformSelector:
    def test_none_platform_has_no_ratio(self):
        assert _PLATFORM_MAP["none"]["recommended_ratio"] is None

    def test_instagram_story_is_vertical(self):
        assert _PLATFORM_MAP["instagram_story"]["recommended_ratio"] == "9:16"

    def test_youtube_thumb_is_landscape(self):
        assert _PLATFORM_MAP["youtube_thumb"]["recommended_ratio"] == "16:9"

    def test_linkedin_is_portrait(self):
        assert _PLATFORM_MAP["linkedin"]["recommended_ratio"] == "4:5"

    def test_all_platforms_have_label(self):
        for key, plat in _PLATFORM_MAP.items():
            assert "label" in plat, f"Platform '{key}' missing label"

    def test_all_platforms_have_hint(self):
        for key, plat in _PLATFORM_MAP.items():
            assert "hint" in plat, f"Platform '{key}' missing hint"

    def test_all_recommended_ratios_are_valid(self):
        for key, plat in _PLATFORM_MAP.items():
            ratio = plat["recommended_ratio"]
            if ratio is not None:
                assert ratio in _VALID_RATIOS, (
                    f"Platform '{key}' has invalid ratio '{ratio}'"
                )

    def test_platform_count(self):
        assert len(_PLATFORM_MAP) == 9  # none + 8 platforms


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. AI PROMPT ASSISTANT (Feature A)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestAssistedMode:
    def test_assisted_calls_gemini(self, recipe):
        """In assisted mode, _build_assisted_prompt should call Gemini."""
        with patch(_PATCH_GEMINI, return_value="A detailed crafted prompt") as mock_gem:
            result = recipe._build_assisted_prompt(
                user_description="coffee shop ad",
                style=_STYLE_PRESETS["product_shot"],
                platform=_PLATFORM_MAP["instagram_feed"],
                negative_prompt="no text",
                reference_analysis="",
                brand_ctx="",
                persona_ctx="",
                aspect_ratio="1:1",
            )
            mock_gem.assert_called_once()
            assert result == "A detailed crafted prompt"

    def test_assisted_includes_user_description_in_meta_prompt(self, recipe):
        with patch(_PATCH_GEMINI, return_value="result") as mock_gem:
            recipe._build_assisted_prompt(
                user_description="my special product",
                style=_STYLE_PRESETS["none"],
                platform=_PLATFORM_MAP["none"],
                negative_prompt="",
                reference_analysis="",
                brand_ctx="",
                persona_ctx="",
                aspect_ratio="1:1",
            )
            call_args = mock_gem.call_args[0][0]
            assert "my special product" in call_args

    def test_assisted_includes_style_fragment(self, recipe):
        with patch(_PATCH_GEMINI, return_value="result") as mock_gem:
            recipe._build_assisted_prompt(
                user_description="test",
                style=_STYLE_PRESETS["lifestyle"],
                platform=_PLATFORM_MAP["none"],
                negative_prompt="",
                reference_analysis="",
                brand_ctx="",
                persona_ctx="",
                aspect_ratio="1:1",
            )
            call_args = mock_gem.call_args[0][0]
            assert "Lifestyle" in call_args or "lifestyle" in call_args.lower()

    def test_assisted_includes_negative_prompt(self, recipe):
        with patch(_PATCH_GEMINI, return_value="result") as mock_gem:
            recipe._build_assisted_prompt(
                user_description="test",
                style=_STYLE_PRESETS["none"],
                platform=_PLATFORM_MAP["none"],
                negative_prompt="watermarks, text, blurry",
                reference_analysis="",
                brand_ctx="",
                persona_ctx="",
                aspect_ratio="1:1",
            )
            call_args = mock_gem.call_args[0][0]
            assert "watermarks" in call_args

    def test_assisted_includes_reference_analysis(self, recipe):
        with patch(_PATCH_GEMINI, return_value="result") as mock_gem:
            recipe._build_assisted_prompt(
                user_description="test",
                style=_STYLE_PRESETS["none"],
                platform=_PLATFORM_MAP["none"],
                negative_prompt="",
                reference_analysis="Dark blue palette, moody lighting",
                brand_ctx="",
                persona_ctx="",
                aspect_ratio="1:1",
            )
            call_args = mock_gem.call_args[0][0]
            assert "Dark blue palette" in call_args

    def test_assisted_includes_brand_context(self, recipe):
        with patch(_PATCH_GEMINI, return_value="result") as mock_gem:
            recipe._build_assisted_prompt(
                user_description="test",
                style=_STYLE_PRESETS["none"],
                platform=_PLATFORM_MAP["none"],
                negative_prompt="",
                reference_analysis="",
                brand_ctx="═══ BRAND CONTEXT ═══\nBrand: TestBrand\n═══ END ═══",
                persona_ctx="",
                aspect_ratio="1:1",
            )
            call_args = mock_gem.call_args[0][0]
            assert "TestBrand" in call_args

    def test_assisted_fallback_on_gemini_error(self, recipe):
        """If Gemini fails, should fall back to manual prompt building."""
        with patch(_PATCH_GEMINI, side_effect=RuntimeError("API down")):
            result = recipe._build_assisted_prompt(
                user_description="my product",
                style=_STYLE_PRESETS["product_shot"],
                platform=_PLATFORM_MAP["none"],
                negative_prompt="",
                reference_analysis="",
                brand_ctx="",
                persona_ctx="",
                aspect_ratio="1:1",
            )
            # Should contain the raw description as fallback
            assert "my product" in result

    def test_assisted_strips_quotes(self, recipe):
        with patch(_PATCH_GEMINI, return_value='"A quoted prompt"'):
            result = recipe._build_assisted_prompt(
                user_description="test",
                style=_STYLE_PRESETS["none"],
                platform=_PLATFORM_MAP["none"],
                negative_prompt="",
                reference_analysis="",
                brand_ctx="",
                persona_ctx="",
                aspect_ratio="1:1",
            )
            assert not result.startswith('"')
            assert not result.endswith('"')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. MANUAL MODE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestManualMode:
    def test_manual_includes_raw_prompt(self):
        result = ImageCreator._build_manual_prompt(
            raw_prompt="a golden retriever",
            style=_STYLE_PRESETS["none"],
            platform=_PLATFORM_MAP["none"],
            negative_prompt="",
            reference_analysis="",
            brand_ctx="",
            persona_ctx="",
        )
        assert "a golden retriever" in result

    def test_manual_includes_style(self):
        result = ImageCreator._build_manual_prompt(
            raw_prompt="test",
            style=_STYLE_PRESETS["flat_lay"],
            platform=_PLATFORM_MAP["none"],
            negative_prompt="",
            reference_analysis="",
            brand_ctx="",
            persona_ctx="",
        )
        assert "flat lay" in result.lower() or "Flat" in result

    def test_manual_includes_negative_prompt(self):
        result = ImageCreator._build_manual_prompt(
            raw_prompt="test",
            style=_STYLE_PRESETS["none"],
            platform=_PLATFORM_MAP["none"],
            negative_prompt="no people, no text",
            reference_analysis="",
            brand_ctx="",
            persona_ctx="",
        )
        assert "no people" in result

    def test_manual_includes_platform_hint(self):
        result = ImageCreator._build_manual_prompt(
            raw_prompt="test",
            style=_STYLE_PRESETS["none"],
            platform=_PLATFORM_MAP["youtube_thumb"],
            negative_prompt="",
            reference_analysis="",
            brand_ctx="",
            persona_ctx="",
        )
        assert "YouTube" in result or "16:9" in result

    def test_manual_includes_reference_analysis(self):
        result = ImageCreator._build_manual_prompt(
            raw_prompt="test",
            style=_STYLE_PRESETS["none"],
            platform=_PLATFORM_MAP["none"],
            negative_prompt="",
            reference_analysis="Vibrant warm palette",
            brand_ctx="",
            persona_ctx="",
        )
        assert "Vibrant warm palette" in result

    def test_manual_includes_brand_and_persona(self):
        result = ImageCreator._build_manual_prompt(
            raw_prompt="test",
            style=_STYLE_PRESETS["none"],
            platform=_PLATFORM_MAP["none"],
            negative_prompt="",
            reference_analysis="",
            brand_ctx="BRAND: Acme",
            persona_ctx="PERSONA: Friendly",
        )
        assert "BRAND: Acme" in result
        assert "PERSONA: Friendly" in result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. REFERENCE IMAGE (Feature B)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestReferenceImage:
    @patch(_PATCH_COST, return_value=0.0)
    @patch(_PATCH_GEN, return_value={"status": "success", "result_url": "/img.png"})
    @patch(_PATCH_GEMINI, return_value="Detailed AI prompt")
    @patch(_PATCH_VISION, return_value="Dark palette, moody lighting, sharp focus")
    def test_reference_image_analysed(self, mock_vis, mock_gem, mock_gen, mock_cost,
                                       recipe, tmp_path):
        ref = tmp_path / "ref.jpg"
        ref.write_bytes(b"\xff\xd8\xff\xe0")  # fake JPEG header

        result = recipe.execute(
            inputs={
                "prompt": "coffee ad",
                "creation_mode": "assisted",
                "reference_image": str(ref),
            },
            run_id=1, user_id=1,
        )

        # Vision was called with the reference image
        mock_vis.assert_called_once()
        call_path = mock_vis.call_args[0][1]
        assert str(ref) in call_path

        # Reference analysis appears in outputs
        titles = [o["title"] for o in result["outputs"]]
        assert any("Reference" in t for t in titles)

    @patch(_PATCH_COST, return_value=0.0)
    @patch(_PATCH_GEN, return_value={"status": "success", "result_url": "/img.png"})
    @patch(_PATCH_GEMINI, return_value="Detailed AI prompt")
    @patch(_PATCH_VISION, return_value="Analysis text")
    def test_reference_passed_to_generate(self, mock_vis, mock_gem, mock_gen, mock_cost,
                                           recipe, tmp_path):
        ref = tmp_path / "ref.png"
        ref.write_bytes(b"\x89PNG")

        recipe.execute(
            inputs={
                "prompt": "test",
                "creation_mode": "manual",
                "reference_image": str(ref),
            },
            run_id=1, user_id=1,
        )

        # generate_ugc_image should receive reference_paths containing the ref
        gen_kwargs = mock_gen.call_args
        ref_paths = gen_kwargs.kwargs.get("reference_paths") or gen_kwargs[1].get("reference_paths")
        assert ref_paths is not None
        assert str(ref) in ref_paths

    @patch(_PATCH_COST, return_value=0.0)
    @patch(_PATCH_GEN, return_value={"status": "success", "result_url": "/img.png"})
    @patch(_PATCH_GEMINI, return_value="prompt")
    def test_nonexistent_reference_ignored(self, mock_gem, mock_gen, mock_cost, recipe):
        result = recipe.execute(
            inputs={
                "prompt": "test",
                "reference_image": "/nonexistent/ref.jpg",
            },
            run_id=1, user_id=1,
        )
        # Should succeed without error
        assert "outputs" in result

    @patch(_PATCH_COST, return_value=0.0)
    @patch(_PATCH_GEN, return_value={"status": "success", "result_url": "/img.png"})
    @patch(_PATCH_GEMINI, return_value="prompt")
    @patch(_PATCH_VISION, side_effect=RuntimeError("Vision API error"))
    def test_reference_analysis_failure_handled(self, mock_vis, mock_gem,
                                                  mock_gen, mock_cost,
                                                  recipe, tmp_path):
        ref = tmp_path / "ref.jpg"
        ref.write_bytes(b"\xff\xd8")

        result = recipe.execute(
            inputs={"prompt": "test", "reference_image": str(ref)},
            run_id=1, user_id=1,
        )
        # Should still succeed, with a warning in outputs
        assert "outputs" in result
        texts = [o.get("value", "") for o in result["outputs"]]
        assert any("Could not analyse" in t for t in texts)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. BRAND PHOTO LIBRARY (Feature F)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestBrandPhotoLibrary:
    @patch(_PATCH_COST, return_value=0.0)
    @patch(_PATCH_GEN, return_value={"status": "success", "result_url": "/img.png"})
    @patch(_PATCH_GEMINI, return_value="prompt")
    @patch("app.recipes.image_creator.ImageCreator.get_brand_reference_paths",
           return_value=["/brand/ref1.jpg", "/brand/ref2.jpg"])
    def test_brand_refs_passed_to_generator(self, mock_refs, mock_gem,
                                             mock_gen, mock_cost,
                                             recipe, mock_brand):
        result = recipe.execute(
            inputs={"prompt": "test"},
            run_id=1, user_id=1, brand=mock_brand,
        )

        gen_kwargs = mock_gen.call_args
        ref_paths = gen_kwargs.kwargs.get("reference_paths") or gen_kwargs[1].get("reference_paths")
        assert ref_paths is not None
        assert "/brand/ref1.jpg" in ref_paths

    @patch(_PATCH_COST, return_value=0.0)
    @patch(_PATCH_GEN, return_value={"status": "success", "result_url": "/img.png"})
    @patch(_PATCH_GEMINI, return_value="prompt")
    @patch("app.recipes.image_creator.ImageCreator.get_brand_reference_paths",
           return_value=["/brand/style.jpg"])
    def test_brand_refs_in_summary(self, mock_refs, mock_gem, mock_gen, mock_cost,
                                    recipe, mock_brand):
        result = recipe.execute(
            inputs={"prompt": "test"},
            run_id=1, user_id=1, brand=mock_brand,
        )
        summary = result["outputs"][0]
        assert "Brand Photos Used" in summary["value"]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 8. EXECUTE — HAPPY PATH
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestExecuteHappyPath:
    @patch(_PATCH_COST, return_value=0.07)
    @patch(_PATCH_GEN, return_value=_make_success_result())
    @patch(_PATCH_GEMINI, return_value="A stunning product photo")
    def test_assisted_single_image(self, mock_gem, mock_gen, mock_cost, recipe):
        result = recipe.execute(
            inputs={
                "prompt": "coffee shop ad",
                "creation_mode": "assisted",
                "model": "nanobanana",
            },
            run_id=1, user_id=1,
        )
        assert result["cost"] >= 0
        images = [o for o in result["outputs"] if o["type"] == "image"]
        assert len(images) == 1
        # Gemini was called for assisted prompt
        mock_gem.assert_called_once()

    @patch(_PATCH_COST, return_value=0.0)
    @patch(_PATCH_GEN, return_value=_make_success_result())
    def test_manual_single_image(self, mock_gen, mock_cost, recipe):
        result = recipe.execute(
            inputs={
                "prompt": "A golden retriever on a beach",
                "creation_mode": "manual",
            },
            run_id=1, user_id=1,
        )
        images = [o for o in result["outputs"] if o["type"] == "image"]
        assert len(images) == 1

    @patch(_PATCH_COST, return_value=0.0)
    @patch(_PATCH_GEN, side_effect=[_make_success_result(i) for i in range(4)])
    @patch(_PATCH_GEMINI, return_value="Four images prompt")
    def test_multi_image_generation(self, mock_gem, mock_gen, mock_cost, recipe):
        result = recipe.execute(
            inputs={
                "prompt": "test",
                "creation_mode": "assisted",
                "image_count": "4",
            },
            run_id=1, user_id=1,
        )
        images = [o for o in result["outputs"] if o["type"] == "image"]
        assert len(images) == 4
        assert mock_gen.call_count == 4

    @patch(_PATCH_COST, return_value=0.0)
    @patch(_PATCH_GEN, return_value=_make_success_result())
    @patch(_PATCH_GEMINI, return_value="prompt")
    def test_platform_auto_aspect_ratio(self, mock_gem, mock_gen, mock_cost, recipe):
        """Instagram Story platform should auto-set 9:16 ratio."""
        recipe.execute(
            inputs={
                "prompt": "test",
                "platform": "instagram_story",
                "aspect_ratio": "1:1",  # default — should be overridden
            },
            run_id=1, user_id=1,
        )
        gen_kwargs = mock_gen.call_args
        ratio = gen_kwargs.kwargs.get("aspect_ratio") or gen_kwargs[1].get("aspect_ratio")
        assert ratio == "9:16"

    @patch(_PATCH_COST, return_value=0.0)
    @patch(_PATCH_GEN, return_value=_make_success_result())
    @patch(_PATCH_GEMINI, return_value="prompt")
    def test_style_preset_in_assisted_prompt(self, mock_gem, mock_gen, mock_cost, recipe):
        recipe.execute(
            inputs={
                "prompt": "test",
                "creation_mode": "assisted",
                "style_preset": "product_shot",
            },
            run_id=1, user_id=1,
        )
        # Gemini meta-prompt should include the style fragment
        gemini_prompt = mock_gem.call_args[0][0]
        assert "Studio" in gemini_prompt or "product" in gemini_prompt.lower()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 9. EXECUTE — ERROR HANDLING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestExecuteErrors:
    def test_empty_prompt_raises(self, recipe):
        with pytest.raises(ValueError, match="required"):
            recipe.execute(
                inputs={"prompt": "   "},
                run_id=1, user_id=1,
            )

    @patch(_PATCH_COST, return_value=0.0)
    @patch(_PATCH_GEN, side_effect=RuntimeError("Provider exploded"))
    @patch(_PATCH_GEMINI, return_value="prompt")
    def test_generation_error_isolated(self, mock_gem, mock_gen, mock_cost, recipe):
        result = recipe.execute(
            inputs={"prompt": "test", "image_count": "2"},
            run_id=1, user_id=1,
        )
        # Both images failed but recipe didn't crash — 2 per-image errors + 1 summary error
        errors = [o for o in result["outputs"] if "Error" in o.get("title", "")]
        assert len(errors) >= 2

    @patch(_PATCH_COST, return_value=0.0)
    @patch(_PATCH_GEN, return_value=_make_error_result())
    @patch(_PATCH_GEMINI, return_value="prompt")
    def test_provider_error_status(self, mock_gem, mock_gen, mock_cost, recipe):
        result = recipe.execute(
            inputs={"prompt": "test"},
            run_id=1, user_id=1,
        )
        errors = [o for o in result["outputs"] if "Error" in o.get("title", "")]
        assert len(errors) >= 1
        assert "Provider down" in errors[0]["value"]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 10. SUMMARY CARD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestSummaryCard:
    @patch(_PATCH_COST, return_value=0.07)
    @patch(_PATCH_GEN, return_value=_make_success_result())
    @patch(_PATCH_GEMINI, return_value="prompt")
    def test_summary_contains_mode(self, mock_gem, mock_gen, mock_cost, recipe):
        result = recipe.execute(
            inputs={"prompt": "test", "creation_mode": "assisted"},
            run_id=1, user_id=1,
        )
        summary = result["outputs"][0]
        assert "Assisted" in summary["value"]

    @patch(_PATCH_COST, return_value=0.0)
    @patch(_PATCH_GEN, return_value=_make_success_result())
    def test_summary_contains_manual_mode(self, mock_gen, mock_cost, recipe):
        result = recipe.execute(
            inputs={"prompt": "test", "creation_mode": "manual"},
            run_id=1, user_id=1,
        )
        summary = result["outputs"][0]
        assert "Manual" in summary["value"]

    @patch(_PATCH_COST, return_value=0.0)
    @patch(_PATCH_GEN, return_value=_make_success_result())
    @patch(_PATCH_GEMINI, return_value="prompt")
    def test_summary_contains_style(self, mock_gem, mock_gen, mock_cost, recipe):
        result = recipe.execute(
            inputs={"prompt": "test", "style_preset": "lifestyle"},
            run_id=1, user_id=1,
        )
        summary = result["outputs"][0]
        assert "Lifestyle" in summary["value"]

    @patch(_PATCH_COST, return_value=0.0)
    @patch(_PATCH_GEN, return_value=_make_success_result())
    @patch(_PATCH_GEMINI, return_value="prompt")
    def test_summary_contains_platform(self, mock_gem, mock_gen, mock_cost, recipe):
        result = recipe.execute(
            inputs={"prompt": "test", "platform": "tiktok"},
            run_id=1, user_id=1,
        )
        summary = result["outputs"][0]
        assert "TikTok" in summary["value"]

    @patch(_PATCH_COST, return_value=0.0)
    @patch(_PATCH_GEN, return_value=_make_success_result())
    @patch(_PATCH_GEMINI, return_value="prompt")
    def test_summary_contains_negative(self, mock_gem, mock_gen, mock_cost, recipe):
        result = recipe.execute(
            inputs={"prompt": "test", "negative_prompt": "no watermarks"},
            run_id=1, user_id=1,
        )
        summary = result["outputs"][0]
        assert "watermarks" in summary["value"].lower()

    @patch(_PATCH_COST, return_value=0.0)
    @patch(_PATCH_GEN, return_value=_make_success_result())
    @patch(_PATCH_GEMINI, return_value="prompt")
    @patch("app.recipes.image_creator.ImageCreator.get_brand_reference_paths",
           return_value=[])
    def test_summary_contains_brand(self, mock_refs, mock_gem, mock_gen, mock_cost,
                                     recipe, mock_brand):
        result = recipe.execute(
            inputs={"prompt": "test"},
            run_id=1, user_id=1, brand=mock_brand,
        )
        summary = result["outputs"][0]
        assert "TestBrand" in summary["value"]

    @patch(_PATCH_COST, return_value=0.0)
    @patch(_PATCH_GEN, return_value=_make_success_result())
    @patch(_PATCH_GEMINI, return_value="prompt")
    def test_summary_contains_persona(self, mock_gem, mock_gen, mock_cost,
                                       recipe, mock_persona):
        result = recipe.execute(
            inputs={"prompt": "test"},
            run_id=1, user_id=1, persona=mock_persona,
        )
        summary = result["outputs"][0]
        assert "ProVoice" in summary["value"]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 11. VALIDATION & SECURITY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestValidation:
    @patch(_PATCH_COST, return_value=0.0)
    @patch(_PATCH_GEN, return_value=_make_success_result())
    @patch(_PATCH_GEMINI, return_value="prompt")
    def test_invalid_model_falls_back(self, mock_gem, mock_gen, mock_cost, recipe):
        result = recipe.execute(
            inputs={"prompt": "test", "model": "hacked_model"},
            run_id=1, user_id=1,
        )
        # Should fall back to nanobanana, not crash
        gen_kwargs = mock_gen.call_args
        model_used = gen_kwargs.kwargs.get("model") or gen_kwargs[1].get("model")
        assert model_used == "nano-banana-pro"

    @patch(_PATCH_COST, return_value=0.0)
    @patch(_PATCH_GEN, return_value=_make_success_result())
    @patch(_PATCH_GEMINI, return_value="prompt")
    def test_invalid_ratio_falls_back(self, mock_gem, mock_gen, mock_cost, recipe):
        result = recipe.execute(
            inputs={"prompt": "test", "aspect_ratio": "99:1"},
            run_id=1, user_id=1,
        )
        gen_kwargs = mock_gen.call_args
        ratio = gen_kwargs.kwargs.get("aspect_ratio") or gen_kwargs[1].get("aspect_ratio")
        assert ratio in _VALID_RATIOS

    @patch(_PATCH_COST, return_value=0.0)
    @patch(_PATCH_GEN, return_value=_make_success_result())
    @patch(_PATCH_GEMINI, return_value="prompt")
    def test_invalid_count_falls_back(self, mock_gem, mock_gen, mock_cost, recipe):
        result = recipe.execute(
            inputs={"prompt": "test", "image_count": "999"},
            run_id=1, user_id=1,
        )
        # Should fall back to 1 image
        assert mock_gen.call_count == 1

    @patch(_PATCH_COST, return_value=0.0)
    @patch(_PATCH_GEN, return_value=_make_success_result())
    @patch(_PATCH_GEMINI, return_value="prompt")
    def test_invalid_style_preset_falls_back(self, mock_gem, mock_gen, mock_cost, recipe):
        result = recipe.execute(
            inputs={"prompt": "test", "style_preset": "xss_attack"},
            run_id=1, user_id=1,
        )
        # Should not crash, falls back to "none"
        assert "outputs" in result

    @patch(_PATCH_COST, return_value=0.0)
    @patch(_PATCH_GEN, return_value=_make_success_result())
    @patch(_PATCH_GEMINI, return_value="prompt")
    def test_invalid_platform_falls_back(self, mock_gem, mock_gen, mock_cost, recipe):
        result = recipe.execute(
            inputs={"prompt": "test", "platform": "evil_platform"},
            run_id=1, user_id=1,
        )
        assert "outputs" in result

    @patch(_PATCH_COST, return_value=0.0)
    @patch(_PATCH_GEN, return_value=_make_success_result())
    @patch(_PATCH_GEMINI, return_value="prompt")
    def test_invalid_creation_mode_falls_back(self, mock_gem, mock_gen, mock_cost, recipe):
        result = recipe.execute(
            inputs={"prompt": "test", "creation_mode": "hacked"},
            run_id=1, user_id=1,
        )
        # Should fall back to assisted
        mock_gem.assert_called_once()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 12. PROGRESS CALLBACKS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestProgressCallbacks:
    @patch(_PATCH_COST, return_value=0.0)
    @patch(_PATCH_GEN, return_value=_make_success_result())
    @patch(_PATCH_GEMINI, return_value="prompt")
    def test_progress_called_for_all_steps(self, mock_gem, mock_gen, mock_cost, recipe):
        labels = []

        def capture(step, label):
            labels.append((step, label))

        recipe.execute(
            inputs={"prompt": "test"},
            run_id=1, user_id=1,
            on_progress=capture,
        )

        steps_seen = {s for s, _ in labels}
        assert 0 in steps_seen  # Analysing
        assert 1 in steps_seen  # Crafting prompt
        assert 2 in steps_seen  # Generating
        assert 3 in steps_seen  # Processing

    @patch(_PATCH_COST, return_value=0.0)
    @patch(_PATCH_GEN, return_value=_make_success_result())
    @patch(_PATCH_GEMINI, return_value="prompt")
    def test_assisted_crafted_prompt_in_outputs(self, mock_gem, mock_gen, mock_cost, recipe):
        result = recipe.execute(
            inputs={"prompt": "test", "creation_mode": "assisted"},
            run_id=1, user_id=1,
        )
        titles = [o["title"] for o in result["outputs"]]
        assert any("AI-Crafted" in t for t in titles)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 13. RECIPE METADATA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestMetadata:
    def test_is_active(self, recipe):
        assert recipe.is_active is True

    def test_slug(self, recipe):
        assert recipe.slug == "image-creator"

    def test_how_to_use_mentions_assisted(self, recipe):
        assert "Assisted" in recipe.how_to_use

    def test_how_to_use_mentions_reference(self, recipe):
        assert "reference" in recipe.how_to_use.lower()

    def test_how_to_use_mentions_style(self, recipe):
        assert "style" in recipe.how_to_use.lower()

    def test_how_to_use_mentions_platform(self, recipe):
        assert "platform" in recipe.how_to_use.lower() or "Platform" in recipe.how_to_use

    def test_how_to_use_mentions_negative(self, recipe):
        assert "negative" in recipe.how_to_use.lower()

    def test_how_to_use_mentions_brand(self, recipe):
        assert "Brand" in recipe.how_to_use
