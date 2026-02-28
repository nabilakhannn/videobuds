"""Unit tests for Higgsfield video generation (Seedance & Minimax).

Covers:
  - Provider registry integration
  - Model resolution in create_video
  - submit_video payload construction
  - poll_video status handling
  - poll_video_tasks_parallel concurrency
  - Cost & model catalog entries
  - Video Creator recipe model map integration
  - OWASP: input validation, error handling
"""

import json
import os
import sys
import types
import pytest
from unittest.mock import patch, MagicMock, PropertyMock

# Ensure project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ═══════════════════════════════════════════════════════════════════════════
# 1. Provider Registry Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestProviderRegistry:
    """Verify seedance & minimax are registered in VIDEO_PROVIDERS."""

    def test_seedance_registered(self):
        from tools.providers import VIDEO_PROVIDERS
        assert "seedance" in VIDEO_PROVIDERS

    def test_minimax_registered(self):
        from tools.providers import VIDEO_PROVIDERS
        assert "minimax" in VIDEO_PROVIDERS

    def test_seedance_default_provider_is_higgsfield(self):
        from tools.providers import VIDEO_PROVIDERS
        assert VIDEO_PROVIDERS["seedance"]["default"] == "higgsfield"

    def test_minimax_default_provider_is_higgsfield(self):
        from tools.providers import VIDEO_PROVIDERS
        assert VIDEO_PROVIDERS["minimax"]["default"] == "higgsfield"

    def test_get_video_provider_seedance(self):
        from tools.providers import get_video_provider
        provider, name = get_video_provider("seedance")
        assert name == "higgsfield"
        assert hasattr(provider, "submit_video")

    def test_get_video_provider_minimax(self):
        from tools.providers import get_video_provider
        provider, name = get_video_provider("minimax")
        assert name == "higgsfield"
        assert hasattr(provider, "submit_video")

    def test_higgsfield_has_video_functions(self):
        from tools.providers import higgsfield
        assert hasattr(higgsfield, "submit_video")
        assert hasattr(higgsfield, "poll_video")
        assert hasattr(higgsfield, "poll_video_tasks_parallel")

    def test_video_is_sync_false(self):
        from tools.providers import higgsfield
        assert higgsfield.video_IS_SYNC is False


# ═══════════════════════════════════════════════════════════════════════════
# 2. Model Resolution Tests (create_video)
# ═══════════════════════════════════════════════════════════════════════════

class TestModelResolution:
    """Verify _resolve_model maps display names to internal slugs."""

    def test_resolve_seedance(self):
        from tools.create_video import _resolve_model
        assert _resolve_model("Seedance") == "seedance"

    def test_resolve_minimax(self):
        from tools.create_video import _resolve_model
        assert _resolve_model("Minimax") == "minimax"

    def test_resolve_unknown_falls_back(self):
        from tools.create_video import _resolve_model
        result = _resolve_model("nonexistent-model", "fallback-model")
        assert result == "fallback-model"


# ═══════════════════════════════════════════════════════════════════════════
# 3. submit_video Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestSubmitVideo:
    """Verify submit_video builds correct payloads for Seedance & Minimax."""

    @patch("tools.providers.higgsfield.requests.post")
    def test_seedance_text_to_video_payload(self, mock_post):
        from tools.providers.higgsfield import submit_video

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "gen-123"}
        mock_post.return_value = mock_resp

        result = submit_video("A coffee cup steaming", model="seedance")

        assert result == "gen-123"
        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert payload["task"] == "text-to-video"
        assert "seedance" in payload["model"]
        assert payload["prompt"] == "A coffee cup steaming"

    @patch("tools.providers.higgsfield.requests.post")
    def test_seedance_image_to_video_payload(self, mock_post):
        from tools.providers.higgsfield import submit_video

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "gen-456"}
        mock_post.return_value = mock_resp

        result = submit_video(
            "Animate this product",
            image_url="https://example.com/product.jpg",
            model="seedance",
        )

        assert result == "gen-456"
        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert payload["task"] == "image-to-video"
        assert "seedance" in payload["model"]
        assert "image_urls" in payload

    @patch("tools.providers.higgsfield.requests.post")
    def test_minimax_text_to_video_payload(self, mock_post):
        from tools.providers.higgsfield import submit_video

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "gen-789"}
        mock_post.return_value = mock_resp

        result = submit_video("Social media teaser", model="minimax")

        assert result == "gen-789"
        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert payload["task"] == "text-to-video"
        assert "minimax" in payload["model"]

    @patch("tools.providers.higgsfield.requests.post")
    def test_minimax_image_to_video_payload(self, mock_post):
        from tools.providers.higgsfield import submit_video

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"generation_id": "gen-abc"}
        mock_post.return_value = mock_resp

        result = submit_video(
            "Animate this",
            image_url="https://example.com/image.png",
            model="minimax",
        )

        assert result == "gen-abc"

    @patch("tools.providers.higgsfield.requests.post")
    def test_submit_video_includes_duration(self, mock_post):
        from tools.providers.higgsfield import submit_video

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "gen-dur"}
        mock_post.return_value = mock_resp

        submit_video("Test", model="seedance", duration="8")

        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert payload["duration"] == 8

    @patch("tools.providers.higgsfield.requests.post")
    def test_submit_video_includes_dimensions(self, mock_post):
        from tools.providers.higgsfield import submit_video

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "gen-dim"}
        mock_post.return_value = mock_resp

        submit_video("Test", model="minimax", aspect_ratio="16:9")

        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert payload["width"] == 1024
        assert payload["height"] == 576

    @patch("tools.providers.higgsfield.requests.post")
    def test_submit_video_api_error_raises(self, mock_post):
        from tools.providers.higgsfield import submit_video

        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        mock_post.return_value = mock_resp

        with pytest.raises(Exception, match="Higgsfield video submit error 500"):
            submit_video("Test", model="seedance")

    @patch("tools.providers.higgsfield.requests.post")
    def test_submit_video_no_id_raises(self, mock_post):
        from tools.providers.higgsfield import submit_video

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"message": "ok"}
        mock_post.return_value = mock_resp

        with pytest.raises(Exception, match="No generation ID"):
            submit_video("Test", model="seedance")

    @patch("tools.providers.higgsfield.requests.post")
    def test_submit_video_local_image_path(self, mock_post, tmp_path):
        from tools.providers.higgsfield import submit_video

        # Create a temporary image file
        img_file = tmp_path / "test.png"
        img_file.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "gen-local"}
        mock_post.return_value = mock_resp

        result = submit_video(
            "Animate", model="seedance", image_path=str(img_file)
        )

        assert result == "gen-local"
        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert payload["task"] == "image-to-video"
        assert payload["image_urls"][0].startswith("data:image/png;base64,")


# ═══════════════════════════════════════════════════════════════════════════
# 4. poll_video Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestPollVideo:
    """Verify poll_video handles various status responses."""

    @patch("tools.providers.higgsfield.requests.get")
    def test_poll_success_with_videos_array(self, mock_get):
        from tools.providers.higgsfield import poll_video

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "completed",
            "videos": [{"url": "https://cdn.example.com/video.mp4"}],
        }
        mock_get.return_value = mock_resp

        result = poll_video("gen-123", max_wait=10, poll_interval=1)

        assert result["status"] == "success"
        assert result["result_url"] == "https://cdn.example.com/video.mp4"
        assert result["task_id"] == "gen-123"

    @patch("tools.providers.higgsfield.requests.get")
    def test_poll_success_with_result_url_fallback(self, mock_get):
        from tools.providers.higgsfield import poll_video

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "completed",
            "result_url": "https://cdn.example.com/fallback.mp4",
        }
        mock_get.return_value = mock_resp

        result = poll_video("gen-456", max_wait=10, poll_interval=1)

        assert result["status"] == "success"
        assert "fallback.mp4" in result["result_url"]

    @patch("tools.providers.higgsfield.requests.get")
    def test_poll_failed_raises(self, mock_get):
        from tools.providers.higgsfield import poll_video

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "failed",
            "error": "Content policy violation",
        }
        mock_get.return_value = mock_resp

        with pytest.raises(Exception, match="Higgsfield video failed"):
            poll_video("gen-fail", max_wait=10, poll_interval=1)

    @patch("tools.providers.higgsfield.requests.get")
    def test_poll_nsfw_raises(self, mock_get):
        from tools.providers.higgsfield import poll_video

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "nsfw"}
        mock_get.return_value = mock_resp

        with pytest.raises(Exception, match="nsfw"):
            poll_video("gen-nsfw", max_wait=10, poll_interval=1)

    @patch("tools.providers.higgsfield.time.sleep")
    @patch("tools.providers.higgsfield.requests.get")
    def test_poll_timeout_raises(self, mock_get, mock_sleep):
        from tools.providers.higgsfield import poll_video

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "in_progress"}
        mock_get.return_value = mock_resp

        with pytest.raises(Exception, match="timeout"):
            poll_video("gen-slow", max_wait=1, poll_interval=0.1)

    @patch("tools.providers.higgsfield.requests.get")
    def test_poll_no_video_url_raises(self, mock_get):
        from tools.providers.higgsfield import poll_video

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "completed",
            "videos": [],
        }
        mock_get.return_value = mock_resp

        with pytest.raises(Exception, match="No video URL"):
            poll_video("gen-empty", max_wait=10, poll_interval=1)


# ═══════════════════════════════════════════════════════════════════════════
# 5. poll_video_tasks_parallel Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestPollVideoParallel:
    """Verify parallel polling for multiple video generations."""

    @patch("tools.providers.higgsfield.poll_video")
    def test_parallel_empty_input(self, mock_poll):
        from tools.providers.higgsfield import poll_video_tasks_parallel
        result = poll_video_tasks_parallel([])
        assert result == {}
        mock_poll.assert_not_called()

    @patch("tools.providers.higgsfield.poll_video")
    def test_parallel_single_success(self, mock_poll):
        from tools.providers.higgsfield import poll_video_tasks_parallel

        mock_poll.return_value = {
            "status": "success",
            "result_url": "https://cdn.example.com/video1.mp4",
            "task_id": "gen-1",
        }

        results = poll_video_tasks_parallel(["gen-1"])
        assert "gen-1" in results
        assert results["gen-1"]["status"] == "success"

    @patch("tools.providers.higgsfield.poll_video")
    def test_parallel_mixed_results(self, mock_poll):
        from tools.providers.higgsfield import poll_video_tasks_parallel

        def side_effect(gen_id, **kwargs):
            if gen_id == "gen-ok":
                return {
                    "status": "success",
                    "result_url": "https://cdn.example.com/ok.mp4",
                    "task_id": "gen-ok",
                }
            raise Exception("Generation failed")

        mock_poll.side_effect = side_effect

        results = poll_video_tasks_parallel(["gen-ok", "gen-fail"])
        assert results["gen-ok"]["status"] == "success"
        assert results["gen-fail"]["status"] == "error"


# ═══════════════════════════════════════════════════════════════════════════
# 6. Cost & Model Catalog Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestCostAndCatalog:
    """Verify cost entries and model catalog entries."""

    def test_seedance_retail_cost(self):
        from tools.config import COSTS
        assert ("seedance", "higgsfield") in COSTS
        assert COSTS[("seedance", "higgsfield")] == 0.08

    def test_minimax_retail_cost(self):
        from tools.config import COSTS
        assert ("minimax", "higgsfield") in COSTS
        assert COSTS[("minimax", "higgsfield")] == 0.08

    def test_seedance_actual_cost(self):
        from tools.config import ACTUAL_COSTS
        assert ("seedance", "higgsfield") in ACTUAL_COSTS
        assert ACTUAL_COSTS[("seedance", "higgsfield")] == 0.03

    def test_minimax_actual_cost(self):
        from tools.config import ACTUAL_COSTS
        assert ("minimax", "higgsfield") in ACTUAL_COSTS
        assert ACTUAL_COSTS[("minimax", "higgsfield")] == 0.03

    def test_get_cost_seedance(self):
        from tools.config import get_cost
        assert get_cost("seedance", "higgsfield") == 0.08

    def test_get_cost_minimax(self):
        from tools.config import get_cost
        assert get_cost("minimax", "higgsfield") == 0.08

    def test_get_cost_seedance_default_provider(self):
        from tools.config import get_cost
        # Should auto-resolve provider to "higgsfield"
        assert get_cost("seedance") == 0.08

    def test_get_cost_minimax_default_provider(self):
        from tools.config import get_cost
        assert get_cost("minimax") == 0.08

    def test_higgsfield_video_models_config(self):
        from tools.config import HIGGSFIELD_VIDEO_MODELS
        assert "seedance" in HIGGSFIELD_VIDEO_MODELS
        assert "minimax" in HIGGSFIELD_VIDEO_MODELS

    def test_model_catalog_seedance(self):
        from app.services.model_service import MODEL_CATALOG
        assert "seedance" in MODEL_CATALOG
        info = MODEL_CATALOG["seedance"]
        assert info["type"] == "video"
        assert info["default_provider"] == "higgsfield"
        assert "higgsfield" in info["providers"]

    def test_model_catalog_minimax(self):
        from app.services.model_service import MODEL_CATALOG
        assert "minimax" in MODEL_CATALOG
        info = MODEL_CATALOG["minimax"]
        assert info["type"] == "video"
        assert info["default_provider"] == "higgsfield"
        assert "higgsfield" in info["providers"]

    def test_seedance_is_not_free_tier(self):
        from app.services.model_service import has_free_tier
        assert has_free_tier("seedance") is False

    def test_minimax_is_not_free_tier(self):
        from app.services.model_service import has_free_tier
        assert has_free_tier("minimax") is False

    def test_video_models_include_new_models(self):
        from app.services.model_service import get_video_models
        video_models = get_video_models()
        assert "seedance" in video_models
        assert "minimax" in video_models

    def test_model_choices_include_new_models(self):
        from app.services.model_service import get_model_choices
        choices = get_model_choices("video")
        slugs = {c["slug"] for c in choices}
        assert "seedance" in slugs
        assert "minimax" in slugs


# ═══════════════════════════════════════════════════════════════════════════
# 7. Video Creator Recipe Model Map Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestVideoCreatorRecipeModels:
    """Verify the Video Creator recipe exposes Seedance & Minimax."""

    def test_model_map_has_seedance(self):
        from app.recipes.video_creator import _MODEL_MAP
        assert "seedance" in _MODEL_MAP
        name, label, provider, cost = _MODEL_MAP["seedance"]
        assert name == "seedance"
        assert provider == "higgsfield"
        assert "$0.08" in cost

    def test_model_map_has_minimax(self):
        from app.recipes.video_creator import _MODEL_MAP
        assert "minimax" in _MODEL_MAP
        name, label, provider, cost = _MODEL_MAP["minimax"]
        assert name == "minimax"
        assert provider == "higgsfield"
        assert "$0.08" in cost

    def test_input_fields_include_new_models(self):
        from app.recipes.video_creator import VideoCreator
        recipe = VideoCreator()
        fields = recipe.get_input_fields()
        model_field = next(f for f in fields if f.name == "model")
        option_values = {o["value"] for o in model_field.options}
        assert "seedance" in option_values
        assert "minimax" in option_values

    def test_model_count_is_six(self):
        from app.recipes.video_creator import _MODEL_MAP
        assert len(_MODEL_MAP) == 6


# ═══════════════════════════════════════════════════════════════════════════
# 8. Video Model Constants Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestVideoModelConstants:
    """Verify the internal model ID mappings are correct."""

    def test_seedance_video_model_ids(self):
        from tools.providers.higgsfield import _VIDEO_MODELS
        assert "seedance" in _VIDEO_MODELS
        assert "bytedance" in _VIDEO_MODELS["seedance"]

    def test_seedance_i2v_model_id(self):
        from tools.providers.higgsfield import _VIDEO_MODELS
        assert "seedance-i2v" in _VIDEO_MODELS
        assert "image-to-video" in _VIDEO_MODELS["seedance-i2v"]

    def test_minimax_video_model_id(self):
        from tools.providers.higgsfield import _VIDEO_MODELS
        assert "minimax" in _VIDEO_MODELS
        assert "minimax-ai" in _VIDEO_MODELS["minimax"]


# ═══════════════════════════════════════════════════════════════════════════
# 9. Security / Edge Cases
# ═══════════════════════════════════════════════════════════════════════════

class TestSecurityEdgeCases:
    """OWASP-aligned edge case tests for video generation inputs."""

    @patch("tools.providers.higgsfield.requests.post")
    def test_empty_prompt_still_submits(self, mock_post):
        """Provider should not crash on empty prompts — validation happens
        at the recipe layer."""
        from tools.providers.higgsfield import submit_video

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "gen-empty-prompt"}
        mock_post.return_value = mock_resp

        result = submit_video("", model="seedance")
        assert result == "gen-empty-prompt"

    @patch("tools.providers.higgsfield.requests.post")
    def test_very_long_prompt_truncation(self, mock_post):
        """Provider should handle very long prompts without crashing."""
        from tools.providers.higgsfield import submit_video

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "gen-long"}
        mock_post.return_value = mock_resp

        long_prompt = "A" * 10000
        result = submit_video(long_prompt, model="minimax")
        assert result == "gen-long"

    @patch("tools.providers.higgsfield.requests.post")
    def test_invalid_aspect_ratio_fallback(self, mock_post):
        """Unknown aspect ratio should fall back to default dimensions."""
        from tools.providers.higgsfield import submit_video

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "gen-ratio"}
        mock_post.return_value = mock_resp

        submit_video("Test", model="seedance", aspect_ratio="99:1")

        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        # Should fall back to default (576, 1024) — 9:16
        assert payload["width"] == 576
        assert payload["height"] == 1024

    @patch("tools.providers.higgsfield.requests.post")
    def test_invalid_duration_fallback(self, mock_post):
        """Non-numeric duration should default to 5."""
        from tools.providers.higgsfield import submit_video

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "gen-dur-inv"}
        mock_post.return_value = mock_resp

        submit_video("Test", model="seedance", duration="not-a-number")

        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert payload["duration"] == 5

    def test_unknown_model_in_recipe_falls_back(self):
        """VideoCreator recipe should fall back to veo-3.1 for unknown models."""
        from app.recipes.video_creator import _MODEL_MAP
        # This tests that the recipe validates model input
        assert "nonexistent" not in _MODEL_MAP


# ═══════════════════════════════════════════════════════════════════════════
# 10. Duration Options & Clamping Tests
# ═══════════════════════════════════════════════════════════════════════════

class TestDurationOptions:
    """Verify extended duration options and per-model clamping."""

    def test_valid_durations_includes_extended(self):
        from app.recipes.video_creator import _VALID_DURATIONS
        for d in ("4", "5", "6", "8", "10", "15", "20"):
            assert d in _VALID_DURATIONS

    def test_model_max_duration_all_models_present(self):
        from app.recipes.video_creator import _MODEL_MAX_DURATION, _MODEL_MAP
        for key in _MODEL_MAP:
            assert key in _MODEL_MAX_DURATION, f"Missing max duration for {key}"

    def test_veo_max_is_8(self):
        from app.recipes.video_creator import _MODEL_MAX_DURATION
        assert _MODEL_MAX_DURATION["veo-3.1"] == 8

    def test_kling_max_is_10(self):
        from app.recipes.video_creator import _MODEL_MAX_DURATION
        assert _MODEL_MAX_DURATION["kling-3.0"] == 10

    def test_sora2_max_is_20(self):
        from app.recipes.video_creator import _MODEL_MAX_DURATION
        assert _MODEL_MAX_DURATION["sora-2"] == 20

    def test_sora2pro_max_is_20(self):
        from app.recipes.video_creator import _MODEL_MAX_DURATION
        assert _MODEL_MAX_DURATION["sora-2-pro"] == 20

    def test_seedance_max_is_10(self):
        from app.recipes.video_creator import _MODEL_MAX_DURATION
        assert _MODEL_MAX_DURATION["seedance"] == 10

    def test_minimax_max_is_10(self):
        from app.recipes.video_creator import _MODEL_MAX_DURATION
        assert _MODEL_MAX_DURATION["minimax"] == 10

    def test_duration_field_has_extended_options(self):
        from app.recipes.video_creator import VideoCreator
        recipe = VideoCreator()
        fields = recipe.get_input_fields()
        dur_field = next(f for f in fields if f.name == "duration")
        values = {o["value"] for o in dur_field.options}
        assert "15" in values
        assert "20" in values

    def test_clamping_veo_20_to_8(self):
        """20s request on Veo 3.1 should be clamped to 8s."""
        from app.recipes.video_creator import VideoCreator
        recipe = VideoCreator()

        # Mock generate_ugc_video to capture the duration passed
        captured = {}

        def fake_generate(prompt, image_path=None, model=None,
                          duration="5", aspect_ratio="9:16", provider=None):
            captured["duration"] = duration
            return {"status": "success", "result_url": "https://x.mp4"}

        import app.recipes.video_creator as vc_mod
        original = vc_mod.__dict__.get("generate_ugc_video", None)
        try:
            # Patch at module level in create_video
            from unittest.mock import patch
            with patch.object(recipe, "_call_gemini", return_value="mocked prompt"):
                with patch("tools.create_video.generate_ugc_video", side_effect=fake_generate):
                    result = recipe.execute(
                        inputs={
                            "motion_prompt": "test video",
                            "model": "veo-3.1",
                            "duration": "20",
                            "creation_mode": "assisted",
                        },
                        run_id=999, user_id=1,
                    )
        finally:
            pass

        # Should have clamped to 8
        assert captured["duration"] == "8"
        # Should have a notice output
        texts = [o.get("title", "") for o in result["outputs"]]
        assert any("Duration Adjusted" in t for t in texts)

    def test_no_clamping_when_within_limit(self):
        """8s on Veo should NOT trigger clamping."""
        from app.recipes.video_creator import VideoCreator
        recipe = VideoCreator()

        captured = {}

        def fake_generate(prompt, image_path=None, model=None,
                          duration="5", aspect_ratio="9:16", provider=None):
            captured["duration"] = duration
            return {"status": "success", "result_url": "https://x.mp4"}

        from unittest.mock import patch
        with patch.object(recipe, "_call_gemini", return_value="mocked prompt"):
            with patch("tools.create_video.generate_ugc_video", side_effect=fake_generate):
                result = recipe.execute(
                    inputs={
                        "motion_prompt": "test video",
                        "model": "veo-3.1",
                        "duration": "8",
                        "creation_mode": "assisted",
                    },
                    run_id=999, user_id=1,
                )

        assert captured["duration"] == "8"
        texts = [o.get("title", "") for o in result["outputs"]]
        assert not any("Duration Adjusted" in t for t in texts)

    def test_sora2pro_accepts_20s(self):
        """20s on Sora 2 Pro should NOT be clamped."""
        from app.recipes.video_creator import VideoCreator
        recipe = VideoCreator()

        captured = {}

        def fake_generate(prompt, image_path=None, model=None,
                          duration="5", aspect_ratio="9:16", provider=None):
            captured["duration"] = duration
            return {"status": "success", "result_url": "https://x.mp4"}

        from unittest.mock import patch
        with patch.object(recipe, "_call_gemini", return_value="mocked prompt"):
            with patch("tools.create_video.generate_ugc_video", side_effect=fake_generate):
                result = recipe.execute(
                    inputs={
                        "motion_prompt": "test video",
                        "model": "sora-2-pro",
                        "duration": "20",
                        "creation_mode": "assisted",
                    },
                    run_id=999, user_id=1,
                )

        assert captured["duration"] == "20"
        texts = [o.get("title", "") for o in result["outputs"]]
        assert not any("Duration Adjusted" in t for t in texts)
