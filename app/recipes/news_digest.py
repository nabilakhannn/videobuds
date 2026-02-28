"""News Digest — auto-curate news on any topic into a newsletter / blog / article.

Uses Gemini to research trending stories on user-specified topics, rank them
by relevance, summarise each story, and format the result as a polished
newsletter, blog post, or LinkedIn article.

When *Blog Post* format is selected, an optional **SEO / GEO / AEO**
checkbox injects search-engine, generative-engine, and answer-engine
optimisation guidelines into the formatting prompt.  The result is a
publish-ready blog with keyword-rich structure, AI-extractable facts,
FAQ section, and a bonus SEO metadata card.
"""

import json
import logging
from datetime import datetime, timezone

from .base import BaseRecipe, InputField

logger = logging.getLogger(__name__)


class NewsDigest(BaseRecipe):
    slug = "news-digest"
    name = "AI News Digest"
    short_description = "Auto-curate the latest news on any topic into a newsletter or SEO-optimized blog."
    description = (
        "Tell the AI what topics you care about (AI, marketing, crypto, etc.) "
        "and it will scan the web, pick the top stories, summarise them, "
        "and assemble a beautiful email newsletter — ready to send to your "
        "audience or save as a blog post. Enable SEO/GEO/AEO optimization "
        "for blog posts to get search-engine-ready content with keyword "
        "targeting, FAQ schema, and AI-overview-friendly structure."
    )
    category = "distribution"
    icon = "📰"
    estimated_cost = "Free – $0.02 per digest"

    how_to_use = """\
### How to use AI News Digest

1. **Enter your topics** — e.g. "AI tools, video marketing, startup funding".
2. **Choose the format** — email newsletter, blog post, or LinkedIn article.
3. **Set the tone** — professional, casual, or witty.
4. *(Blog only)* Check **SEO / GEO / AEO Optimization** for search-engine-ready output.
5. Click **Generate** to have the AI curate today's top stories.
6. Review, edit if needed, and send or download.

**What happens behind the scenes:**
- Step 1: AI searches dozens of news sources for your topics
- Step 2: Stories are ranked by relevance and recency
- Step 3: Top stories are summarised in your chosen tone
- Step 4: Content is formatted as an email / blog post
- *(If SEO enabled)* Blog is optimised for Google, AI overviews & answer engines; a bonus SEO metadata card is generated

**SEO / GEO / AEO explained:**
- **SEO** — keyword-rich headings, meta title & description, internal linking cues
- **GEO** — structured for Google AI Overviews & Perplexity (factual claims, source attribution)
- **AEO** — FAQ section for schema.org markup, featured-snippet-friendly answers

**Tips:**
- Narrow topics produce more relevant digests.
- Run this daily to build a consistent newsletter habit.
- Enable SEO optimisation for blogs you want to rank on Google.
- Connect your email provider for one-click send (coming soon).
"""

    def get_input_fields(self):
        return [
            InputField(
                name="topics",
                label="Topics",
                field_type="text",
                required=True,
                placeholder="e.g. AI tools, video marketing, SaaS startups",
                help_text="Comma-separated topics the AI should search for.",
            ),
            InputField(
                name="story_count",
                label="Number of Stories",
                field_type="select",
                default="5",
                options=[
                    {"value": "3", "label": "3 stories (quick)"},
                    {"value": "5", "label": "5 stories (standard)"},
                    {"value": "10", "label": "10 stories (comprehensive)"},
                ],
            ),
            InputField(
                name="output_format",
                label="Output Format",
                field_type="select",
                default="email",
                options=[
                    {"value": "email", "label": "Email Newsletter"},
                    {"value": "blog", "label": "Blog Post"},
                    {"value": "linkedin", "label": "LinkedIn Article"},
                ],
            ),
            InputField(
                name="tone",
                label="Tone",
                field_type="select",
                default="professional",
                options=[
                    {"value": "professional", "label": "Professional"},
                    {"value": "casual", "label": "Casual & friendly"},
                    {"value": "witty", "label": "Witty & opinionated"},
                ],
            ),
            InputField(
                name="seo_optimize",
                label="SEO / GEO / AEO Optimization",
                field_type="checkbox",
                required=False,
                help_text=(
                    "Optimize blog for search engines (SEO), generative AI "
                    "overviews (GEO), and answer engines (AEO). "
                    "Works best with Blog Post format."
                ),
            ),
        ]

    def get_steps(self):
        return [
            "Researching trending stories",
            "Ranking by relevance",
            "Summarising stories",
            "Formatting digest",
        ]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _call_gemini(prompt: str) -> str:
        """Call Gemini text API — thin wrapper around agent_service helper."""
        from ..services.agent_service import _call_gemini
        return _call_gemini(prompt)

    @staticmethod
    def _call_gemini_grounded(prompt: str) -> str:
        """Call Gemini with Google Search grounding — searches the real web.

        Falls back to standard ``_call_gemini`` if grounding is unavailable
        (e.g. API tier doesn't support it, network issue).
        """
        from ..services.agent_service import _call_gemini_grounded
        return _call_gemini_grounded(prompt)

    # ------------------------------------------------------------------
    # Execute
    # ------------------------------------------------------------------

    def execute(self, inputs, run_id, user_id, on_progress=None,
                brand=None, persona=None):
        """Generate a news digest using Gemini AI.

        Pipeline:
            1. Research — ask Gemini for trending stories on the topics
            2. Rank — filter and rank stories by relevance
            3. Summarise — rewrite each story in the chosen tone
            4. Format — assemble into the requested output format

        When a brand/persona is attached, their voice and audience context
        are injected into the formatting prompt so the digest reads
        on-brand and in the persona's voice.
        """
        topics = inputs.get("topics", "AI")
        story_count = int(inputs.get("story_count", "5"))
        output_format = inputs.get("output_format", "email")
        tone = inputs.get("tone", "professional")

        # SEO/GEO/AEO — only applies when blog format is selected
        seo_optimize = (
            inputs.get("seo_optimize") == "1" and output_format == "blog"
        )

        # Build optional brand/persona context blocks
        brand_ctx = self.build_brand_context(brand)
        persona_ctx = self.build_persona_context(persona)

        today = datetime.now(timezone.utc).strftime("%B %d, %Y")

        # ── Format instructions ──
        format_instructions = {
            "email": (
                "Format the output as an **email newsletter**. "
                "Include a catchy subject line at the top, a short intro paragraph, "
                "numbered story sections with headlines + 2-3 sentence summaries, "
                "and a closing CTA inviting the reader to reply or share."
            ),
            "blog": (
                "Format the output as a **blog post**. "
                "Include a compelling title, an engaging intro paragraph, "
                "story sections with h3 headlines and 3-4 sentence summaries, "
                "analysis of key trends, and a conclusion paragraph."
            ),
            "linkedin": (
                "Format the output as a **LinkedIn article**. "
                "Start with a hook line, use a professional yet engaging tone, "
                "keep each story summary to 2 sentences, include personal insight "
                "after each story, and end with a discussion prompt question."
            ),
        }

        # ── Override blog instructions when SEO/GEO/AEO is enabled ──
        if seo_optimize:
            format_instructions["blog"] = self._build_seo_format_instructions()

        tone_instructions = {
            "professional": "Use a professional, authoritative tone. Write like a respected industry analyst.",
            "casual": "Use a casual, friendly tone. Write like a knowledgeable friend sharing interesting finds over coffee.",
            "witty": "Use a witty, opinionated tone. Add clever commentary, occasional humor, and hot takes.",
        }

        # ── Step 1: Research trending stories ──
        step_label = (
            "Researching stories & SEO keywords…"
            if seo_optimize else "Researching trending stories…"
        )
        self.report_progress(on_progress, 0, step_label)

        research_prompt = f"""You are a world-class news researcher and curator.
Today's date is {today}.

Research and identify the {story_count} most important, trending, and newsworthy
stories related to these topics: **{topics}**

For EACH story, provide:
1. **Headline** — a compelling, accurate headline
2. **Source** — the publication or source name (e.g. TechCrunch, Reuters, The Verge)
3. **Summary** — a factual 3-4 sentence summary of the story
4. **Why it matters** — 1-2 sentences on the significance
5. **Key quote** — a notable quote or data point from the story (if available)

Focus on:
- Stories from the last 7 days
- Factual, verified information
- Stories with real impact on the industry
- Diversity of sources and perspectives

Output ONLY a JSON array of objects. No markdown fences, no extra text.
Example:
[
  {{
    "headline": "...",
    "source": "...",
    "summary": "...",
    "why_it_matters": "...",
    "key_quote": "..."
  }}
]"""

        try:
            # Use grounded search so Gemini actually searches the web for
            # real, current news — this is what differentiates us from ChatGPT.
            raw_stories = self._call_gemini_grounded(research_prompt)
        except Exception as exc:
            logger.error("News Digest: research call failed – %s", exc)
            raise RuntimeError(
                f"Failed to research news stories for '{topics}'. "
                f"Please try again in a moment. (Detail: {exc})"
            ) from exc

        # ── Step 2: Rank stories ──
        self.report_progress(on_progress, 1, "Ranking by relevance…")

        # Parse the stories JSON
        cleaned = raw_stories.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines)

        try:
            stories = json.loads(cleaned)
            if not isinstance(stories, list):
                stories = [stories]
        except json.JSONDecodeError:
            logger.warning("Failed to parse stories JSON, using raw text")
            stories = None

        # ── Step 3: Summarise and format ──
        self.report_progress(on_progress, 2, "Summarising stories…")

        if stories:
            stories_text = "\n\n".join(
                f"**Story {i+1}:**\n"
                f"- Headline: {s.get('headline', 'N/A')}\n"
                f"- Source: {s.get('source', 'N/A')}\n"
                f"- Summary: {s.get('summary', 'N/A')}\n"
                f"- Why it matters: {s.get('why_it_matters', 'N/A')}\n"
                f"- Key quote: {s.get('key_quote', 'N/A')}"
                for i, s in enumerate(stories[:story_count])
            )
        else:
            stories_text = raw_stories

        # ── Step 4: Format into final output ──
        fmt_label = (
            "Formatting SEO/GEO/AEO-optimized blog…"
            if seo_optimize else "Formatting digest…"
        )
        self.report_progress(on_progress, 3, fmt_label)

        # Build brand/persona sections for the formatting prompt
        brand_format_section = ""
        if brand_ctx:
            brand_format_section = (
                f"\n{brand_ctx}\n"
                "Write this digest as if it's coming from the brand above. "
                "Reference the brand's audience, pillars, and style where natural.\n"
            )

        persona_format_section = ""
        if persona_ctx:
            persona_format_section = (
                f"\n{persona_ctx}\n"
                "Write in this persona's voice and tone. "
                "Use their keywords naturally. "
                "Avoid their listed 'never use' words.\n"
            )

        format_prompt = f"""You are an expert content writer and newsletter curator.
Today's date is {today}.

Below are {story_count} curated news stories about **{topics}**:

{stories_text}

{tone_instructions.get(tone, tone_instructions['professional'])}

{format_instructions.get(output_format, format_instructions['email'])}
{brand_format_section}{persona_format_section}
IMPORTANT RULES:
- Write ONLY the final formatted content — no meta-commentary
- Each story must have a clear headline and summary
- Add smooth transitions between stories
- Include an overall theme or trend that connects the stories
- Make it ready to copy-paste and publish immediately
- Use markdown formatting (headers, bold, bullet points) for structure
- The total length should be 800-1500 words"""

        try:
            digest_content = self._call_gemini(format_prompt)
        except Exception as exc:
            logger.error("News Digest: formatting call failed – %s", exc)
            # Graceful fallback: return the raw research data instead of crashing
            digest_content = (
                f"⚠️ **Formatting failed** — the AI could not format the digest "
                f"({exc}). Here are the raw stories:\n\n{stories_text}"
            )

        # ── Parse SEO metadata if present ──
        seo_metadata = None
        if seo_optimize:
            digest_content, seo_metadata = self._extract_seo_metadata(
                digest_content
            )

        # ── Build outputs ──
        outputs = []

        # The main digest
        label_prefix = "📰"
        if seo_optimize:
            label_prefix = "🔍📰"  # signal SEO-optimised
        outputs.append({
            "type": "text",
            "label": f"{label_prefix} {output_format.replace('_', ' ').title()} — {topics}",
            "value": digest_content,
        })

        # SEO Metadata card (only when SEO was enabled and metadata parsed OK)
        if seo_metadata:
            outputs.append({
                "type": "text",
                "label": "🔍 SEO / GEO / AEO Metadata",
                "value": self._format_seo_metadata(seo_metadata),
            })

        # Raw research data (collapsible)
        if stories:
            research_summary = "\n\n".join(
                f"**{i+1}. {s.get('headline', 'Untitled')}** ({s.get('source', 'Unknown')})\n"
                f"{s.get('summary', '')}\n"
                f"*Why it matters:* {s.get('why_it_matters', '')}"
                for i, s in enumerate(stories[:story_count])
            )
            outputs.append({
                "type": "text",
                "label": "🔍 Research Data (Raw Stories)",
                "value": research_summary,
            })

        return {
            "outputs": outputs,
            "cost": 0.0,
            "model_used": "gemini-2.5-flash",
        }

    # ── SEO / GEO / AEO helpers ───────────────────────────────────

    @staticmethod
    def _build_seo_format_instructions() -> str:
        """Return enhanced blog format instructions with SEO/GEO/AEO guidelines."""
        return (
            "Format the output as a **fully SEO / GEO / AEO-optimized blog post**.\n\n"
            "=== SEO (Search Engine Optimization) ===\n"
            "- Craft a keyword-rich H1 title (≤60 chars) with the primary topic keyword\n"
            "- Use H2/H3 subheadings containing secondary keywords (clear hierarchy)\n"
            "- Include the primary keyword naturally in the first 100 words\n"
            "- Target 1500–2500 words for comprehensive topical authority\n"
            "- Write a compelling intro paragraph with a hook\n"
            "- Add a conclusion with key takeaways\n"
            "- Suggest 2–3 internal linking opportunities as [Related: topic] markers\n"
            "- Use transition words for readability (Yoast-friendly)\n"
            "- Include at least one numbered or bulleted list per major section\n\n"
            "=== GEO (Generative Engine Optimization) ===\n"
            "- Write clear, factual declarative statements that AI overviews can extract\n"
            "- Include specific statistics and data points with source attribution\n"
            "- Structure information in self-contained, easily parseable sections\n"
            "- Provide balanced, authoritative perspective on each story\n"
            '- Use "According to [Source]…" attribution for credibility\n'
            "- Each section should be independently understandable\n\n"
            "=== AEO (Answer Engine Optimization) ===\n"
            "- Include a dedicated **## FAQ** section at the end with 4–5 Q&A pairs\n"
            '- Frame key sections as answers to "What / How / Why" questions\n'
            "- Lead key paragraphs with a direct answer (40–60 words), then expand\n"
            "- Use definition-style openings for technical concepts\n"
            "- Structure for Featured Snippets: question → concise answer → detail\n\n"
            "After the COMPLETE blog post content, output this EXACT separator on "
            "its own line:\n"
            "---SEO_METADATA_JSON---\n"
            "Then output ONLY a valid JSON object (no markdown fences) with:\n"
            "{\n"
            '  "title_tag": "SEO title ≤60 chars with primary keyword",\n'
            '  "meta_description": "Meta description ≤155 chars with keyword + CTA",\n'
            '  "primary_keyword": "main target keyword",\n'
            '  "secondary_keywords": ["kw1", "kw2", "kw3", "kw4", "kw5"],\n'
            '  "search_intent": "informational | navigational | transactional",\n'
            '  "faq_schema": [\n'
            '    {"question": "...", "answer": "concise ≤150 chars"},\n'
            "    ...\n"
            "  ],\n"
            '  "internal_link_suggestions": ["topic1", "topic2", "topic3"],\n'
            '  "readability_level": "easy | medium | advanced",\n'
            '  "estimated_word_count": 1800\n'
            "}\n"
        )

    @staticmethod
    def _extract_seo_metadata(
        content: str,
    ) -> "tuple[str, dict | None]":
        """Split blog content from the SEO metadata JSON block.

        Returns ``(blog_content, seo_metadata_dict_or_None)``.
        If the separator is absent or JSON is malformed the full content is
        returned unchanged with ``None`` metadata — no exception is raised.
        """
        SEP = "---SEO_METADATA_JSON---"
        if SEP not in content:
            return content.strip(), None

        parts = content.split(SEP, 1)
        blog = parts[0].strip()
        meta_text = parts[1].strip()

        # Strip optional markdown code fences the model might wrap around JSON
        if meta_text.startswith("```"):
            lines = meta_text.splitlines()
            lines = [ln for ln in lines if not ln.strip().startswith("```")]
            meta_text = "\n".join(lines).strip()

        try:
            metadata = json.loads(meta_text)
        except (json.JSONDecodeError, ValueError):
            logger.warning("SEO metadata JSON could not be parsed — skipping.")
            metadata = None

        return blog, metadata

    @staticmethod
    def _format_seo_metadata(meta: dict) -> str:
        """Render a human-readable markdown card from the parsed SEO metadata."""
        lines = ["## 🔍 SEO / GEO / AEO Metadata\n"]

        if meta.get("title_tag"):
            lines.append(f"**Title Tag:** {meta['title_tag']}\n")
        if meta.get("meta_description"):
            lines.append(f"**Meta Description:** {meta['meta_description']}\n")
        if meta.get("primary_keyword"):
            lines.append(f"**Primary Keyword:** `{meta['primary_keyword']}`\n")

        secondary = meta.get("secondary_keywords", [])
        if secondary:
            lines.append(
                "**Secondary Keywords:** "
                + ", ".join(f"`{kw}`" for kw in secondary)
                + "\n"
            )

        if meta.get("search_intent"):
            lines.append(f"**Search Intent:** {meta['search_intent']}\n")
        if meta.get("readability_level"):
            lines.append(f"**Readability:** {meta['readability_level']}\n")
        if meta.get("estimated_word_count"):
            lines.append(
                f"**Est. Word Count:** ~{meta['estimated_word_count']}\n"
            )

        links = meta.get("internal_link_suggestions", [])
        if links:
            lines.append(
                "**Internal Link Suggestions:** " + ", ".join(links) + "\n"
            )

        faq = meta.get("faq_schema", [])
        if faq:
            lines.append("\n### ❓ FAQ Schema (schema.org ready)\n")
            for item in faq:
                q = item.get("question", "")
                a = item.get("answer", "")
                lines.append(f"**Q:** {q}\n**A:** {a}\n")

        return "\n".join(lines)
