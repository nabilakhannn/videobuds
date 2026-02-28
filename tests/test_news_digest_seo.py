"""Unit tests for the SEO / GEO / AEO feature in the News Digest recipe.

Tests cover:
- InputField checkbox presence
- SEO format instructions generation
- SEO metadata extraction / parsing (happy-path + edge cases)
- SEO metadata formatting
- Integration: seo_optimize flag gating (blog-only)
- Integration: progress labels reflect SEO mode
"""

import json
import pytest

from app.recipes.news_digest import NewsDigest as NewsDigestRecipe


# ─────────────────────────── Fixtures ────────────────────────────

@pytest.fixture
def recipe():
    return NewsDigestRecipe()


# Realistic Gemini-style response containing blog + SEO metadata
SAMPLE_BLOG_WITH_METADATA = """\
# AI Revolution: Top 5 Stories Shaping the Future

The artificial intelligence landscape continues to evolve at a breathtaking pace…

## 1. OpenAI Launches GPT-5

According to OpenAI, the new model achieves human-level performance on several benchmarks…

## 2. Google DeepMind's Gemini 2.5

DeepMind announced significant improvements in multimodal reasoning…

## FAQ

**Q: What is GPT-5?**
A: GPT-5 is OpenAI's latest large language model, featuring improved reasoning…

**Q: How does Gemini 2.5 compare?**
A: Gemini 2.5 excels in multimodal tasks, combining vision and language capabilities…

---SEO_METADATA_JSON---
{
  "title_tag": "AI Revolution 2026: Top 5 Stories Shaping the Future",
  "meta_description": "Discover the top 5 AI breakthroughs of 2026, from GPT-5 to Gemini 2.5. Stay ahead with our expert analysis.",
  "primary_keyword": "AI breakthroughs 2026",
  "secondary_keywords": ["GPT-5 launch", "Gemini 2.5", "AI trends", "machine learning", "LLM updates"],
  "search_intent": "informational",
  "faq_schema": [
    {"question": "What is GPT-5?", "answer": "GPT-5 is OpenAI's latest LLM with human-level reasoning."},
    {"question": "How does Gemini 2.5 compare?", "answer": "Gemini 2.5 excels in multimodal tasks combining vision and language."}
  ],
  "internal_link_suggestions": ["AI tools roundup", "machine learning guide", "LLM comparison"],
  "readability_level": "medium",
  "estimated_word_count": 1800
}"""

SAMPLE_BLOG_NO_METADATA = """\
# AI Revolution: Top 5 Stories

Some blog content without the SEO metadata separator."""


# ─────────── Test 1: InputField checkbox exists ────────────

class TestSEOInputField:
    def test_seo_checkbox_present(self, recipe):
        """SEO checkbox must be in the input fields."""
        fields = recipe.get_input_fields()
        seo_fields = [f for f in fields if f.name == "seo_optimize"]
        assert len(seo_fields) == 1, "seo_optimize field not found"
        seo = seo_fields[0]
        assert seo.field_type == "checkbox"
        assert seo.required is False
        assert "SEO" in seo.label
        assert "GEO" in seo.label
        assert "AEO" in seo.label

    def test_seo_checkbox_is_last_field(self, recipe):
        """SEO checkbox should appear after all other fields."""
        fields = recipe.get_input_fields()
        assert fields[-1].name == "seo_optimize"

    def test_help_text_mentions_blog(self, recipe):
        """Help text should mention 'Blog Post' since SEO works best with it."""
        fields = recipe.get_input_fields()
        seo = [f for f in fields if f.name == "seo_optimize"][0]
        assert "blog" in seo.help_text.lower()


# ────── Test 2: SEO Format Instructions ──────

class TestSEOFormatInstructions:
    def test_instructions_contain_seo_section(self):
        instructions = NewsDigestRecipe._build_seo_format_instructions()
        assert "SEO (Search Engine Optimization)" in instructions

    def test_instructions_contain_geo_section(self):
        instructions = NewsDigestRecipe._build_seo_format_instructions()
        assert "GEO (Generative Engine Optimization)" in instructions

    def test_instructions_contain_aeo_section(self):
        instructions = NewsDigestRecipe._build_seo_format_instructions()
        assert "AEO (Answer Engine Optimization)" in instructions

    def test_instructions_request_faq(self):
        instructions = NewsDigestRecipe._build_seo_format_instructions()
        assert "FAQ" in instructions

    def test_instructions_request_metadata_separator(self):
        instructions = NewsDigestRecipe._build_seo_format_instructions()
        assert "---SEO_METADATA_JSON---" in instructions

    def test_instructions_request_json_fields(self):
        instructions = NewsDigestRecipe._build_seo_format_instructions()
        for field in ["title_tag", "meta_description", "primary_keyword",
                       "secondary_keywords", "faq_schema"]:
            assert field in instructions, f"Missing {field} in instructions"


# ────── Test 3: SEO Metadata Extraction ──────

class TestSEOMetadataExtraction:
    def test_happy_path_extraction(self):
        """Full content with valid SEO metadata should parse cleanly."""
        blog, meta = NewsDigestRecipe._extract_seo_metadata(
            SAMPLE_BLOG_WITH_METADATA
        )
        assert meta is not None
        assert "---SEO_METADATA_JSON---" not in blog
        assert "AI Revolution" in blog
        assert meta["primary_keyword"] == "AI breakthroughs 2026"
        assert len(meta["secondary_keywords"]) == 5
        assert len(meta["faq_schema"]) == 2
        assert meta["estimated_word_count"] == 1800

    def test_no_separator_returns_none_metadata(self):
        """When separator is absent, return full content + None."""
        blog, meta = NewsDigestRecipe._extract_seo_metadata(
            SAMPLE_BLOG_NO_METADATA
        )
        assert meta is None
        assert "AI Revolution" in blog

    def test_empty_content(self):
        blog, meta = NewsDigestRecipe._extract_seo_metadata("")
        assert blog == ""
        assert meta is None

    def test_malformed_json_returns_none(self):
        """Malformed JSON after separator should not crash."""
        content = "Blog text\n---SEO_METADATA_JSON---\n{invalid json here!!"
        blog, meta = NewsDigestRecipe._extract_seo_metadata(content)
        assert meta is None
        assert "Blog text" in blog

    def test_json_with_markdown_fences(self):
        """Model might wrap JSON in ```json fences — should still parse."""
        content = (
            "Blog text\n---SEO_METADATA_JSON---\n"
            '```json\n{"title_tag": "Test Title", "primary_keyword": "test"}\n```'
        )
        blog, meta = NewsDigestRecipe._extract_seo_metadata(content)
        assert meta is not None
        assert meta["title_tag"] == "Test Title"
        assert "Blog text" in blog

    def test_blog_content_preserved_exactly(self):
        """Blog content before separator must not be altered."""
        original_blog = "# Title\n\nParagraph one.\n\n## Section\n\nMore text."
        content = original_blog + "\n---SEO_METADATA_JSON---\n{}"
        blog, meta = NewsDigestRecipe._extract_seo_metadata(content)
        assert blog == original_blog
        assert meta == {}


# ────── Test 4: SEO Metadata Formatting ──────

class TestSEOMetadataFormatting:
    def test_format_full_metadata(self):
        meta = {
            "title_tag": "AI Trends 2026",
            "meta_description": "Top AI trends to watch in 2026.",
            "primary_keyword": "AI trends",
            "secondary_keywords": ["GPT-5", "Gemini", "LLMs"],
            "search_intent": "informational",
            "readability_level": "medium",
            "estimated_word_count": 1500,
            "internal_link_suggestions": ["ML guide", "AI tools"],
            "faq_schema": [
                {"question": "What are AI trends?", "answer": "Latest AI developments."},
            ],
        }
        result = NewsDigestRecipe._format_seo_metadata(meta)
        assert "AI Trends 2026" in result
        assert "`AI trends`" in result  # keyword in code format
        assert "`GPT-5`" in result
        assert "ML guide" in result
        assert "FAQ Schema" in result
        assert "What are AI trends?" in result

    def test_format_minimal_metadata(self):
        """Should not crash with only a subset of fields."""
        meta = {"title_tag": "Minimal"}
        result = NewsDigestRecipe._format_seo_metadata(meta)
        assert "Minimal" in result

    def test_format_empty_metadata(self):
        """Empty dict should produce header only, no crash."""
        result = NewsDigestRecipe._format_seo_metadata({})
        assert "SEO / GEO / AEO Metadata" in result


# ────── Test 5: SEO Flag Gating (blog-only) ──────

class TestSEOFlagGating:
    """Verify seo_optimize only triggers for blog format."""

    def test_seo_flag_true_for_blog(self):
        """seo_optimize=1 + blog → True."""
        inputs = {"seo_optimize": "1", "output_format": "blog"}
        flag = inputs.get("seo_optimize") == "1" and inputs.get("output_format") == "blog"
        assert flag is True

    def test_seo_flag_false_for_email(self):
        """seo_optimize=1 + email → False (SEO only for blog)."""
        inputs = {"seo_optimize": "1", "output_format": "email"}
        flag = inputs.get("seo_optimize") == "1" and inputs.get("output_format") == "blog"
        assert flag is False

    def test_seo_flag_false_for_linkedin(self):
        inputs = {"seo_optimize": "1", "output_format": "linkedin"}
        flag = inputs.get("seo_optimize") == "1" and inputs.get("output_format") == "blog"
        assert flag is False

    def test_seo_flag_false_when_unchecked(self):
        """Checkbox unchecked → seo_optimize absent from inputs."""
        inputs = {"output_format": "blog"}
        flag = inputs.get("seo_optimize") == "1" and inputs.get("output_format") == "blog"
        assert flag is False


# ────── Test 6: Integration (mocked Gemini) ──────

class TestSEOIntegration:
    """Integration tests that mock _call_gemini to verify full flow."""

    def test_seo_blog_produces_metadata_output(self, recipe, monkeypatch):
        """When SEO + blog, outputs should include an SEO metadata card."""
        # First Gemini call = research (returns JSON stories)
        research_json = json.dumps([
            {
                "headline": "AI News Story",
                "source": "TechCrunch",
                "summary": "A summary of AI news.",
                "why_it_matters": "Important for the industry.",
                "relevance_score": 9,
            }
        ])
        # Research step now uses _call_gemini_grounded; format step uses _call_gemini
        monkeypatch.setattr(recipe, "_call_gemini_grounded", lambda prompt: research_json)
        monkeypatch.setattr(recipe, "_call_gemini", lambda prompt: SAMPLE_BLOG_WITH_METADATA)

        result = recipe.execute(
            inputs={
                "topics": "AI",
                "story_count": "1",
                "output_format": "blog",
                "tone": "professional",
                "seo_optimize": "1",
            },
            run_id=1,
            user_id=1,
            on_progress=lambda *a, **kw: None,
        )

        outputs = result["outputs"]
        labels = [o["label"] for o in outputs]

        # Should have: SEO blog, SEO metadata card, research data
        assert any("SEO / GEO / AEO Metadata" in l for l in labels), \
            f"SEO metadata card missing; got labels: {labels}"
        # Blog content should NOT contain the separator
        blog_output = outputs[0]
        assert "---SEO_METADATA_JSON---" not in blog_output["value"]

    def test_non_seo_blog_has_no_metadata_output(self, recipe, monkeypatch):
        """When SEO is off, no metadata card should be produced."""
        research_json = json.dumps([
            {
                "headline": "Story",
                "source": "Src",
                "summary": "Sum.",
                "why_it_matters": "Why.",
                "relevance_score": 8,
            }
        ])
        monkeypatch.setattr(recipe, "_call_gemini_grounded", lambda prompt: research_json)
        monkeypatch.setattr(recipe, "_call_gemini", lambda prompt: SAMPLE_BLOG_NO_METADATA)

        result = recipe.execute(
            inputs={
                "topics": "AI",
                "story_count": "1",
                "output_format": "blog",
                "tone": "professional",
                # seo_optimize NOT set
            },
            run_id=1,
            user_id=1,
            on_progress=lambda *a, **kw: None,
        )

        labels = [o["label"] for o in result["outputs"]]
        assert not any("SEO / GEO / AEO Metadata" in l for l in labels)

    def test_seo_email_has_no_metadata_output(self, recipe, monkeypatch):
        """SEO checkbox + email format → SEO should NOT trigger."""
        research_json = json.dumps([
            {
                "headline": "Story",
                "source": "Src",
                "summary": "Sum.",
                "why_it_matters": "Why.",
                "relevance_score": 8,
            }
        ])
        monkeypatch.setattr(recipe, "_call_gemini_grounded", lambda prompt: research_json)
        monkeypatch.setattr(recipe, "_call_gemini", lambda prompt: "Email newsletter content here.")

        result = recipe.execute(
            inputs={
                "topics": "AI",
                "story_count": "1",
                "output_format": "email",
                "tone": "professional",
                "seo_optimize": "1",  # checked but email format
            },
            run_id=1,
            user_id=1,
            on_progress=lambda *a, **kw: None,
        )

        labels = [o["label"] for o in result["outputs"]]
        assert not any("SEO / GEO / AEO Metadata" in l for l in labels)

    def test_seo_progress_labels(self, recipe, monkeypatch):
        """When SEO is active, progress labels should mention SEO."""
        research_json = json.dumps([
            {
                "headline": "Story",
                "source": "Src",
                "summary": "Sum.",
                "why_it_matters": "Why.",
                "relevance_score": 8,
            }
        ])
        monkeypatch.setattr(recipe, "_call_gemini_grounded", lambda prompt: research_json)
        monkeypatch.setattr(recipe, "_call_gemini", lambda prompt: SAMPLE_BLOG_WITH_METADATA)

        progress_labels = []
        def capture_progress(step, label=""):
            progress_labels.append(label)

        recipe.execute(
            inputs={
                "topics": "AI",
                "story_count": "1",
                "output_format": "blog",
                "tone": "professional",
                "seo_optimize": "1",
            },
            run_id=1,
            user_id=1,
            on_progress=capture_progress,
        )

        # Step 0 and step 3 should mention SEO
        assert any("SEO" in l for l in progress_labels), \
            f"No SEO in progress labels: {progress_labels}"

    def test_non_seo_progress_labels(self, recipe, monkeypatch):
        """When SEO is off, progress labels should NOT mention SEO."""
        research_json = json.dumps([
            {
                "headline": "Story",
                "source": "Src",
                "summary": "Sum.",
                "why_it_matters": "Why.",
                "relevance_score": 8,
            }
        ])
        monkeypatch.setattr(recipe, "_call_gemini_grounded", lambda prompt: research_json)
        monkeypatch.setattr(recipe, "_call_gemini", lambda prompt: SAMPLE_BLOG_NO_METADATA)

        progress_labels = []
        def capture_progress(step, label=""):
            progress_labels.append(label)

        recipe.execute(
            inputs={
                "topics": "AI",
                "story_count": "1",
                "output_format": "blog",
                "tone": "professional",
            },
            run_id=1,
            user_id=1,
            on_progress=capture_progress,
        )

        # No label should mention SEO
        assert not any("SEO" in l for l in progress_labels), \
            f"SEO found in non-SEO labels: {progress_labels}"


# ────── Test 7: Step count stays at 4 ──────

class TestStepCount:
    def test_get_steps_returns_four(self, recipe):
        """Step count must remain 4 regardless of SEO — avoids progress bar issues."""
        steps = recipe.get_steps()
        assert len(steps) == 4

    def test_how_to_use_mentions_seo(self, recipe):
        """How-to-use should mention the SEO checkbox."""
        assert "SEO" in recipe.how_to_use
        assert "GEO" in recipe.how_to_use
        assert "AEO" in recipe.how_to_use
