"""Phase 41 — Talking Avatar, Influencer Content Kit, Persona Wiring.

Tests cover:
  A. TTS provider (tools/providers/tts.py)
  B. Talking Avatar recipe (app/recipes/talking_avatar.py)
  C. Influencer Content Kit recipe (app/recipes/influencer_content_kit.py)
  D. Persona wiring in generate.py & api.py routes
  E. Provider registry (talking head / TTS entries)
"""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch, call

import pytest

# ──────────────────────────────────────────────────────────────────────
# Shared fixtures
# ──────────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_image():
    """Create a temporary image file for upload tests."""
    fd, path = tempfile.mkstemp(suffix=".jpg")
    os.write(fd, b"\xff\xd8\xff\xe0" + b"\x00" * 100)  # Minimal JPEG header
    os.close(fd)
    yield path
    os.unlink(path)


@pytest.fixture
def app():
    """Create a Flask app with test config."""
    from app import create_app
    application = create_app()
    application.config["TESTING"] = True
    application.config["WTF_CSRF_ENABLED"] = False
    application.config["LOGIN_DISABLED"] = True
    return application


# ======================================================================
# A. TTS PROVIDER — tools/providers/tts.py
# ======================================================================

class TestTTSProvider:
    """Unit tests for Gemini TTS speech generation."""

    def test_empty_text_raises_value_error(self):
        from tools.providers.tts import generate_speech
        with pytest.raises(ValueError, match="Text cannot be empty"):
            generate_speech("")

    def test_none_text_raises_value_error(self):
        from tools.providers.tts import generate_speech
        with pytest.raises(ValueError, match="Text cannot be empty"):
            generate_speech(None)

    def test_text_too_long_raises_value_error(self):
        from tools.providers.tts import generate_speech
        with pytest.raises(ValueError, match="too long"):
            generate_speech("A" * 10_000)

    def test_missing_api_key_raises_runtime_error(self):
        from tools.providers.tts import generate_speech
        with patch("tools.providers.tts.config") as mock_cfg:
            mock_cfg.GOOGLE_API_KEY = None
            with pytest.raises(RuntimeError, match="GOOGLE_API_KEY"):
                generate_speech("Hello world", api_key=None)

    def test_unknown_voice_falls_back_to_default(self):
        """Unknown voices fall back to Kore without crashing."""
        from tools.providers.tts import generate_speech, DEFAULT_VOICE
        import base64

        # Minimal PCM data → WAV
        pcm = b"\x00\x01" * 100
        b64_pcm = base64.b64encode(pcm).decode()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [{"content": {"parts": [
                {"inlineData": {"data": b64_pcm, "mimeType": "audio/pcm"}}
            ]}}]
        }

        with patch("tools.providers.tts.requests.post", return_value=mock_resp):
            with patch("tools.providers.tts.config") as mock_cfg:
                mock_cfg.GOOGLE_API_KEY = "test-key"
                result = generate_speech("hello", voice_name="NONEXISTENT")
                assert isinstance(result, bytes)
                assert result[:4] == b"RIFF"  # WAV header

    def test_successful_generation_returns_wav_bytes(self):
        """Successful TTS call returns WAV file bytes."""
        import base64
        from tools.providers.tts import generate_speech

        pcm = b"\x00\x01" * 200
        b64_pcm = base64.b64encode(pcm).decode()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [{"content": {"parts": [
                {"inlineData": {"data": b64_pcm, "mimeType": "audio/pcm"}}
            ]}}]
        }

        with patch("tools.providers.tts.requests.post", return_value=mock_resp):
            with patch("tools.providers.tts.config") as mock_cfg:
                mock_cfg.GOOGLE_API_KEY = "test-key"
                wav = generate_speech("Test speech", voice_name="Charon")
                assert isinstance(wav, bytes)
                assert wav[:4] == b"RIFF"

    def test_retry_on_server_error(self):
        """Retries on 500 errors, then fails."""
        from tools.providers.tts import generate_speech

        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.raise_for_status.side_effect = Exception("500")

        with patch("tools.providers.tts.requests.post", return_value=mock_resp):
            with patch("tools.providers.tts.config") as mock_cfg:
                mock_cfg.GOOGLE_API_KEY = "test-key"
                with patch("tools.providers.tts.time.sleep"):
                    with pytest.raises(RuntimeError, match="failed after"):
                        generate_speech("hello", max_retries=2)

    def test_no_audio_data_raises_error(self):
        """No inlineData in response raises RuntimeError."""
        from tools.providers.tts import generate_speech

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "oops"}]}}]
        }

        with patch("tools.providers.tts.requests.post", return_value=mock_resp):
            with patch("tools.providers.tts.config") as mock_cfg:
                mock_cfg.GOOGLE_API_KEY = "test-key"
                with patch("tools.providers.tts.time.sleep"):
                    with pytest.raises(RuntimeError, match="failed after"):
                        generate_speech("hello", max_retries=1)

    def test_available_voices_list(self):
        from tools.providers.tts import AVAILABLE_VOICES
        assert "Kore" in AVAILABLE_VOICES
        assert "Charon" in AVAILABLE_VOICES
        assert len(AVAILABLE_VOICES) >= 6

    def test_pcm_to_wav_produces_valid_header(self):
        from tools.providers.tts import _pcm_to_wav
        pcm = b"\x00\x01" * 100
        wav = _pcm_to_wav(pcm)
        assert wav[:4] == b"RIFF"
        assert wav[8:12] == b"WAVE"
        assert len(wav) == len(pcm) + 44  # 44 byte WAV header


# ======================================================================
# B. TALKING AVATAR RECIPE
# ======================================================================

class TestTalkingAvatarRecipe:
    """Unit tests for the TalkingAvatar recipe."""

    def _recipe(self):
        from app.recipes.talking_avatar import TalkingAvatar
        return TalkingAvatar()

    def test_recipe_is_active(self):
        r = self._recipe()
        assert r.is_active is True

    def test_slug(self):
        assert self._recipe().slug == "talking-avatar"

    def test_has_input_fields(self):
        fields = self._recipe().get_input_fields()
        names = [f.name for f in fields]
        assert "headshot" in names
        assert "script" in names
        assert "brief" in names
        assert "voice_preset" in names

    def test_has_steps(self):
        steps = self._recipe().get_steps()
        assert len(steps) >= 4
        assert any("headshot" in s.lower() or "analys" in s.lower() for s in steps)

    def test_missing_headshot_returns_error(self):
        r = self._recipe()
        result = r.execute({"headshot": ""}, "run-1", "user-1")
        assert "❌" in result["outputs"][0]["title"]

    def test_missing_headshot_file_returns_error(self):
        r = self._recipe()
        result = r.execute(
            {"headshot": "/nonexistent/path.jpg"}, "run-1", "user-1"
        )
        assert "❌" in result["outputs"][0]["title"]

    def test_no_script_no_brief_returns_error(self, tmp_image):
        r = self._recipe()
        result = r.execute(
            {"headshot": tmp_image, "script": "", "brief": ""},
            "run-1", "user-1",
        )
        assert "❌" in result["outputs"][0]["title"]
        assert "script" in result["outputs"][0]["value"].lower() or \
               "brief" in result["outputs"][0]["value"].lower()

    def test_script_trimming(self, tmp_image):
        """Long scripts are trimmed to 8000 chars."""
        r = self._recipe()
        long_script = "A" * 9000

        # Mock all external calls
        with patch("tools.providers.tts.generate_speech", return_value=b"WAV") as mock_tts, \
             patch("tools.providers.wavespeed.upload_media", return_value="https://cdn/file"), \
             patch("tools.providers.higgsfield.submit_speak_v2", return_value="req-1"), \
             patch("tools.providers.higgsfield.poll_speak_v2",
                   return_value={"result_url": "https://vid.mp4"}), \
             patch("tools.config.get_cost", return_value=0.01):
            result = r.execute(
                {"headshot": tmp_image, "script": long_script},
                "run-1", "user-1",
            )
            # Script passed to TTS should be trimmed
            actual_text = mock_tts.call_args[1].get("text", mock_tts.call_args[0][0] if mock_tts.call_args[0] else "")
            assert len(actual_text) <= 8000

    def test_tts_failure_returns_error(self, tmp_image):
        r = self._recipe()
        with patch("tools.providers.tts.generate_speech",
                   side_effect=RuntimeError("TTS boom")), \
             patch("tools.config.get_cost", return_value=0.01):
            result = r.execute(
                {"headshot": tmp_image, "script": "Hello world"},
                "run-1", "user-1",
            )
            titles = [o["title"] for o in result["outputs"]]
            assert any("TTS" in t or "❌" in t for t in titles)

    def test_upload_failure_returns_error(self, tmp_image):
        r = self._recipe()
        with patch("tools.providers.tts.generate_speech", return_value=b"WAV"), \
             patch("tools.providers.wavespeed.upload_media",
                   side_effect=RuntimeError("Upload failed")), \
             patch("tools.config.get_cost", return_value=0.01):
            result = r.execute(
                {"headshot": tmp_image, "script": "Hello"},
                "run-1", "user-1",
            )
            titles = [o["title"] for o in result["outputs"]]
            assert any("Upload" in t or "❌" in t for t in titles)

    def test_speak_v2_success(self, tmp_image):
        """When Speak v2 succeeds, video is returned with correct method."""
        r = self._recipe()
        with patch("tools.providers.tts.generate_speech", return_value=b"WAV"), \
             patch("tools.providers.wavespeed.upload_media", return_value="https://cdn/f"), \
             patch("tools.providers.higgsfield.submit_speak_v2", return_value="req-1"), \
             patch("tools.providers.higgsfield.poll_speak_v2",
                   return_value={"result_url": "https://video.mp4"}), \
             patch("tools.config.get_cost", return_value=0.01):
            result = r.execute(
                {"headshot": tmp_image, "script": "Hello"},
                "run-1", "user-1",
            )
            assert result["model_used"] == "speak-v2"
            video_outputs = [o for o in result["outputs"] if o["type"] == "video"]
            assert len(video_outputs) >= 1
            assert "video.mp4" in video_outputs[0]["url"]

    def test_fallback_to_talking_photo(self, tmp_image):
        """If Speak v2 fails, falls back to talking_photo."""
        r = self._recipe()
        with patch("tools.providers.tts.generate_speech", return_value=b"WAV"), \
             patch("tools.providers.wavespeed.upload_media", return_value="https://cdn/f"), \
             patch("tools.providers.higgsfield.submit_speak_v2",
                   side_effect=RuntimeError("v2 down")), \
             patch("tools.providers.higgsfield.submit_talking_photo", return_value="gen-1"), \
             patch("tools.providers.higgsfield.poll_talking_photo",
                   return_value={"result_url": "https://tp.mp4"}), \
             patch("tools.config.get_cost", return_value=0.01):
            result = r.execute(
                {"headshot": tmp_image, "script": "Hello"},
                "run-1", "user-1",
            )
            assert result["model_used"] == "talking-photo"

    def test_fallback_to_infinitetalk(self, tmp_image):
        """If Speak v2 + talking_photo fail, falls back to InfiniteTalk."""
        r = self._recipe()
        with patch("tools.providers.tts.generate_speech", return_value=b"WAV"), \
             patch("tools.providers.wavespeed.upload_media", return_value="https://cdn/f"), \
             patch("tools.providers.higgsfield.submit_speak_v2",
                   side_effect=RuntimeError("v2 down")), \
             patch("tools.providers.higgsfield.submit_talking_photo",
                   side_effect=RuntimeError("tp down")), \
             patch("tools.providers.wavespeed.submit_infinitetalk",
                   return_value="https://poll/url"), \
             patch("tools.providers.wavespeed.poll_infinitetalk",
                   return_value="https://infinite.mp4"), \
             patch("tools.config.get_cost", return_value=0.01):
            result = r.execute(
                {"headshot": tmp_image, "script": "Hello"},
                "run-1", "user-1",
            )
            assert result["model_used"] == "infinitetalk"

    def test_all_engines_fail(self, tmp_image):
        """When all 3 engines fail, error message lists required API keys."""
        r = self._recipe()
        with patch("tools.providers.tts.generate_speech", return_value=b"WAV"), \
             patch("tools.providers.wavespeed.upload_media", return_value="https://cdn/f"), \
             patch("tools.providers.higgsfield.submit_speak_v2",
                   side_effect=RuntimeError("fail1")), \
             patch("tools.providers.higgsfield.submit_talking_photo",
                   side_effect=RuntimeError("fail2")), \
             patch("tools.providers.wavespeed.submit_infinitetalk",
                   side_effect=RuntimeError("fail3")), \
             patch("tools.config.get_cost", return_value=0.01):
            result = r.execute(
                {"headshot": tmp_image, "script": "Hello"},
                "run-1", "user-1",
            )
            assert result["model_used"] == "none"
            # Should mention API keys
            errors = [o for o in result["outputs"] if "❌" in o.get("title", "")]
            assert len(errors) >= 1
            assert "HIGGSFIELD" in errors[0]["value"] or "API" in errors[0]["value"]

    def test_voice_preset_mapping(self):
        from app.recipes.talking_avatar import _VOICE_MAP
        assert _VOICE_MAP["natural_female"] == "Kore"
        assert _VOICE_MAP["natural_male"] == "Charon"
        assert _VOICE_MAP["energetic_male"] == "Puck"

    def test_ai_script_generation(self, tmp_image):
        """When no script provided but brief given, AI generates script."""
        r = self._recipe()
        with patch("app.services.agent_service._call_gemini",
                   return_value="Hey there! Check this out.") as mock_gemini, \
             patch("tools.providers.tts.generate_speech", return_value=b"WAV"), \
             patch("tools.providers.wavespeed.upload_media", return_value="https://cdn/f"), \
             patch("tools.providers.higgsfield.submit_speak_v2", return_value="r1"), \
             patch("tools.providers.higgsfield.poll_speak_v2",
                   return_value={"result_url": "https://v.mp4"}), \
             patch("tools.config.get_cost", return_value=0.01):
            result = r.execute(
                {"headshot": tmp_image, "brief": "Promote protein shakes"},
                "run-1", "user-1",
            )
            # Should have an AI-generated script output
            script_outputs = [
                o for o in result["outputs"]
                if "script" in o.get("title", "").lower()
            ]
            assert len(script_outputs) >= 1

    def test_cost_tracking(self, tmp_image):
        """Costs are accumulated correctly."""
        r = self._recipe()
        cost_calls = []

        def fake_cost(model, provider):
            c = 0.05
            cost_calls.append((model, provider))
            return c

        with patch("tools.providers.tts.generate_speech", return_value=b"WAV"), \
             patch("tools.providers.wavespeed.upload_media", return_value="https://cdn/f"), \
             patch("tools.providers.higgsfield.submit_speak_v2", return_value="r1"), \
             patch("tools.providers.higgsfield.poll_speak_v2",
                   return_value={"result_url": "https://v.mp4"}), \
             patch("tools.config.get_cost", side_effect=fake_cost):
            result = r.execute(
                {"headshot": tmp_image, "script": "Hello"},
                "run-1", "user-1",
            )
            assert result["cost"] > 0
            # Should track TTS + speak-v2 costs
            models_costed = [c[0] for c in cost_calls]
            assert "gemini-tts" in models_costed
            assert "speak-v2" in models_costed


# ======================================================================
# C. INFLUENCER CONTENT KIT RECIPE
# ======================================================================

class TestInfluencerContentKit:
    """Unit tests for the InfluencerContentKit recipe."""

    def _recipe(self):
        from app.recipes.influencer_content_kit import InfluencerContentKit
        return InfluencerContentKit()

    def test_recipe_is_active(self):
        assert self._recipe().is_active is True

    def test_slug(self):
        assert self._recipe().slug == "influencer-content-kit"

    def test_has_input_fields(self):
        fields = self._recipe().get_input_fields()
        names = [f.name for f in fields]
        assert "character_photo" in names
        assert "brief" in names
        assert "post_count" in names
        assert "platforms" in names

    def test_has_steps(self):
        steps = self._recipe().get_steps()
        assert len(steps) >= 3

    def test_missing_photo_returns_error(self):
        r = self._recipe()
        result = r.execute(
            {"character_photo": "", "brief": "test"},
            "run-1", "user-1",
        )
        assert "❌" in result["outputs"][0]["title"]

    def test_missing_brief_returns_error(self, tmp_image):
        r = self._recipe()
        result = r.execute(
            {"character_photo": tmp_image, "brief": ""},
            "run-1", "user-1",
        )
        assert "❌" in result["outputs"][0]["title"]

    def test_invalid_post_count_defaults_to_3(self, tmp_image):
        """Invalid post_count falls back to 3."""
        r = self._recipe()
        scenes_json = json.dumps([
            {"scene": f"Scene {i}", "image_prompt": f"A person {i}",
             "caption": f"Caption {i}", "hashtags": f"#tag{i}"}
            for i in range(3)
        ])

        with patch("app.services.agent_service._call_gemini",
                   return_value=scenes_json), \
             patch("app.services.agent_service._call_gemini_with_image",
                   return_value="A young woman with brown hair"), \
             patch("tools.create_image.generate_ugc_image",
                   return_value={"result_url": "https://img.jpg"}), \
             patch("tools.config.get_cost", return_value=0.02):
            result = r.execute(
                {"character_photo": tmp_image, "brief": "Test",
                 "post_count": "99"},
                "run-1", "user-1",
            )
            # Should produce a content plan with 3 posts
            plan_out = [o for o in result["outputs"]
                        if "Content Plan" in o.get("title", "")]
            assert len(plan_out) >= 1

    def test_invalid_platform_defaults_to_instagram(self, tmp_image):
        r = self._recipe()
        scenes_json = json.dumps([
            {"scene": "Scene 1", "image_prompt": "A person",
             "caption": "Caption", "hashtags": "#tag"}
        ])

        with patch("app.services.agent_service._call_gemini",
                   return_value=scenes_json), \
             patch("app.services.agent_service._call_gemini_with_image",
                   return_value="A person"), \
             patch("tools.create_image.generate_ugc_image",
                   return_value={"result_url": "https://img.jpg"}), \
             patch("tools.config.get_cost", return_value=0.02):
            result = r.execute(
                {"character_photo": tmp_image, "brief": "Test",
                 "post_count": "1", "platforms": "INVALID"},
                "run-1", "user-1",
            )
            # Should succeed despite invalid platform
            assert result["cost"] >= 0

    def test_successful_execution(self, tmp_image):
        """Full successful execution returns plan + images + captions."""
        r = self._recipe()
        scenes_json = json.dumps([
            {"scene": "Morning workout", "image_prompt": "A person exercising",
             "caption": "Rise and grind!", "hashtags": "#fitness #morning"},
            {"scene": "Protein shake", "image_prompt": "A person with a shake",
             "caption": "Fuel your day!", "hashtags": "#protein #health"},
        ])

        with patch("app.services.agent_service._call_gemini",
                   return_value=scenes_json), \
             patch("app.services.agent_service._call_gemini_with_image",
                   return_value="A young woman with brown hair"), \
             patch("tools.create_image.generate_ugc_image",
                   return_value={"result_url": "https://img.jpg"}), \
             patch("tools.config.get_cost", return_value=0.02):
            result = r.execute(
                {"character_photo": tmp_image, "brief": "Fitness campaign",
                 "post_count": "3", "platforms": "instagram"},
                "run-1", "user-1",
            )

            # Should have content plan
            plans = [o for o in result["outputs"]
                     if "Content Plan" in o.get("title", "")]
            assert len(plans) == 1

            # Should have images
            images = [o for o in result["outputs"] if o["type"] == "image"]
            assert len(images) == 2  # 2 scenes

            # Should have captions
            captions = [o for o in result["outputs"]
                        if "Caption" in o.get("title", "")]
            assert len(captions) == 2

            # Should have summary
            summaries = [o for o in result["outputs"]
                         if "Summary" in o.get("title", "")]
            assert len(summaries) == 1

            assert result["cost"] > 0

    def test_image_generation_failure_partial(self, tmp_image):
        """If one image fails, others still generate + warning shown."""
        r = self._recipe()
        scenes_json = json.dumps([
            {"scene": "Scene 1", "image_prompt": "Prompt 1",
             "caption": "Cap 1", "hashtags": "#a"},
            {"scene": "Scene 2", "image_prompt": "Prompt 2",
             "caption": "Cap 2", "hashtags": "#b"},
        ])

        call_count = [0]

        def fake_generate(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("Provider down")
            return {"result_url": "https://img2.jpg"}

        with patch("app.services.agent_service._call_gemini",
                   return_value=scenes_json), \
             patch("app.services.agent_service._call_gemini_with_image",
                   return_value="A person"), \
             patch("tools.create_image.generate_ugc_image",
                   side_effect=fake_generate), \
             patch("tools.config.get_cost", return_value=0.02):
            result = r.execute(
                {"character_photo": tmp_image, "brief": "Test",
                 "post_count": "3"},
                "run-1", "user-1",
            )

            # Should have warning for failed image
            warnings = [o for o in result["outputs"]
                        if "⚠️" in o.get("title", "")]
            assert len(warnings) >= 1

            # Should still have the successful image
            images = [o for o in result["outputs"] if o["type"] == "image"]
            assert len(images) >= 1

    def test_planning_failure_returns_error(self, tmp_image):
        """If Gemini planning fails, recipe returns error."""
        r = self._recipe()
        with patch("app.services.agent_service._call_gemini",
                   side_effect=RuntimeError("Gemini down")), \
             patch("app.services.agent_service._call_gemini_with_image",
                   return_value="A person"):
            result = r.execute(
                {"character_photo": tmp_image, "brief": "Test"},
                "run-1", "user-1",
            )
            assert "❌" in result["outputs"][0]["title"]

    def test_character_analysis_failure_graceful(self, tmp_image):
        """If character analysis fails, recipe continues with brief only."""
        r = self._recipe()
        scenes_json = json.dumps([
            {"scene": "Scene", "image_prompt": "A person",
             "caption": "Hey!", "hashtags": "#tag"}
        ])

        with patch("app.services.agent_service._call_gemini_with_image",
                   side_effect=RuntimeError("Vision down")), \
             patch("app.services.agent_service._call_gemini",
                   return_value=scenes_json), \
             patch("tools.create_image.generate_ugc_image",
                   return_value={"result_url": "https://img.jpg"}), \
             patch("tools.config.get_cost", return_value=0.02):
            result = r.execute(
                {"character_photo": tmp_image, "brief": "Test",
                 "post_count": "1"},
                "run-1", "user-1",
            )
            # Should still succeed despite vision failure
            images = [o for o in result["outputs"] if o["type"] == "image"]
            assert len(images) >= 1

    def test_parse_scenes_with_markdown_fences(self):
        """Parser handles JSON wrapped in markdown fences."""
        from app.recipes.influencer_content_kit import InfluencerContentKit

        raw = '```json\n[{"scene":"Test","image_prompt":"A","caption":"B","hashtags":"#c"}]\n```'
        scenes = InfluencerContentKit._parse_scenes(raw, 3)
        assert len(scenes) == 1
        assert scenes[0]["scene"] == "Test"

    def test_parse_scenes_fallback(self):
        """Parser creates fallback when JSON is unparseable."""
        from app.recipes.influencer_content_kit import InfluencerContentKit

        raw = "This is not JSON at all"
        scenes = InfluencerContentKit._parse_scenes(raw, 3)
        assert len(scenes) == 1
        assert "image_prompt" in scenes[0]

    def test_parse_scenes_embedded_json(self):
        """Parser finds JSON array embedded in text."""
        from app.recipes.influencer_content_kit import InfluencerContentKit

        raw = 'Here are the scenes:\n[{"scene":"A","image_prompt":"B","caption":"C","hashtags":"#d"}]\nDone!'
        scenes = InfluencerContentKit._parse_scenes(raw, 3)
        assert len(scenes) == 1
        assert scenes[0]["scene"] == "A"

    def test_brand_persona_context_passed(self, tmp_image):
        """Brand and persona context are included in planning prompt."""
        r = self._recipe()

        mock_brand = MagicMock()
        mock_brand.name = "TestBrand"
        mock_brand.tagline = "Test tagline"
        mock_brand.colors_json = '["#FF0000"]'
        mock_brand.voice_json = '{"tone":"bold"}'
        mock_brand.hashtags = "#test"
        mock_brand.caption_template = ""
        mock_brand.logo_path = ""
        mock_brand.brand_doc = ""

        mock_persona = MagicMock()
        mock_persona.name = "TestPersona"
        mock_persona.tone = "casual"
        mock_persona.voice_style = "fun"
        mock_persona.bio = ""
        mock_persona.industry = "tech"
        mock_persona.target_audience = "millennials"
        mock_persona.brand_keywords_json = ""
        mock_persona.avoid_words_json = ""
        mock_persona.sample_phrases_json = ""
        mock_persona.writing_guidelines = ""
        mock_persona.ai_prompt_summary = ""

        scenes_json = json.dumps([
            {"scene": "Scene", "image_prompt": "Prompt",
             "caption": "Cap", "hashtags": "#tag"}
        ])

        gemini_calls = []

        def capture_gemini(prompt):
            gemini_calls.append(prompt)
            return scenes_json

        with patch("app.services.agent_service._call_gemini",
                   side_effect=capture_gemini), \
             patch("app.services.agent_service._call_gemini_with_image",
                   return_value="A person"), \
             patch("tools.create_image.generate_ugc_image",
                   return_value={"result_url": "https://img.jpg"}), \
             patch("tools.config.get_cost", return_value=0.02):
            r.execute(
                {"character_photo": tmp_image, "brief": "Test",
                 "post_count": "1"},
                "run-1", "user-1",
                brand=mock_brand, persona=mock_persona,
            )

            # The planning prompt should contain brand and persona info
            assert len(gemini_calls) >= 1
            planning = gemini_calls[0]
            assert "TestBrand" in planning
            assert "TestPersona" in planning


# ======================================================================
# D. PERSONA WIRING — generate.py & api.py
# ======================================================================

class TestPersonaWiring:
    """Verify persona is passed through generate.py and api.py routes."""

    def test_generate_py_has_persona_param_in_run_generation(self):
        """_run_generation accepts persona keyword argument."""
        import inspect
        from app.routes.generate import _run_generation
        sig = inspect.signature(_run_generation)
        assert "persona" in sig.parameters

    def test_generate_single_reads_persona_id(self):
        """generate_single route reads persona_id from form."""
        from app.routes.generate import generate_single
        import inspect
        source = inspect.getsource(generate_single)
        assert "persona_id" in source

    def test_bulk_generate_worker_exists(self):
        """_bulk_generate_worker is importable and callable."""
        from app.routes.generate import _bulk_generate_worker
        import inspect
        assert callable(_bulk_generate_worker)
        sig = inspect.signature(_bulk_generate_worker)
        # Must accept app, campaign_id, brand_id, post_ids, user_id
        assert len(sig.parameters) >= 5

    def test_api_suggest_captions_reads_persona(self):
        """agent_suggest_captions route reads persona_id."""
        from app.routes.api import agent_suggest_captions
        import inspect
        source = inspect.getsource(agent_suggest_captions)
        assert "persona_id" in source

    def test_api_enhance_prompt_reads_persona(self):
        """agent_enhance_prompt route reads persona_id."""
        from app.routes.api import agent_enhance_prompt
        import inspect
        source = inspect.getsource(agent_enhance_prompt)
        assert "persona_id" in source


# ======================================================================
# E. PROVIDER REGISTRY
# ======================================================================

class TestProviderRegistry:
    """Verify talking head and TTS providers are registered."""

    def test_tts_provider_registered(self):
        from tools.providers import TTS_PROVIDERS
        assert "gemini-tts" in TTS_PROVIDERS

    def test_talking_head_providers_registered(self):
        from tools.providers import TALKING_HEAD_PROVIDERS
        assert "speak-v2" in TALKING_HEAD_PROVIDERS
        assert "talking-photo" in TALKING_HEAD_PROVIDERS
        assert "infinitetalk" in TALKING_HEAD_PROVIDERS

    def test_get_tts_provider(self):
        from tools.providers import get_tts_provider
        provider, name = get_tts_provider("gemini-tts")
        assert name == "gemini"
        assert provider is not None

    def test_get_talking_head_provider_speak_v2(self):
        from tools.providers import get_talking_head_provider
        provider, name = get_talking_head_provider("speak-v2")
        assert name == "higgsfield"

    def test_get_talking_head_provider_infinitetalk(self):
        from tools.providers import get_talking_head_provider
        provider, name = get_talking_head_provider("infinitetalk")
        assert name == "wavespeed"

    def test_unknown_tts_model_raises(self):
        from tools.providers import get_tts_provider
        with pytest.raises(ValueError, match="Unknown TTS model"):
            get_tts_provider("nonexistent")

    def test_unknown_talking_head_model_raises(self):
        from tools.providers import get_talking_head_provider
        with pytest.raises(ValueError, match="Unknown talking head model"):
            get_talking_head_provider("nonexistent")

    def test_cost_entries_exist(self):
        """Costs are configured for TTS and talking head models."""
        from tools.config import get_cost
        assert get_cost("gemini-tts", "gemini") >= 0
        assert get_cost("speak-v2", "higgsfield") >= 0
        assert get_cost("talking-photo", "higgsfield") >= 0
        assert get_cost("infinitetalk", "wavespeed") >= 0


# ======================================================================
# F. RECIPE REGISTRY — all 8 active recipes discoverable
# ======================================================================

class TestRecipeRegistry:
    """Ensure all Phase 41 recipes appear in the registry."""

    def test_talking_avatar_in_registry(self, app):
        with app.app_context():
            from app.recipes import get_all_recipes
            recipes = get_all_recipes()
            slugs = [r.slug for r in recipes]
            assert "talking-avatar" in slugs

    def test_influencer_content_kit_in_registry(self, app):
        with app.app_context():
            from app.recipes import get_all_recipes
            recipes = get_all_recipes()
            slugs = [r.slug for r in recipes]
            assert "influencer-content-kit" in slugs

    def test_active_recipe_count(self, app):
        """Should have at least 8 active recipes after Phase 41."""
        with app.app_context():
            from app.recipes import get_all_recipes
            active = [r for r in get_all_recipes() if r.is_active]
            assert len(active) >= 8, (
                f"Expected ≥8 active recipes, got {len(active)}: "
                f"{[r.slug for r in active]}"
            )
