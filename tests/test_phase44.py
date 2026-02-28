"""Phase 44 — Talking Avatar B-Roll Pipeline unit tests.

Tests cover:
  - Style reference analysis (Gemini Vision)
  - SEALCaM B-roll prompt generation
  - B-roll image generation
  - B-roll video generation
  - Full B-roll pipeline orchestration
  - Input field additions
  - Step count updates
  - Edge cases (missing files, API failures, partial failures)
"""

import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from app import create_app
from app.recipes.talking_avatar import TalkingAvatar, _VOICE_MAP


class TestTalkingAvatarInputFields(unittest.TestCase):
    """Verify new B-roll input fields are present."""

    def setUp(self):
        self.recipe = TalkingAvatar()

    def test_has_style_reference_field(self):
        names = [f.name for f in self.recipe.get_input_fields()]
        self.assertIn("style_reference", names)

    def test_style_reference_is_optional(self):
        field = next(f for f in self.recipe.get_input_fields()
                     if f.name == "style_reference")
        self.assertFalse(field.required)
        self.assertEqual(field.field_type, "file")
        self.assertEqual(field.accept, "image/*")

    def test_has_generate_broll_field(self):
        names = [f.name for f in self.recipe.get_input_fields()]
        self.assertIn("generate_broll", names)

    def test_generate_broll_defaults_to_no(self):
        field = next(f for f in self.recipe.get_input_fields()
                     if f.name == "generate_broll")
        self.assertEqual(field.default, "no")
        values = [o["value"] for o in field.options]
        self.assertIn("yes", values)
        self.assertIn("no", values)

    def test_has_broll_count_field(self):
        names = [f.name for f in self.recipe.get_input_fields()]
        self.assertIn("broll_count", names)

    def test_broll_count_options(self):
        field = next(f for f in self.recipe.get_input_fields()
                     if f.name == "broll_count")
        values = [o["value"] for o in field.options]
        self.assertIn("2", values)
        self.assertIn("3", values)
        self.assertIn("4", values)
        self.assertEqual(field.default, "3")

    def test_total_input_count(self):
        """Should have 7 input fields (headshot, script, brief, voice, style_ref,
        generate_broll, broll_count)."""
        fields = self.recipe.get_input_fields()
        self.assertEqual(len(fields), 7)


class TestTalkingAvatarSteps(unittest.TestCase):
    """Verify step list includes B-roll stages."""

    def setUp(self):
        self.recipe = TalkingAvatar()

    def test_step_count(self):
        """Should have 9 steps (0–8)."""
        steps = self.recipe.get_steps()
        self.assertEqual(len(steps), 9)

    def test_broll_steps_present(self):
        steps = self.recipe.get_steps()
        step_text = " ".join(steps).lower()
        self.assertIn("style reference", step_text)
        self.assertIn("b-roll prompts", step_text)
        self.assertIn("b-roll images", step_text)
        self.assertIn("b-roll videos", step_text)

    def test_finalising_is_last(self):
        steps = self.recipe.get_steps()
        self.assertEqual(steps[-1], "Finalising")


class TestStyleReferenceAnalysis(unittest.TestCase):
    """Test _analyse_style_reference helper."""

    def setUp(self):
        self.recipe = TalkingAvatar()

    def test_no_path_returns_default(self):
        result = self.recipe._analyse_style_reference("")
        self.assertIn("No reference image", result)

    def test_none_path_returns_default(self):
        result = self.recipe._analyse_style_reference(None)
        self.assertIn("No reference image", result)

    def test_missing_file_returns_default(self):
        result = self.recipe._analyse_style_reference("/tmp/nonexistent_xyz.jpg")
        self.assertIn("No reference image", result)

    @patch("app.services.agent_service._call_gemini_with_image")
    def test_successful_analysis(self, mock_vision):
        mock_vision.return_value = "Warm tones, soft bokeh, cinematic look."

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
            tmp = f.name

        try:
            result = self.recipe._analyse_style_reference(tmp)
            self.assertEqual(result, "Warm tones, soft bokeh, cinematic look.")
            mock_vision.assert_called_once()
        finally:
            os.unlink(tmp)

    @patch("app.services.agent_service._call_gemini_with_image",
           side_effect=RuntimeError("Vision API down"))
    def test_vision_failure_returns_default(self, _mock):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"\x89PNG" + b"\x00" * 100)
            tmp = f.name

        try:
            result = self.recipe._analyse_style_reference(tmp)
            self.assertIn("No reference image", result)
        finally:
            os.unlink(tmp)


class TestBrollPromptGeneration(unittest.TestCase):
    """Test _generate_broll_prompts helper."""

    def setUp(self):
        self.recipe = TalkingAvatar()
        self.app = create_app("testing")

    _MOCK_BROLL_JSON = json.dumps({
        "segments": [
            {
                "segment_number": 1,
                "segment_name": "Product Reveal",
                "image_prompt": "Subject: Skincare bottle\nEnvironment: Marble surface",
                "video_prompt": "Subject: Skincare bottle\nAction: slow rotation",
            },
            {
                "segment_number": 2,
                "segment_name": "Lifestyle Shot",
                "image_prompt": "Subject: Woman applying cream\nEnvironment: Bathroom",
                "video_prompt": "Subject: Woman\nAction: gentle movement",
            },
            {
                "segment_number": 3,
                "segment_name": "Close-up Detail",
                "image_prompt": "Subject: Product texture\nEnvironment: Clean surface",
                "video_prompt": "Subject: Texture\nAction: macro zoom",
            },
        ]
    })

    @patch("app.services.agent_service._call_gemini",
           return_value=_MOCK_BROLL_JSON)
    def test_generates_correct_count(self, _mock):
        with self.app.app_context():
            prompts = self.recipe._generate_broll_prompts(
                "Hello world", "Modern style", 3,
            )
        self.assertEqual(len(prompts), 3)

    @patch("app.services.agent_service._call_gemini",
           return_value=_MOCK_BROLL_JSON)
    def test_respects_count_limit(self, _mock):
        with self.app.app_context():
            prompts = self.recipe._generate_broll_prompts(
                "Hello world", "Modern style", 2,
            )
        self.assertEqual(len(prompts), 2)

    @patch("app.services.agent_service._call_gemini",
           return_value=_MOCK_BROLL_JSON)
    def test_segments_have_required_keys(self, _mock):
        with self.app.app_context():
            prompts = self.recipe._generate_broll_prompts(
                "Hello world", "Modern style", 3,
            )
        for p in prompts:
            self.assertIn("segment_name", p)
            self.assertIn("image_prompt", p)
            self.assertIn("video_prompt", p)

    @patch("app.services.agent_service._call_gemini",
           return_value="```json\n" + _MOCK_BROLL_JSON + "\n```")
    def test_strips_markdown_fences(self, _mock):
        with self.app.app_context():
            prompts = self.recipe._generate_broll_prompts(
                "Hello world", "Modern style", 3,
            )
        self.assertEqual(len(prompts), 3)

    @patch("app.services.agent_service._call_gemini",
           side_effect=RuntimeError("API down"))
    def test_api_failure_returns_empty(self, _mock):
        with self.app.app_context():
            prompts = self.recipe._generate_broll_prompts(
                "Hello world", "Modern style", 3,
            )
        self.assertEqual(prompts, [])

    @patch("app.services.agent_service._call_gemini",
           return_value="not valid json at all")
    def test_invalid_json_returns_empty(self, _mock):
        with self.app.app_context():
            prompts = self.recipe._generate_broll_prompts(
                "Hello world", "Modern style", 3,
            )
        self.assertEqual(prompts, [])

    @patch("app.services.agent_service._call_gemini",
           return_value=_MOCK_BROLL_JSON)
    def test_brand_context_in_prompt(self, mock_gemini):
        """Brand context should be included in the Gemini prompt."""
        with self.app.app_context():
            brand = MagicMock()
            brand.name = "TestBrand"
            brand.tagline = "Great stuff"
            brand.visual_style = "Bold"
            brand.target_audience = "Millennials"
            brand.content_pillars = []
            brand.never_do = ""
            brand.colors = ["#FF0000"]
            brand.voice = "Friendly"
            brand.colors_json = None
            brand.voice_json = None
            brand.hashtags = ""
            brand.caption_template = ""
            brand.logo_path = ""
            brand.brand_doc = ""

            self.recipe._generate_broll_prompts(
                "Hello world", "Modern style", 3, brand=brand,
            )

        call_args = mock_gemini.call_args[0][0]
        self.assertIn("TestBrand", call_args)


class TestBrollImageGeneration(unittest.TestCase):
    """Test _generate_broll_images helper."""

    def setUp(self):
        self.recipe = TalkingAvatar()
        self.prompts = [
            {
                "segment_number": 1,
                "segment_name": "Product Reveal",
                "image_prompt": "Subject: Skincare bottle\nEnvironment: Marble",
                "video_prompt": "Subject: Skincare bottle\nAction: rotation",
            },
            {
                "segment_number": 2,
                "segment_name": "Lifestyle Shot",
                "image_prompt": "Subject: Woman\nEnvironment: Bathroom",
                "video_prompt": "Subject: Woman\nAction: movement",
            },
        ]

    @patch("tools.create_image.generate_ugc_image")
    @patch("tools.config.get_cost", return_value=0.13)
    def test_generates_images_for_each_prompt(self, _cost, mock_gen):
        mock_gen.return_value = {"status": "completed", "result_url": "https://cdn.example.com/img1.png"}

        results = self.recipe._generate_broll_images(self.prompts)
        self.assertEqual(len(results), 2)
        self.assertEqual(mock_gen.call_count, 2)

    @patch("tools.create_image.generate_ugc_image")
    @patch("tools.config.get_cost", return_value=0.13)
    def test_result_contains_name_and_url(self, _cost, mock_gen):
        mock_gen.return_value = {"status": "completed", "result_url": "https://cdn.example.com/img.png"}

        results = self.recipe._generate_broll_images(self.prompts)
        self.assertEqual(results[0]["name"], "Product Reveal")
        self.assertEqual(results[0]["url"], "https://cdn.example.com/img.png")
        self.assertEqual(results[0]["cost"], 0.13)

    @patch("tools.create_image.generate_ugc_image")
    @patch("tools.config.get_cost", return_value=0.13)
    def test_passes_style_reference_as_ref_path(self, _cost, mock_gen):
        mock_gen.return_value = {"status": "completed", "result_url": "https://cdn.example.com/img.png"}

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"\xff\xd8\xff\xe0" + b"\x00" * 50)
            tmp = f.name

        try:
            self.recipe._generate_broll_images(self.prompts, style_ref_path=tmp)
            # First call — check keyword args contain reference_paths
            _, kwargs = mock_gen.call_args_list[0]
            ref = kwargs.get("reference_paths")
            self.assertIsNotNone(ref)
            self.assertIn(tmp, ref)
        finally:
            os.unlink(tmp)

    @patch("tools.create_image.generate_ugc_image",
           side_effect=RuntimeError("Provider down"))
    @patch("tools.config.get_cost", return_value=0.13)
    def test_one_failure_does_not_block_others(self, _cost, mock_gen):
        """If first image fails, second should still be attempted."""
        # Make first fail, second succeed
        mock_gen.side_effect = [
            RuntimeError("Provider down"),
            {"status": "completed", "result_url": "https://cdn.example.com/img2.png"},
        ]
        results = self.recipe._generate_broll_images(self.prompts)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Lifestyle Shot")

    @patch("tools.create_image.generate_ugc_image")
    @patch("tools.config.get_cost", return_value=0.13)
    def test_skips_empty_prompt(self, _cost, mock_gen):
        mock_gen.return_value = {"status": "completed", "result_url": "https://cdn.example.com/img.png"}
        prompts_with_empty = [
            {"segment_name": "A", "image_prompt": "", "video_prompt": "x"},
            {"segment_name": "B", "image_prompt": "Subject: X", "video_prompt": "y"},
        ]
        results = self.recipe._generate_broll_images(prompts_with_empty)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "B")

    @patch("tools.create_image.generate_ugc_image")
    @patch("tools.config.get_cost", return_value=0.13)
    def test_no_url_in_result_skipped(self, _cost, mock_gen):
        mock_gen.return_value = {"status": "completed", "result_url": ""}
        results = self.recipe._generate_broll_images(self.prompts)
        self.assertEqual(len(results), 0)


class TestBrollVideoGeneration(unittest.TestCase):
    """Test _generate_broll_videos helper."""

    def setUp(self):
        self.recipe = TalkingAvatar()
        self.prompts = [
            {"segment_name": "Reveal", "image_prompt": "X", "video_prompt": "rotation"},
            {"segment_name": "Lifestyle", "image_prompt": "Y", "video_prompt": "movement"},
        ]
        self.images = [
            {"name": "Reveal", "url": "https://cdn.example.com/img1.png",
             "cost": 0.13, "segment": self.prompts[0]},
            {"name": "Lifestyle", "url": "https://cdn.example.com/img2.png",
             "cost": 0.13, "segment": self.prompts[1]},
        ]

    @patch("tools.create_video.generate_ugc_video")
    @patch("tools.config.get_cost", return_value=0.30)
    def test_generates_video_for_each_image(self, _cost, mock_gen):
        mock_gen.return_value = {"status": "completed", "result_url": "https://cdn.example.com/vid1.mp4"}
        results = self.recipe._generate_broll_videos(self.images, self.prompts)
        self.assertEqual(len(results), 2)
        self.assertEqual(mock_gen.call_count, 2)

    @patch("tools.create_video.generate_ugc_video")
    @patch("tools.config.get_cost", return_value=0.30)
    def test_result_has_correct_fields(self, _cost, mock_gen):
        mock_gen.return_value = {"status": "completed", "result_url": "https://cdn.example.com/vid.mp4"}
        results = self.recipe._generate_broll_videos(self.images, self.prompts)
        self.assertEqual(results[0]["name"], "Reveal")
        self.assertEqual(results[0]["url"], "https://cdn.example.com/vid.mp4")
        self.assertEqual(results[0]["cost"], 0.30)

    @patch("tools.create_video.generate_ugc_video")
    @patch("tools.config.get_cost", return_value=0.30)
    def test_uses_kling_model_and_short_duration(self, _cost, mock_gen):
        mock_gen.return_value = {"status": "completed", "result_url": "https://cdn.example.com/vid.mp4"}
        self.recipe._generate_broll_videos(self.images, self.prompts)
        call_kwargs = mock_gen.call_args[1]
        self.assertEqual(call_kwargs.get("model"), "kling-3.0")
        self.assertEqual(call_kwargs.get("duration"), "5")
        self.assertEqual(call_kwargs.get("aspect_ratio"), "16:9")

    @patch("tools.create_video.generate_ugc_video",
           side_effect=RuntimeError("Timeout"))
    @patch("tools.config.get_cost", return_value=0.30)
    def test_failure_does_not_block_others(self, _cost, mock_gen):
        mock_gen.side_effect = [
            RuntimeError("Timeout"),
            {"status": "completed", "result_url": "https://cdn.example.com/vid2.mp4"},
        ]
        results = self.recipe._generate_broll_videos(self.images, self.prompts)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Lifestyle")

    @patch("tools.create_video.generate_ugc_video")
    @patch("tools.config.get_cost", return_value=0.30)
    def test_skips_image_with_no_video_prompt(self, _cost, mock_gen):
        mock_gen.return_value = {"status": "completed", "result_url": "https://cdn.example.com/v.mp4"}
        images_no_prompt = [
            {"name": "A", "url": "https://cdn.example.com/a.png",
             "segment": {"video_prompt": ""}},
            {"name": "B", "url": "https://cdn.example.com/b.png",
             "segment": {"video_prompt": "Some motion"}},
        ]
        results = self.recipe._generate_broll_videos(images_no_prompt, [])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "B")


class TestBrollPipelineOrchestration(unittest.TestCase):
    """Test _run_broll_pipeline and full execute with B-roll enabled."""

    def setUp(self):
        self.recipe = TalkingAvatar()
        self.app = create_app("testing")

    @patch.object(TalkingAvatar, "_generate_broll_videos")
    @patch.object(TalkingAvatar, "_generate_broll_images")
    @patch.object(TalkingAvatar, "_generate_broll_prompts")
    @patch.object(TalkingAvatar, "_analyse_style_reference")
    def test_pipeline_returns_outputs_and_cost(
        self, mock_analyse, mock_prompts, mock_images, mock_videos,
    ):
        mock_analyse.return_value = "Cinematic warm tones."
        mock_prompts.return_value = [
            {"segment_name": "Clip 1", "image_prompt": "X", "video_prompt": "Y"},
        ]
        mock_images.return_value = [
            {"name": "Clip 1", "url": "https://cdn.example.com/img.png",
             "cost": 0.13, "segment": mock_prompts.return_value[0]},
        ]
        mock_videos.return_value = [
            {"name": "Clip 1", "url": "https://cdn.example.com/vid.mp4",
             "cost": 0.30},
        ]

        with self.app.app_context():
            outputs, cost = self.recipe._run_broll_pipeline(
                script="Hello world",
                style_ref_path="",
                headshot_path="",
                broll_count=3,
                brand=None,
                persona=None,
                on_progress=None,
            )

        # Should have: style analysis, prompts, 1 image, 1 video = 4 outputs
        self.assertEqual(len(outputs), 4)
        self.assertAlmostEqual(cost, 0.43, places=2)

    @patch.object(TalkingAvatar, "_generate_broll_prompts", return_value=[])
    @patch.object(TalkingAvatar, "_analyse_style_reference",
                  return_value="Default style.")
    def test_pipeline_skips_when_no_prompts(self, _analyse, _prompts):
        with self.app.app_context():
            outputs, cost = self.recipe._run_broll_pipeline(
                script="Hello", style_ref_path="", headshot_path="",
                broll_count=3, brand=None, persona=None, on_progress=None,
            )

        # Should have: style analysis + warning = 2 outputs
        self.assertEqual(len(outputs), 2)
        titles = [o["title"] for o in outputs]
        self.assertTrue(any("⚠️" in t for t in titles))
        self.assertEqual(cost, 0.0)

    @patch.object(TalkingAvatar, "_generate_broll_images", return_value=[])
    @patch.object(TalkingAvatar, "_generate_broll_prompts")
    @patch.object(TalkingAvatar, "_analyse_style_reference",
                  return_value="Style.")
    def test_pipeline_skips_videos_when_no_images(
        self, _analyse, mock_prompts, _images,
    ):
        mock_prompts.return_value = [
            {"segment_name": "A", "image_prompt": "X", "video_prompt": "Y"},
        ]
        with self.app.app_context():
            outputs, cost = self.recipe._run_broll_pipeline(
                script="Hello", style_ref_path="", headshot_path="",
                broll_count=3, brand=None, persona=None, on_progress=None,
            )

        titles = [o["title"] for o in outputs]
        self.assertTrue(any("⚠️ B-Roll Images" in t for t in titles))
        self.assertEqual(cost, 0.0)


class TestFullExecuteWithBroll(unittest.TestCase):
    """Test the full execute method with B-roll enabled."""

    def setUp(self):
        self.recipe = TalkingAvatar()
        self.app = create_app("testing")

    @patch.object(TalkingAvatar, "_run_broll_pipeline")
    @patch("tools.providers.higgsfield.submit_speak_v2", return_value="req-123")
    @patch("tools.providers.higgsfield.poll_speak_v2",
           return_value={"result_url": "https://cdn.example.com/talking.mp4"})
    @patch("tools.providers.wavespeed.upload_media",
           return_value="https://cdn.example.com/uploaded")
    @patch("tools.providers.tts.generate_speech", return_value=b"WAV_DATA")
    @patch("tools.config.get_cost", return_value=0.15)
    def test_broll_enabled_calls_pipeline(
        self, _cost, _tts, _upload, _poll, _submit, mock_broll,
    ):
        mock_broll.return_value = (
            [{"type": "text", "title": "🎨 Style", "value": "test"}],
            0.43,
        )

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
            headshot = f.name

        try:
            with self.app.app_context():
                result = self.recipe.execute(
                    {
                        "headshot": headshot,
                        "script": "Hello world test script.",
                        "voice_preset": "natural_female",
                        "generate_broll": "yes",
                        "broll_count": "3",
                    },
                    run_id=1, user_id=1,
                )
        finally:
            os.unlink(headshot)

        mock_broll.assert_called_once()
        # Cost should include TTS + speak-v2 + broll
        self.assertGreater(result["cost"], 0)

    @patch("tools.providers.higgsfield.submit_speak_v2", return_value="req-123")
    @patch("tools.providers.higgsfield.poll_speak_v2",
           return_value={"result_url": "https://cdn.example.com/talking.mp4"})
    @patch("tools.providers.wavespeed.upload_media",
           return_value="https://cdn.example.com/uploaded")
    @patch("tools.providers.tts.generate_speech", return_value=b"WAV_DATA")
    @patch("tools.config.get_cost", return_value=0.15)
    def test_broll_disabled_skips_pipeline(
        self, _cost, _tts, _upload, _poll, _submit,
    ):
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
            headshot = f.name

        try:
            with self.app.app_context():
                result = self.recipe.execute(
                    {
                        "headshot": headshot,
                        "script": "Hello world test script.",
                        "voice_preset": "natural_female",
                        "generate_broll": "no",
                    },
                    run_id=1, user_id=1,
                )
        finally:
            os.unlink(headshot)

        # Should NOT have any B-Roll outputs
        titles = [o.get("title", "") for o in result["outputs"]]
        broll_titles = [t for t in titles if "B-Roll" in t]
        self.assertEqual(len(broll_titles), 0)

    @patch("tools.providers.higgsfield.submit_speak_v2", return_value="req-123")
    @patch("tools.providers.higgsfield.poll_speak_v2",
           return_value={"result_url": "https://cdn.example.com/talking.mp4"})
    @patch("tools.providers.wavespeed.upload_media",
           return_value="https://cdn.example.com/uploaded")
    @patch("tools.providers.tts.generate_speech", return_value=b"WAV_DATA")
    @patch("tools.config.get_cost", return_value=0.15)
    def test_summary_includes_broll_counts(
        self, _cost, _tts, _upload, _poll, _submit,
    ):
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
            headshot = f.name

        try:
            with self.app.app_context():
                result = self.recipe.execute(
                    {
                        "headshot": headshot,
                        "script": "Hello world test script.",
                        "voice_preset": "natural_female",
                        "generate_broll": "no",
                    },
                    run_id=1, user_id=1,
                )
        finally:
            os.unlink(headshot)

        summary = next(
            o for o in result["outputs"]
            if o.get("title", "").startswith("📊")
        )
        self.assertIn("B-Roll images", summary["value"])
        self.assertIn("B-Roll videos", summary["value"])


class TestMetadata(unittest.TestCase):
    """Test recipe metadata is correct."""

    def test_estimated_cost_mentions_broll(self):
        recipe = TalkingAvatar()
        self.assertIn("B-roll", recipe.estimated_cost)

    def test_description_mentions_broll(self):
        recipe = TalkingAvatar()
        self.assertIn("B-roll", recipe.description)

    def test_how_to_use_mentions_style_reference(self):
        recipe = TalkingAvatar()
        self.assertIn("style-reference", recipe.how_to_use)

    def test_how_to_use_mentions_sealcam(self):
        recipe = TalkingAvatar()
        self.assertIn("SEALCaM", recipe.how_to_use)

    def test_is_active(self):
        recipe = TalkingAvatar()
        self.assertTrue(recipe.is_active)


class TestExistingFunctionalityPreserved(unittest.TestCase):
    """Ensure Phase 41 talking-head functionality still works."""

    def test_voice_map_unchanged(self):
        self.assertEqual(_VOICE_MAP["natural_female"], "Kore")
        self.assertEqual(_VOICE_MAP["natural_male"], "Charon")
        self.assertEqual(_VOICE_MAP["energetic_female"], "Aoede")
        self.assertEqual(_VOICE_MAP["energetic_male"], "Puck")
        self.assertEqual(len(_VOICE_MAP), 6)

    def test_validate_inputs_still_requires_script_or_brief(self):
        recipe = TalkingAvatar()
        err = recipe.validate_inputs({"script": "", "brief": ""})
        self.assertIsNotNone(err)
        self.assertIn("Script", err)

    def test_validate_inputs_passes_with_script(self):
        recipe = TalkingAvatar()
        err = recipe.validate_inputs({"script": "Hello world"})
        self.assertIsNone(err)

    def test_validate_inputs_passes_with_brief(self):
        recipe = TalkingAvatar()
        err = recipe.validate_inputs({"brief": "Product promo"})
        self.assertIsNone(err)

    def test_slug_unchanged(self):
        recipe = TalkingAvatar()
        self.assertEqual(recipe.slug, "talking-avatar")

    def test_original_input_fields_present(self):
        recipe = TalkingAvatar()
        names = [f.name for f in recipe.get_input_fields()]
        self.assertIn("headshot", names)
        self.assertIn("script", names)
        self.assertIn("brief", names)
        self.assertIn("voice_preset", names)


if __name__ == "__main__":
    unittest.main()
