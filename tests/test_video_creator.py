"""Unit tests for Video Creator recipe — Phase 34A.

Tests cover:
  1. Recipe metadata & registration
  2. Input field definitions
  3. Input validation & whitelisting
  4. Assisted prompt builder (Gemini integration)
  5. Manual prompt builder (context enrichment)
  6. Reference image handling (image-to-video vs text-to-video)
  7. Brand & persona context injection
  8. Platform auto-ratio selection
  9. Video generation success flow
 10. Error handling & resilience
 11. Cost calculation
 12. Summary card contents
"""

import os
import pytest
from unittest.mock import patch, MagicMock


# ── Helpers ──────────────────────────────────────────────────────────────

def _make_recipe():
    from app.recipes.video_creator import VideoCreator
    return VideoCreator()


def _base_inputs(**overrides):
    """Return minimal valid inputs dict, with overrides."""
    base = {
        "motion_prompt": "A cinematic product reveal with steam rising",
        "creation_mode": "manual",
        "model": "veo-3.1",
        "duration": "5",
        "aspect_ratio": "9:16",
    }
    base.update(overrides)
    return base


def _mock_generate_success(**kwargs):
    """Simulate a successful video generation result."""
    return {
        "status": "success",
        "task_id": "test-task-123",
        "result_url": "/api/outputs/test_video.mp4",
    }


def _mock_generate_error(**kwargs):
    """Simulate a failed video generation result."""
    raise RuntimeError("Provider timeout")


def _mock_gemini(prompt):
    """Simulate a Gemini text response."""
    return "Slow cinematic dolly push-in on a coffee cup, golden hour light, steam wisps rising gently."


def _mock_gemini_vision(prompt, image_path):
    """Simulate a Gemini vision response."""
    return "A coffee cup on a marble counter with warm light and steam."


# ── Flask app fixture ───────────────────────────────────────────────────

@pytest.fixture(scope="module")
def app():
    """Create a Flask app for tests that need app context."""
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    app.config["LOGIN_DISABLED"] = True
    return app


# ══════════════════════════════════════════════════════════════════════════
# 1. Recipe metadata & registration
# ══════════════════════════════════════════════════════════════════════════

class TestRecipeMetadata:
    def test_slug(self):
        r = _make_recipe()
        assert r.slug == "video-creator"

    def test_name(self):
        r = _make_recipe()
        assert r.name == "Video Creator"

    def test_category(self):
        r = _make_recipe()
        assert r.category == "video_studio"

    def test_is_active(self):
        r = _make_recipe()
        assert r.is_active is True

    def test_icon(self):
        r = _make_recipe()
        assert r.icon == "🎥"

    def test_estimated_cost(self):
        r = _make_recipe()
        assert "$" in r.estimated_cost

    def test_registered_in_global_registry(self):
        from app.recipes import get_recipe
        r = get_recipe("video-creator")
        assert r is not None
        assert r.is_active is True

    def test_how_to_use_contains_models(self):
        r = _make_recipe()
        assert "Veo 3.1" in r.how_to_use
        assert "Kling 3.0" in r.how_to_use
        assert "Sora 2" in r.how_to_use
        assert "Sora 2 Pro" in r.how_to_use


# ══════════════════════════════════════════════════════════════════════════
# 2. Input field definitions
# ══════════════════════════════════════════════════════════════════════════

class TestInputFields:
    def test_field_count(self):
        r = _make_recipe()
        fields = r.get_input_fields()
        assert len(fields) == 8

    def test_field_names(self):
        r = _make_recipe()
        names = [f.name for f in r.get_input_fields()]
        expected = [
            "creation_mode", "motion_prompt", "reference_image",
            "style_preset", "platform", "model", "duration", "aspect_ratio",
        ]
        assert names == expected

    def test_motion_prompt_required(self):
        r = _make_recipe()
        fields = {f.name: f for f in r.get_input_fields()}
        assert fields["motion_prompt"].required is True

    def test_reference_image_optional(self):
        r = _make_recipe()
        fields = {f.name: f for f in r.get_input_fields()}
        assert fields["reference_image"].required is False

    def test_model_options_include_all_four(self):
        r = _make_recipe()
        fields = {f.name: f for f in r.get_input_fields()}
        model_values = [o["value"] for o in fields["model"].options]
        assert "veo-3.1" in model_values
        assert "kling-3.0" in model_values
        assert "sora-2" in model_values
        assert "sora-2-pro" in model_values

    def test_duration_options(self):
        r = _make_recipe()
        fields = {f.name: f for f in r.get_input_fields()}
        durations = [o["value"] for o in fields["duration"].options]
        assert "4" in durations
        assert "5" in durations
        assert "8" in durations
        assert "10" in durations

    def test_creation_mode_options(self):
        r = _make_recipe()
        fields = {f.name: f for f in r.get_input_fields()}
        modes = [o["value"] for o in fields["creation_mode"].options]
        assert "assisted" in modes
        assert "manual" in modes

    def test_style_presets_count(self):
        from app.recipes.video_creator import _STYLE_PRESETS
        r = _make_recipe()
        fields = {f.name: f for f in r.get_input_fields()}
        assert len(fields["style_preset"].options) == len(_STYLE_PRESETS)

    def test_platform_options_count(self):
        from app.recipes.video_creator import _PLATFORM_MAP
        r = _make_recipe()
        fields = {f.name: f for f in r.get_input_fields()}
        assert len(fields["platform"].options) == len(_PLATFORM_MAP)

    def test_steps(self):
        r = _make_recipe()
        steps = r.get_steps()
        assert len(steps) == 4
        assert "Generating video" in steps


# ══════════════════════════════════════════════════════════════════════════
# 3. Input validation & whitelisting
# ══════════════════════════════════════════════════════════════════════════

class TestInputValidation:
    @patch("tools.create_video.generate_ugc_video", side_effect=_mock_generate_success)
    @patch("tools.config.get_cost", return_value=0.50)
    def test_empty_prompt_raises(self, mock_cost, mock_gen):
        r = _make_recipe()
        with pytest.raises(ValueError, match="required"):
            r.execute(_base_inputs(motion_prompt=""), run_id=1, user_id=1)

    @patch("tools.create_video.generate_ugc_video", side_effect=_mock_generate_success)
    @patch("tools.config.get_cost", return_value=0.50)
    def test_whitespace_only_prompt_raises(self, mock_cost, mock_gen):
        r = _make_recipe()
        with pytest.raises(ValueError, match="required"):
            r.execute(_base_inputs(motion_prompt="   "), run_id=1, user_id=1)

    @patch("tools.create_video.generate_ugc_video", side_effect=_mock_generate_success)
    @patch("tools.config.get_cost", return_value=0.50)
    def test_invalid_model_falls_back(self, mock_cost, mock_gen):
        r = _make_recipe()
        result = r.execute(
            _base_inputs(model="nonexistent-model"),
            run_id=1, user_id=1,
        )
        # Should fall back to veo-3.1 and succeed
        assert result["cost"] >= 0

    @patch("tools.create_video.generate_ugc_video", side_effect=_mock_generate_success)
    @patch("tools.config.get_cost", return_value=0.50)
    def test_invalid_aspect_ratio_falls_back(self, mock_cost, mock_gen):
        r = _make_recipe()
        result = r.execute(
            _base_inputs(aspect_ratio="99:99"),
            run_id=1, user_id=1,
        )
        assert result["cost"] >= 0

    @patch("tools.create_video.generate_ugc_video", side_effect=_mock_generate_success)
    @patch("tools.config.get_cost", return_value=0.50)
    def test_invalid_duration_falls_back(self, mock_cost, mock_gen):
        r = _make_recipe()
        result = r.execute(
            _base_inputs(duration="99"),
            run_id=1, user_id=1,
        )
        assert result["cost"] >= 0

    @patch("tools.create_video.generate_ugc_video", side_effect=_mock_generate_success)
    @patch("tools.config.get_cost", return_value=0.50)
    def test_invalid_creation_mode_falls_back(self, mock_cost, mock_gen):
        r = _make_recipe()
        result = r.execute(
            _base_inputs(creation_mode="invalid"),
            run_id=1, user_id=1,
        )
        # Should fall back to "assisted" — which would call Gemini
        # But we're not mocking Gemini so it will fall back to manual
        assert result["cost"] >= 0


# ══════════════════════════════════════════════════════════════════════════
# 4. Assisted prompt builder
# ══════════════════════════════════════════════════════════════════════════

class TestAssistedPrompt:
    def test_gemini_called_in_assisted_mode(self):
        from app.recipes.video_creator import _STYLE_PRESETS, _PLATFORM_MAP
        r = _make_recipe()
        with patch.object(r, "_call_gemini", return_value="crafted motion prompt"):
            result = r._build_assisted_prompt(
                user_description="coffee reveal",
                style=_STYLE_PRESETS["none"],
                platform=_PLATFORM_MAP["none"],
                reference_analysis="",
                brand_ctx="",
                persona_ctx="",
                aspect_ratio="9:16",
                duration="5",
                has_image=False,
            )
            assert result == "crafted motion prompt"

    def test_assisted_includes_style_direction(self):
        from app.recipes.video_creator import _STYLE_PRESETS, _PLATFORM_MAP
        r = _make_recipe()
        captured_prompts = []

        def capture_gemini(prompt):
            captured_prompts.append(prompt)
            return "crafted"

        with patch.object(r, "_call_gemini", side_effect=capture_gemini):
            r._build_assisted_prompt(
                user_description="test",
                style=_STYLE_PRESETS["product_reveal"],
                platform=_PLATFORM_MAP["none"],
                reference_analysis="",
                brand_ctx="",
                persona_ctx="",
                aspect_ratio="9:16",
                duration="5",
                has_image=False,
            )
        assert "STYLE DIRECTION" in captured_prompts[0]
        assert "product reveal" in captured_prompts[0].lower()

    def test_assisted_includes_reference_analysis(self):
        from app.recipes.video_creator import _STYLE_PRESETS, _PLATFORM_MAP
        r = _make_recipe()
        captured_prompts = []

        def capture_gemini(prompt):
            captured_prompts.append(prompt)
            return "crafted"

        with patch.object(r, "_call_gemini", side_effect=capture_gemini):
            r._build_assisted_prompt(
                user_description="test",
                style=_STYLE_PRESETS["none"],
                platform=_PLATFORM_MAP["none"],
                reference_analysis="Warm coffee cup on marble",
                brand_ctx="",
                persona_ctx="",
                aspect_ratio="9:16",
                duration="5",
                has_image=True,
            )
        assert "Warm coffee cup on marble" in captured_prompts[0]
        assert "image-to-video" in captured_prompts[0]

    def test_assisted_includes_brand_context(self):
        from app.recipes.video_creator import _STYLE_PRESETS, _PLATFORM_MAP
        r = _make_recipe()
        captured_prompts = []

        def capture_gemini(prompt):
            captured_prompts.append(prompt)
            return "crafted"

        with patch.object(r, "_call_gemini", side_effect=capture_gemini):
            r._build_assisted_prompt(
                user_description="test",
                style=_STYLE_PRESETS["none"],
                platform=_PLATFORM_MAP["none"],
                reference_analysis="",
                brand_ctx="BRAND CONTEXT: CoffeeCo",
                persona_ctx="",
                aspect_ratio="9:16",
                duration="5",
                has_image=False,
            )
        assert "BRAND CONTEXT: CoffeeCo" in captured_prompts[0]

    def test_assisted_includes_persona_context(self):
        from app.recipes.video_creator import _STYLE_PRESETS, _PLATFORM_MAP
        r = _make_recipe()
        captured_prompts = []

        def capture_gemini(prompt):
            captured_prompts.append(prompt)
            return "crafted"

        with patch.object(r, "_call_gemini", side_effect=capture_gemini):
            r._build_assisted_prompt(
                user_description="test",
                style=_STYLE_PRESETS["none"],
                platform=_PLATFORM_MAP["none"],
                reference_analysis="",
                brand_ctx="",
                persona_ctx="PERSONA: Bold trendsetter",
                aspect_ratio="9:16",
                duration="5",
                has_image=False,
            )
        assert "PERSONA: Bold trendsetter" in captured_prompts[0]

    def test_assisted_fallback_on_gemini_failure(self):
        from app.recipes.video_creator import _STYLE_PRESETS, _PLATFORM_MAP
        r = _make_recipe()

        with patch.object(r, "_call_gemini", side_effect=RuntimeError("Gemini down")):
            result = r._build_assisted_prompt(
                user_description="my coffee reveal",
                style=_STYLE_PRESETS["none"],
                platform=_PLATFORM_MAP["none"],
                reference_analysis="",
                brand_ctx="",
                persona_ctx="",
                aspect_ratio="9:16",
                duration="5",
                has_image=False,
            )
        # Falls back to manual builder — should contain raw description
        assert "my coffee reveal" in result

    def test_text_to_video_mode_in_prompt(self):
        from app.recipes.video_creator import _STYLE_PRESETS, _PLATFORM_MAP
        r = _make_recipe()
        captured = []

        def capture(prompt):
            captured.append(prompt)
            return "crafted"

        with patch.object(r, "_call_gemini", side_effect=capture):
            r._build_assisted_prompt(
                user_description="test",
                style=_STYLE_PRESETS["none"],
                platform=_PLATFORM_MAP["none"],
                reference_analysis="",
                brand_ctx="",
                persona_ctx="",
                aspect_ratio="16:9",
                duration="8",
                has_image=False,
            )
        assert "text-to-video" in captured[0]
        assert "16:9" in captured[0]
        assert "8 seconds" in captured[0]


# ══════════════════════════════════════════════════════════════════════════
# 5. Manual prompt builder
# ══════════════════════════════════════════════════════════════════════════

class TestManualPrompt:
    def test_raw_prompt_included(self):
        from app.recipes.video_creator import VideoCreator, _STYLE_PRESETS, _PLATFORM_MAP
        result = VideoCreator._build_manual_prompt(
            raw_prompt="Camera pushes in slowly",
            style=_STYLE_PRESETS["none"],
            platform=_PLATFORM_MAP["none"],
            reference_analysis="",
            brand_ctx="",
            persona_ctx="",
        )
        assert "Camera pushes in slowly" in result

    def test_style_appended(self):
        from app.recipes.video_creator import VideoCreator, _STYLE_PRESETS, _PLATFORM_MAP
        result = VideoCreator._build_manual_prompt(
            raw_prompt="test",
            style=_STYLE_PRESETS["cinematic"],
            platform=_PLATFORM_MAP["none"],
            reference_analysis="",
            brand_ctx="",
            persona_ctx="",
        )
        assert "Style direction:" in result
        assert "Cinematic" in result

    def test_platform_appended(self):
        from app.recipes.video_creator import VideoCreator, _STYLE_PRESETS, _PLATFORM_MAP
        result = VideoCreator._build_manual_prompt(
            raw_prompt="test",
            style=_STYLE_PRESETS["none"],
            platform=_PLATFORM_MAP["tiktok"],
            reference_analysis="",
            brand_ctx="",
            persona_ctx="",
        )
        assert "Platform:" in result
        assert "TikTok" in result

    def test_reference_analysis_appended(self):
        from app.recipes.video_creator import VideoCreator, _STYLE_PRESETS, _PLATFORM_MAP
        result = VideoCreator._build_manual_prompt(
            raw_prompt="test",
            style=_STYLE_PRESETS["none"],
            platform=_PLATFORM_MAP["none"],
            reference_analysis="Coffee cup warm tones marble counter",
            brand_ctx="",
            persona_ctx="",
        )
        assert "Coffee cup warm tones marble counter" in result

    def test_brand_and_persona_appended(self):
        from app.recipes.video_creator import VideoCreator, _STYLE_PRESETS, _PLATFORM_MAP
        result = VideoCreator._build_manual_prompt(
            raw_prompt="test",
            style=_STYLE_PRESETS["none"],
            platform=_PLATFORM_MAP["none"],
            reference_analysis="",
            brand_ctx="Brand: CoffeeCo",
            persona_ctx="Persona: Bold voice",
        )
        assert "Brand: CoffeeCo" in result
        assert "Persona: Bold voice" in result
        assert "STYLE CONTEXT" in result


# ══════════════════════════════════════════════════════════════════════════
# 6. Platform auto-ratio selection
# ══════════════════════════════════════════════════════════════════════════

class TestPlatformAutoRatio:
    @patch("tools.create_video.generate_ugc_video", side_effect=_mock_generate_success)
    @patch("tools.config.get_cost", return_value=0.50)
    def test_tiktok_sets_vertical(self, mock_cost, mock_gen):
        r = _make_recipe()
        result = r.execute(
            _base_inputs(platform="tiktok", aspect_ratio="9:16"),
            run_id=1, user_id=1,
        )
        # TikTok recommends 9:16 — should remain 9:16
        mock_gen.assert_called_once()
        assert mock_gen.call_args.kwargs["aspect_ratio"] == "9:16"

    @patch("tools.create_video.generate_ugc_video", side_effect=_mock_generate_success)
    @patch("tools.config.get_cost", return_value=0.50)
    def test_youtube_sets_landscape(self, mock_cost, mock_gen):
        r = _make_recipe()
        result = r.execute(
            _base_inputs(platform="youtube", aspect_ratio="9:16"),
            run_id=1, user_id=1,
        )
        # YouTube recommends 16:9 — should override default 9:16
        mock_gen.assert_called_once()
        assert mock_gen.call_args.kwargs["aspect_ratio"] == "16:9"

    @patch("tools.create_video.generate_ugc_video", side_effect=_mock_generate_success)
    @patch("tools.config.get_cost", return_value=0.50)
    def test_linkedin_sets_square(self, mock_cost, mock_gen):
        r = _make_recipe()
        result = r.execute(
            _base_inputs(platform="linkedin", aspect_ratio="9:16"),
            run_id=1, user_id=1,
        )
        mock_gen.assert_called_once()
        assert mock_gen.call_args.kwargs["aspect_ratio"] == "1:1"


# ══════════════════════════════════════════════════════════════════════════
# 7. Video generation — success flow
# ══════════════════════════════════════════════════════════════════════════

class TestGenerationSuccess:
    @patch("tools.create_video.generate_ugc_video", side_effect=_mock_generate_success)
    @patch("tools.config.get_cost", return_value=0.50)
    def test_success_produces_video_output(self, mock_cost, mock_gen):
        r = _make_recipe()
        result = r.execute(_base_inputs(), run_id=1, user_id=1)
        video_outputs = [o for o in result["outputs"] if o.get("type") == "video"]
        assert len(video_outputs) == 1
        assert video_outputs[0]["url"] == "/api/outputs/test_video.mp4"

    @patch("tools.create_video.generate_ugc_video", side_effect=_mock_generate_success)
    @patch("tools.config.get_cost", return_value=0.50)
    def test_cost_calculated(self, mock_cost, mock_gen):
        r = _make_recipe()
        result = r.execute(_base_inputs(), run_id=1, user_id=1)
        assert result["cost"] == 0.50

    @patch("tools.create_video.generate_ugc_video", side_effect=_mock_generate_success)
    @patch("tools.config.get_cost", return_value=0.30)
    def test_kling_model_cost(self, mock_cost, mock_gen):
        r = _make_recipe()
        result = r.execute(
            _base_inputs(model="kling-3.0"),
            run_id=1, user_id=1,
        )
        assert result["cost"] == 0.30

    @patch("tools.create_video.generate_ugc_video", side_effect=_mock_generate_success)
    @patch("tools.config.get_cost", return_value=0.50)
    def test_correct_model_passed_to_generator(self, mock_cost, mock_gen):
        r = _make_recipe()
        r.execute(_base_inputs(model="sora-2-pro"), run_id=1, user_id=1)
        mock_gen.assert_called_once()
        assert mock_gen.call_args.kwargs["model"] == "sora-2-pro"
        assert mock_gen.call_args.kwargs["provider"] == "wavespeed"

    @patch("tools.create_video.generate_ugc_video", side_effect=_mock_generate_success)
    @patch("tools.config.get_cost", return_value=0.50)
    def test_correct_duration_passed(self, mock_cost, mock_gen):
        r = _make_recipe()
        r.execute(_base_inputs(duration="8"), run_id=1, user_id=1)
        mock_gen.assert_called_once()
        assert mock_gen.call_args.kwargs["duration"] == "8"

    @patch("tools.create_video.generate_ugc_video", side_effect=_mock_generate_success)
    @patch("tools.config.get_cost", return_value=0.50)
    def test_text_to_video_no_image(self, mock_cost, mock_gen):
        r = _make_recipe()
        r.execute(_base_inputs(), run_id=1, user_id=1)
        mock_gen.assert_called_once()
        assert mock_gen.call_args.kwargs["image_path"] is None

    @patch("tools.create_video.generate_ugc_video", side_effect=_mock_generate_success)
    @patch("tools.config.get_cost", return_value=0.50)
    def test_image_to_video_with_reference(self, mock_cost, mock_gen, tmp_path):
        # Create a dummy image file
        img = tmp_path / "ref.png"
        img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

        r = _make_recipe()
        r.execute(
            _base_inputs(reference_image=str(img)),
            run_id=1, user_id=1,
        )
        mock_gen.assert_called_once()
        assert mock_gen.call_args.kwargs["image_path"] == str(img)


# ══════════════════════════════════════════════════════════════════════════
# 8. Error handling & resilience
# ══════════════════════════════════════════════════════════════════════════

class TestErrorHandling:
    @patch("tools.create_video.generate_ugc_video", side_effect=RuntimeError("Provider timeout"))
    @patch("tools.config.get_cost", return_value=0.50)
    def test_generation_error_produces_error_output(self, mock_cost, mock_gen):
        r = _make_recipe()
        result = r.execute(_base_inputs(), run_id=1, user_id=1)
        # Should not raise — error is caught and reported
        error_outputs = [o for o in result["outputs"] if "Error" in o.get("title", "")]
        assert len(error_outputs) >= 1
        assert result["cost"] == 0.0

    @patch("tools.create_video.generate_ugc_video", return_value={
        "status": "error", "error": "Content policy violation"
    })
    @patch("tools.config.get_cost", return_value=0.50)
    def test_provider_error_status_handled(self, mock_cost, mock_gen):
        r = _make_recipe()
        result = r.execute(_base_inputs(), run_id=1, user_id=1)
        error_outputs = [o for o in result["outputs"] if "Error" in o.get("title", "")]
        assert len(error_outputs) >= 1
        assert result["cost"] == 0.0

    @patch("tools.create_video.generate_ugc_video", side_effect=_mock_generate_success)
    @patch("tools.config.get_cost", return_value=0.50)
    def test_nonexistent_reference_image_ignored(self, mock_cost, mock_gen):
        r = _make_recipe()
        result = r.execute(
            _base_inputs(reference_image="/nonexistent/path/image.png"),
            run_id=1, user_id=1,
        )
        # Should proceed without reference (text-to-video)
        mock_gen.assert_called_once()
        assert mock_gen.call_args.kwargs["image_path"] is None

    @patch("tools.create_video.generate_ugc_video", side_effect=RuntimeError("Provider timeout"))
    @patch("tools.config.get_cost", return_value=0.50)
    def test_no_video_fallback_message(self, mock_cost, mock_gen):
        r = _make_recipe()
        result = r.execute(_base_inputs(), run_id=1, user_id=1)
        no_video_msgs = [
            o for o in result["outputs"]
            if o.get("type") == "text" and "No video was generated" in o.get("value", "")
        ]
        assert len(no_video_msgs) == 1


# ══════════════════════════════════════════════════════════════════════════
# 9. Summary card contents
# ══════════════════════════════════════════════════════════════════════════

class TestSummaryCard:
    @patch("tools.create_video.generate_ugc_video", side_effect=_mock_generate_success)
    @patch("tools.config.get_cost", return_value=0.50)
    def test_summary_contains_model(self, mock_cost, mock_gen):
        r = _make_recipe()
        result = r.execute(_base_inputs(model="veo-3.1"), run_id=1, user_id=1)
        summary = result["outputs"][0]
        assert summary["title"] == "Generation Summary"
        assert "Veo 3.1" in summary["value"]

    @patch("tools.create_video.generate_ugc_video", side_effect=_mock_generate_success)
    @patch("tools.config.get_cost", return_value=0.50)
    def test_summary_contains_mode(self, mock_cost, mock_gen):
        r = _make_recipe()
        result = r.execute(_base_inputs(creation_mode="manual"), run_id=1, user_id=1)
        summary = result["outputs"][0]
        assert "Manual" in summary["value"]

    @patch("tools.create_video.generate_ugc_video", side_effect=_mock_generate_success)
    @patch("tools.config.get_cost", return_value=0.50)
    def test_summary_contains_duration(self, mock_cost, mock_gen):
        r = _make_recipe()
        result = r.execute(_base_inputs(duration="8"), run_id=1, user_id=1)
        summary = result["outputs"][0]
        assert "8s" in summary["value"]

    @patch("tools.create_video.generate_ugc_video", side_effect=_mock_generate_success)
    @patch("tools.config.get_cost", return_value=0.50)
    def test_summary_shows_style_when_set(self, mock_cost, mock_gen):
        r = _make_recipe()
        result = r.execute(
            _base_inputs(style_preset="cinematic"),
            run_id=1, user_id=1,
        )
        summary = result["outputs"][0]
        assert "Cinematic" in summary["value"]

    @patch("tools.create_video.generate_ugc_video", side_effect=_mock_generate_success)
    @patch("tools.config.get_cost", return_value=0.50)
    def test_summary_shows_platform_when_set(self, mock_cost, mock_gen):
        r = _make_recipe()
        result = r.execute(
            _base_inputs(platform="tiktok"),
            run_id=1, user_id=1,
        )
        summary = result["outputs"][0]
        assert "TikTok" in summary["value"]

    @patch("tools.create_video.generate_ugc_video", side_effect=_mock_generate_success)
    @patch("tools.config.get_cost", return_value=0.50)
    def test_summary_contains_brand(self, mock_cost, mock_gen, app):
        with app.app_context():
            r = _make_recipe()
            mock_brand = MagicMock()
            mock_brand.name = "CoffeeCo"
            mock_brand.tagline = "Wake up bold"
            mock_brand.target_audience = "Coffee lovers"
            mock_brand.visual_style = "Warm"
            mock_brand.content_pillars = None
            mock_brand.never_do = None
            mock_brand.brand_doc = None
            mock_brand.id = 99

            result = r.execute(
                _base_inputs(), run_id=1, user_id=1,
                brand=mock_brand,
            )
            summary = result["outputs"][0]
            assert "CoffeeCo" in summary["value"]

    @patch("tools.create_video.generate_ugc_video", side_effect=_mock_generate_success)
    @patch("tools.config.get_cost", return_value=0.50)
    def test_summary_contains_persona(self, mock_cost, mock_gen):
        r = _make_recipe()
        mock_persona = MagicMock()
        mock_persona.name = "Bold Voice"
        result = r.execute(
            _base_inputs(), run_id=1, user_id=1,
            persona=mock_persona,
        )
        summary = result["outputs"][0]
        assert "Bold Voice" in summary["value"]

    @patch("tools.create_video.generate_ugc_video", side_effect=_mock_generate_success)
    @patch("tools.config.get_cost", return_value=0.50)
    def test_summary_shows_text_to_video(self, mock_cost, mock_gen):
        r = _make_recipe()
        result = r.execute(_base_inputs(), run_id=1, user_id=1)
        summary = result["outputs"][0]
        assert "Text To Video" in summary["value"]

    @patch("tools.create_video.generate_ugc_video", side_effect=_mock_generate_success)
    @patch("tools.config.get_cost", return_value=0.50)
    def test_summary_shows_image_to_video(self, mock_cost, mock_gen, tmp_path):
        img = tmp_path / "ref.png"
        img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

        r = _make_recipe()
        result = r.execute(
            _base_inputs(reference_image=str(img)),
            run_id=1, user_id=1,
        )
        summary = result["outputs"][0]
        assert "Image To Video" in summary["value"]
        assert "Reference Image" in summary["value"]


# ══════════════════════════════════════════════════════════════════════════
# 10. Reference image analysis (with mock Gemini)
# ══════════════════════════════════════════════════════════════════════════

class TestReferenceImageAnalysis:
    @patch("tools.create_video.generate_ugc_video", side_effect=_mock_generate_success)
    @patch("tools.config.get_cost", return_value=0.50)
    def test_reference_image_analysed(self, mock_cost, mock_gen, tmp_path):
        img = tmp_path / "ref.png"
        img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

        r = _make_recipe()
        with patch.object(r, "_call_gemini_vision", return_value="Coffee cup on marble"):
            result = r.execute(
                _base_inputs(reference_image=str(img)),
                run_id=1, user_id=1,
            )

        analysis_outputs = [
            o for o in result["outputs"]
            if "Reference Image Analysis" in o.get("title", "")
        ]
        assert len(analysis_outputs) == 1
        assert "Coffee cup on marble" in analysis_outputs[0]["value"]

    @patch("tools.create_video.generate_ugc_video", side_effect=_mock_generate_success)
    @patch("tools.config.get_cost", return_value=0.50)
    def test_reference_analysis_failure_handled(self, mock_cost, mock_gen, tmp_path):
        img = tmp_path / "ref.png"
        img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

        r = _make_recipe()
        with patch.object(r, "_call_gemini_vision", side_effect=RuntimeError("Vision API down")):
            result = r.execute(
                _base_inputs(reference_image=str(img)),
                run_id=1, user_id=1,
            )

        warning_outputs = [
            o for o in result["outputs"]
            if "Reference Analysis" in o.get("title", "")
        ]
        assert len(warning_outputs) == 1
        assert "Could not analyse" in warning_outputs[0]["value"]


# ══════════════════════════════════════════════════════════════════════════
# 11. All four models — correct provider routing
# ══════════════════════════════════════════════════════════════════════════

class TestModelRouting:
    @patch("tools.create_video.generate_ugc_video", side_effect=_mock_generate_success)
    @patch("tools.config.get_cost", return_value=0.50)
    def test_veo_routes_to_google(self, mock_cost, mock_gen):
        r = _make_recipe()
        r.execute(_base_inputs(model="veo-3.1"), run_id=1, user_id=1)
        assert mock_gen.call_args.kwargs["model"] == "veo-3.1"
        assert mock_gen.call_args.kwargs["provider"] == "google"

    @patch("tools.create_video.generate_ugc_video", side_effect=_mock_generate_success)
    @patch("tools.config.get_cost", return_value=0.30)
    def test_kling_routes_to_wavespeed(self, mock_cost, mock_gen):
        r = _make_recipe()
        r.execute(_base_inputs(model="kling-3.0"), run_id=1, user_id=1)
        assert mock_gen.call_args.kwargs["model"] == "kling-3.0"
        assert mock_gen.call_args.kwargs["provider"] == "wavespeed"

    @patch("tools.create_video.generate_ugc_video", side_effect=_mock_generate_success)
    @patch("tools.config.get_cost", return_value=0.30)
    def test_sora2_routes_to_wavespeed(self, mock_cost, mock_gen):
        r = _make_recipe()
        r.execute(_base_inputs(model="sora-2"), run_id=1, user_id=1)
        assert mock_gen.call_args.kwargs["model"] == "sora-2"
        assert mock_gen.call_args.kwargs["provider"] == "wavespeed"

    @patch("tools.create_video.generate_ugc_video", side_effect=_mock_generate_success)
    @patch("tools.config.get_cost", return_value=0.30)
    def test_sora2_pro_routes_to_wavespeed(self, mock_cost, mock_gen):
        r = _make_recipe()
        r.execute(_base_inputs(model="sora-2-pro"), run_id=1, user_id=1)
        assert mock_gen.call_args.kwargs["model"] == "sora-2-pro"
        assert mock_gen.call_args.kwargs["provider"] == "wavespeed"


# ══════════════════════════════════════════════════════════════════════════
# 12. Progress reporting
# ══════════════════════════════════════════════════════════════════════════

class TestProgressReporting:
    @patch("tools.create_video.generate_ugc_video", side_effect=_mock_generate_success)
    @patch("tools.config.get_cost", return_value=0.50)
    def test_progress_callbacks_called(self, mock_cost, mock_gen):
        r = _make_recipe()
        progress_calls = []

        def capture_progress(step, label):
            progress_calls.append((step, label))

        r.execute(_base_inputs(), run_id=1, user_id=1, on_progress=capture_progress)
        # Should have at least 4 progress calls (one per step)
        assert len(progress_calls) >= 4
        steps = [p[0] for p in progress_calls]
        assert 0 in steps
        assert 1 in steps
        assert 2 in steps
        assert 3 in steps

    @patch("tools.create_video.generate_ugc_video", side_effect=_mock_generate_success)
    @patch("tools.config.get_cost", return_value=0.50)
    def test_progress_mentions_model_name(self, mock_cost, mock_gen):
        r = _make_recipe()
        labels = []

        def capture(step, label):
            labels.append(label)

        r.execute(
            _base_inputs(model="kling-3.0"),
            run_id=1, user_id=1,
            on_progress=capture,
        )
        gen_labels = [l for l in labels if "Kling" in l]
        assert len(gen_labels) >= 1


# ══════════════════════════════════════════════════════════════════════════
# 13. Style presets — data integrity
# ══════════════════════════════════════════════════════════════════════════

class TestStylePresets:
    def test_all_presets_have_required_keys(self):
        from app.recipes.video_creator import _STYLE_PRESETS
        for key, preset in _STYLE_PRESETS.items():
            assert "label" in preset, f"Preset '{key}' missing 'label'"
            assert "prompt_fragment" in preset, f"Preset '{key}' missing 'prompt_fragment'"

    def test_none_preset_has_empty_fragment(self):
        from app.recipes.video_creator import _STYLE_PRESETS
        assert _STYLE_PRESETS["none"]["prompt_fragment"] == ""

    def test_non_none_presets_have_content(self):
        from app.recipes.video_creator import _STYLE_PRESETS
        for key, preset in _STYLE_PRESETS.items():
            if key != "none":
                assert len(preset["prompt_fragment"]) > 10, (
                    f"Preset '{key}' has too short a prompt fragment"
                )


# ══════════════════════════════════════════════════════════════════════════
# 14. Platform map — data integrity
# ══════════════════════════════════════════════════════════════════════════

class TestPlatformMap:
    def test_all_platforms_have_required_keys(self):
        from app.recipes.video_creator import _PLATFORM_MAP
        for key, plat in _PLATFORM_MAP.items():
            assert "label" in plat, f"Platform '{key}' missing 'label'"
            assert "recommended_ratio" in plat, f"Platform '{key}' missing 'recommended_ratio'"
            assert "hint" in plat, f"Platform '{key}' missing 'hint'"

    def test_none_platform_has_no_ratio(self):
        from app.recipes.video_creator import _PLATFORM_MAP
        assert _PLATFORM_MAP["none"]["recommended_ratio"] is None

    def test_platform_ratios_are_valid(self):
        from app.recipes.video_creator import _PLATFORM_MAP, _VALID_RATIOS
        for key, plat in _PLATFORM_MAP.items():
            if plat["recommended_ratio"] is not None:
                assert plat["recommended_ratio"] in _VALID_RATIOS, (
                    f"Platform '{key}' has invalid ratio: {plat['recommended_ratio']}"
                )
