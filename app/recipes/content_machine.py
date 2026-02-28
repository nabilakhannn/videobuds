"""AI Content Machine — competitive intelligence and content strategy.

The user pastes competitor URLs, posts, or content samples and the AI
analyses them to produce:
  1. Hook formula analysis — what makes the content attention-grabbing
  2. Psychological pattern mapping — emotional triggers, pain points, desires
  3. Comment sentiment extraction — what the audience actually cares about
  4. Content strategy playbook — platform-specific content frameworks
  5. Ready-to-use templates — based on proven patterns from the input

Uses Gemini for all analysis.  Brand & persona context is injected so
the strategy output is tailored to *your* brand, not a generic template.

Security: All text inputs validated for length and content.
"""

import json
import logging

from .base import BaseRecipe, InputField

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────

_MAX_CONTENT_LENGTH = 50_000  # chars
_MAX_URLS = 20
_MAX_URL_LEN = 2000

_ANALYSIS_MODES = {
    "full": {
        "label": "Full Analysis — hooks, psychology, strategy, templates",
        "steps": ["hooks", "psychology", "strategy", "templates"],
    },
    "hooks_only": {
        "label": "Hook Analysis Only — what makes the content grab attention",
        "steps": ["hooks"],
    },
    "strategy_only": {
        "label": "Strategy & Templates — skip analysis, go straight to playbook",
        "steps": ["strategy", "templates"],
    },
}

_PLATFORM_TARGETS = {
    "all": "All Platforms",
    "instagram": "Instagram (Reels / Posts / Stories)",
    "tiktok": "TikTok",
    "youtube": "YouTube (Shorts & Long-form)",
    "linkedin": "LinkedIn",
    "x_twitter": "X (Twitter)",
}


class ContentMachine(BaseRecipe):
    slug = "content-machine"
    name = "AI Content Machine"
    short_description = (
        "Paste competitor content — get a psychology-backed content strategy."
    )
    description = (
        "Feed the AI competitor posts, hooks, or URLs. It analyses what makes "
        "the content work (hook formulas, psychological triggers, engagement "
        "patterns) and generates a complete content strategy with ready-to-use "
        "templates tailored to your brand and audience."
    )
    category = "research"
    icon = "🧠"
    estimated_cost = "$0.00 (Gemini analysis only)"
    is_active = True

    how_to_use = """\
### How to use AI Content Machine

**What it does:**
Analyses competitor or viral content to reverse-engineer what works —
then builds a custom content strategy for *your* brand.

**Steps:**
1. **Paste competitor content** — URLs, post text, hooks, or captions (one per line).
   You can also paste comment sections for deeper audience analysis.
2. *(Optional)* **Add audience comments** — paste top comments from viral posts
   for pain-point and desire mapping.
3. **Choose analysis mode** — Full, Hooks Only, or Strategy Only.
4. **Choose target platforms** — where you want to publish.
5. **Select a Brand and/or Persona** — the strategy adapts to your positioning.
6. Click **Analyse** and wait 1–3 minutes.

**What you'll get:**

| Output | Description |
|--------|-------------|
| Hook Formula Analysis | Breakdown of what makes each hook work |
| Psychological Pattern Map | Emotional triggers, pain points, desires |
| Content Strategy Playbook | Platform-specific frameworks |
| Ready-to-Use Templates | Fill-in-the-blank content templates |
| Trend Signals | Patterns across the input content |

**Tips:**
- Paste 3–10 competitor posts for the best pattern detection.
- Include the *best* performing content — the AI learns from winners.
- Add comment sections to understand audience psychology deeper.
- The Brand context ensures the strategy fits your positioning.
- Re-run monthly to keep your playbook fresh.
"""

    # ------------------------------------------------------------------
    # Input fields
    # ------------------------------------------------------------------

    def get_input_fields(self):
        return [
            InputField(
                name="competitor_content",
                label="Competitor Content / URLs / Posts",
                field_type="textarea",
                required=True,
                placeholder=(
                    "Paste competitor content here — one item per line.\n\n"
                    "Examples:\n"
                    "https://www.instagram.com/p/ABC123/\n"
                    "\"Stop scrolling. This one trick changed my morning routine.\"\n"
                    "https://www.tiktok.com/@user/video/123456"
                ),
                help_text=(
                    "Paste URLs, post text, hooks, or captions. "
                    "The AI will analyse each one. Up to 20 items, "
                    "or free-form text up to 50,000 characters."
                ),
            ),
            InputField(
                name="audience_comments",
                label="Audience Comments (optional — for deeper psychology)",
                field_type="textarea",
                required=False,
                placeholder=(
                    "Paste top comments from viral posts:\n\n"
                    "\"This is exactly what I needed to hear\"\n"
                    "\"Why didn't anyone tell me this sooner?\"\n"
                    "\"I've been doing it wrong for years\""
                ),
                help_text=(
                    "Comments reveal audience pain points, desires, and objections. "
                    "Paste them here for deeper psychological analysis."
                ),
            ),
            InputField(
                name="analysis_mode",
                label="Analysis Mode",
                field_type="select",
                default="full",
                options=[
                    {"value": k, "label": v["label"]}
                    for k, v in _ANALYSIS_MODES.items()
                ],
                help_text="Full = hooks + psychology + strategy + templates.",
            ),
            InputField(
                name="target_platform",
                label="Target Platform",
                field_type="select",
                default="all",
                options=[
                    {"value": k, "label": v}
                    for k, v in _PLATFORM_TARGETS.items()
                ],
                help_text="The strategy and templates will be tailored for this platform.",
            ),
            InputField(
                name="industry_context",
                label="Industry / Niche (optional)",
                field_type="text",
                required=False,
                placeholder="e.g. DTC skincare, B2B SaaS, Fitness coaching",
                help_text="Helps the AI produce more relevant patterns and examples.",
            ),
        ]

    def get_steps(self):
        return [
            "Parsing inputs",
            "Analysing hooks & patterns",
            "Mapping psychology & triggers",
            "Generating content strategy",
            "Building templates",
        ]

    # ------------------------------------------------------------------
    # Gemini helper
    # ------------------------------------------------------------------

    @staticmethod
    def _call_gemini(prompt: str) -> str:
        from ..services.agent_service import _call_gemini
        return _call_gemini(prompt)

    # ------------------------------------------------------------------
    # Execute
    # ------------------------------------------------------------------

    def execute(self, inputs, run_id, user_id, on_progress=None,
                brand=None, persona=None):
        """Analyse competitor content and generate a content strategy.

        Returns hook analysis, psychological patterns, strategy playbook,
        and ready-to-use templates — all tailored to the user's brand/persona.
        """
        # ── Step 0: Parse & validate inputs ───────────────────────────
        self.report_progress(on_progress, 0, "Parsing inputs…")

        raw_content = (inputs.get("competitor_content") or "").strip()
        if not raw_content:
            raise ValueError(
                "Competitor content is required. Paste URLs, posts, or hooks."
            )
        if len(raw_content) > _MAX_CONTENT_LENGTH:
            raise ValueError(
                f"Content too long ({len(raw_content):,} chars). "
                f"Maximum is {_MAX_CONTENT_LENGTH:,} characters."
            )

        audience_comments = (inputs.get("audience_comments") or "").strip()
        if len(audience_comments) > _MAX_CONTENT_LENGTH:
            audience_comments = audience_comments[:_MAX_CONTENT_LENGTH]

        analysis_mode = inputs.get("analysis_mode", "full")
        if analysis_mode not in _ANALYSIS_MODES:
            analysis_mode = "full"

        target_platform = inputs.get("target_platform", "all")
        if target_platform not in _PLATFORM_TARGETS:
            target_platform = "all"
        platform_label = _PLATFORM_TARGETS[target_platform]

        industry = (inputs.get("industry_context") or "").strip()[:500]

        # Build brand & persona context
        brand_ctx = self.build_brand_context(brand)
        persona_ctx = self.build_persona_context(persona)

        # Parse content items (split by newlines, filter blanks)
        content_items = [
            line.strip() for line in raw_content.split("\n")
            if line.strip()
        ]

        outputs = []
        mode_steps = _ANALYSIS_MODES[analysis_mode]["steps"]

        # ── Step 1: Hook Analysis ─────────────────────────────────────
        hook_analysis = ""
        if "hooks" in mode_steps:
            self.report_progress(
                on_progress, 1,
                f"Analysing {len(content_items)} items for hook formulas…"
            )
            hook_analysis = self._analyse_hooks(
                content_items, brand_ctx, persona_ctx, platform_label, industry
            )
            outputs.append({
                "type": "text",
                "title": "🪝 Hook Formula Analysis",
                "value": hook_analysis,
            })

        # ── Step 2: Psychological Pattern Mapping ─────────────────────
        psych_analysis = ""
        if "psychology" in mode_steps:
            self.report_progress(
                on_progress, 2,
                "Mapping psychological triggers and audience patterns…"
            )
            psych_analysis = self._analyse_psychology(
                content_items, audience_comments, brand_ctx, persona_ctx,
                platform_label, industry
            )
            outputs.append({
                "type": "text",
                "title": "🧠 Psychological Pattern Map",
                "value": psych_analysis,
            })

        # ── Step 3: Content Strategy ──────────────────────────────────
        strategy = ""
        if "strategy" in mode_steps:
            self.report_progress(
                on_progress, 3,
                f"Generating {platform_label} content strategy…"
            )
            strategy = self._generate_strategy(
                content_items, hook_analysis, psych_analysis,
                audience_comments, brand_ctx, persona_ctx,
                platform_label, industry
            )
            outputs.append({
                "type": "text",
                "title": "📋 Content Strategy Playbook",
                "value": strategy,
            })

        # ── Step 4: Templates ─────────────────────────────────────────
        if "templates" in mode_steps:
            self.report_progress(
                on_progress, 4,
                "Building ready-to-use content templates…"
            )
            templates = self._generate_templates(
                hook_analysis, psych_analysis, strategy,
                brand_ctx, persona_ctx, platform_label, industry
            )
            outputs.append({
                "type": "text",
                "title": "📝 Ready-to-Use Templates",
                "value": templates,
            })

        # ── Summary card ──────────────────────────────────────────────
        summary_lines = [
            f"**Items Analysed:** {len(content_items)}",
            f"**Mode:** {_ANALYSIS_MODES[analysis_mode]['label']}",
            f"**Target Platform:** {platform_label}",
        ]
        if industry:
            summary_lines.append(f"**Industry:** {industry}")
        if audience_comments:
            comment_count = len([
                c for c in audience_comments.split("\n") if c.strip()
            ])
            summary_lines.append(f"**Audience Comments:** {comment_count}")
        if brand:
            summary_lines.append(f"**Brand:** {brand.name}")
        if persona:
            summary_lines.append(f"**Persona:** {persona.name}")
        summary_lines.append(f"**Sections Generated:** {len(outputs)}")

        outputs.insert(0, {
            "type": "text",
            "title": "Analysis Summary",
            "value": "\n".join(summary_lines),
        })

        return {"outputs": outputs, "cost": 0.0}

    # ------------------------------------------------------------------
    # Analysis methods (each calls Gemini with focused prompts)
    # ------------------------------------------------------------------

    def _analyse_hooks(self, content_items, brand_ctx, persona_ctx,
                       platform_label, industry):
        """Analyse hook formulas in competitor content."""
        content_block = "\n---\n".join(content_items[:_MAX_URLS])

        prompt_parts = [
            "You are an expert content strategist and copywriter who specialises "
            "in hook formulas and attention engineering.\n\n",
            "TASK: Analyse the following competitor content and identify the "
            "hook formulas used. For each piece of content:\n"
            "1. Identify the hook type (curiosity gap, contrarian take, "
            "number/list, before/after, social proof, urgency, etc.)\n"
            "2. Explain WHY it works psychologically\n"
            "3. Rate its attention-grabbing power (1–10)\n"
            "4. Show how it could be adapted for the user's brand\n\n",
            f"TARGET PLATFORM: {platform_label}\n",
        ]
        if industry:
            prompt_parts.append(f"INDUSTRY/NICHE: {industry}\n")
        if brand_ctx:
            prompt_parts.append(f"\n{brand_ctx}\n")
        if persona_ctx:
            prompt_parts.append(f"\n{persona_ctx}\n")
        prompt_parts.append(
            f"\n─── COMPETITOR CONTENT TO ANALYSE ───\n{content_block}\n"
            "─── END CONTENT ───\n\n"
            "OUTPUT FORMAT:\n"
            "Use clear markdown with headers for each hook analysis. "
            "End with a **Summary** section listing the top 3 hook patterns "
            "and a **Hook Formula Cheat Sheet** with fill-in-the-blank templates.\n"
            "Be specific, actionable, and insightful — not generic."
        )

        try:
            return self._call_gemini("".join(prompt_parts))
        except Exception as exc:
            logger.error("Hook analysis failed: %s", exc)
            return f"⚠️ Hook analysis could not be completed: {exc}"

    def _analyse_psychology(self, content_items, audience_comments,
                            brand_ctx, persona_ctx, platform_label, industry):
        """Map psychological patterns, triggers, and audience signals."""
        content_block = "\n---\n".join(content_items[:_MAX_URLS])

        prompt_parts = [
            "You are a consumer psychologist and content strategist.\n\n",
            "TASK: Analyse the competitor content (and audience comments if provided) "
            "to map the psychological patterns at play:\n"
            "1. **Emotional Triggers** — which emotions does this content activate? "
            "(fear of missing out, aspiration, frustration, curiosity, belonging, etc.)\n"
            "2. **Pain Points** — what problems/frustrations does the audience express?\n"
            "3. **Desires** — what do they want? What transformation are they seeking?\n"
            "4. **Objections** — what hesitations or skepticism appear?\n"
            "5. **Shareability Drivers** — why would someone share this?\n"
            "6. **Identity Signals** — what does engaging with this say about the person?\n\n",
            f"TARGET PLATFORM: {platform_label}\n",
        ]
        if industry:
            prompt_parts.append(f"INDUSTRY/NICHE: {industry}\n")
        if brand_ctx:
            prompt_parts.append(f"\n{brand_ctx}\n")
        if persona_ctx:
            prompt_parts.append(f"\n{persona_ctx}\n")

        prompt_parts.append(
            f"\n─── COMPETITOR CONTENT ───\n{content_block}\n─── END CONTENT ───\n"
        )
        if audience_comments:
            prompt_parts.append(
                f"\n─── AUDIENCE COMMENTS ───\n{audience_comments[:5000]}\n"
                "─── END COMMENTS ───\n"
            )

        prompt_parts.append(
            "\nOUTPUT FORMAT:\n"
            "Use clear markdown with sections for each pattern category. "
            "Include specific examples from the input. "
            "End with a **Pattern Summary** table mapping triggers → content types.\n"
            "Be data-driven and specific — cite actual phrases from the input."
        )

        try:
            return self._call_gemini("".join(prompt_parts))
        except Exception as exc:
            logger.error("Psychology analysis failed: %s", exc)
            return f"⚠️ Psychological analysis could not be completed: {exc}"

    def _generate_strategy(self, content_items, hook_analysis, psych_analysis,
                           audience_comments, brand_ctx, persona_ctx,
                           platform_label, industry):
        """Generate a content strategy playbook based on all analysis."""
        prompt_parts = [
            "You are a senior content strategist creating a data-driven "
            "content playbook based on competitive intelligence.\n\n",
            "TASK: Using the hook analysis and psychological pattern map below, "
            "generate a comprehensive content strategy:\n"
            "1. **Content Pillars** — 3–5 theme categories based on what works\n"
            "2. **Posting Cadence** — recommended frequency and timing\n"
            "3. **Content Mix** — ratio of content types (educational, "
            "entertaining, promotional, community)\n"
            "4. **Hook Strategy** — which hook formulas to prioritise\n"
            "5. **Engagement Playbook** — how to drive comments and shares\n"
            "6. **Differentiation Angles** — how to stand out from competitors\n"
            "7. **30-Day Quick-Start Plan** — week-by-week action items\n\n",
            f"TARGET PLATFORM: {platform_label}\n",
        ]
        if industry:
            prompt_parts.append(f"INDUSTRY/NICHE: {industry}\n")
        if brand_ctx:
            prompt_parts.append(f"\n{brand_ctx}\n")
        if persona_ctx:
            prompt_parts.append(f"\n{persona_ctx}\n")
        if hook_analysis and not hook_analysis.startswith("⚠️"):
            prompt_parts.append(
                f"\n─── HOOK ANALYSIS ───\n{hook_analysis[:3000]}\n"
                "─── END HOOK ANALYSIS ───\n"
            )
        if psych_analysis and not psych_analysis.startswith("⚠️"):
            prompt_parts.append(
                f"\n─── PSYCHOLOGICAL PATTERNS ───\n{psych_analysis[:3000]}\n"
                "─── END PATTERNS ───\n"
            )

        prompt_parts.append(
            "\nOUTPUT FORMAT:\n"
            "Structured markdown with headers, bullet points, and tables. "
            "Be specific to the user's brand — not generic advice. "
            "Every recommendation should be actionable and tied to evidence "
            "from the analysis."
        )

        try:
            return self._call_gemini("".join(prompt_parts))
        except Exception as exc:
            logger.error("Strategy generation failed: %s", exc)
            return f"⚠️ Strategy generation could not be completed: {exc}"

    def _generate_templates(self, hook_analysis, psych_analysis, strategy,
                            brand_ctx, persona_ctx, platform_label, industry):
        """Generate fill-in-the-blank content templates."""
        prompt_parts = [
            "You are a content creator generating ready-to-use templates "
            "based on proven competitive intelligence.\n\n",
            "TASK: Create 5–8 content templates that the user can fill in "
            "and publish immediately. Each template should:\n"
            "1. Use a proven hook formula from the analysis\n"
            "2. Target a specific psychological trigger\n"
            "3. Be platform-appropriate\n"
            "4. Include [BLANKS] for customisation\n"
            "5. Have a brief usage note explaining when to use it\n\n",
            f"TARGET PLATFORM: {platform_label}\n",
        ]
        if industry:
            prompt_parts.append(f"INDUSTRY/NICHE: {industry}\n")
        if brand_ctx:
            prompt_parts.append(f"\n{brand_ctx}\n")
        if persona_ctx:
            prompt_parts.append(f"\n{persona_ctx}\n")
        if hook_analysis and not hook_analysis.startswith("⚠️"):
            prompt_parts.append(
                f"\n─── HOOK ANALYSIS (reference) ───\n"
                f"{hook_analysis[:2000]}\n─── END ───\n"
            )
        if psych_analysis and not psych_analysis.startswith("⚠️"):
            prompt_parts.append(
                f"\n─── PSYCHOLOGY (reference) ───\n"
                f"{psych_analysis[:2000]}\n─── END ───\n"
            )
        if strategy and not strategy.startswith("⚠️"):
            prompt_parts.append(
                f"\n─── STRATEGY (reference) ───\n"
                f"{strategy[:2000]}\n─── END ───\n"
            )

        prompt_parts.append(
            "\nOUTPUT FORMAT:\n"
            "Number each template. For each:\n"
            "**Template #N: [Name]**\n"
            "- 🎯 When to use: [context]\n"
            "- 🪝 Hook formula: [type]\n"
            "- 📝 Template:\n"
            "```\n[The actual template with [BLANKS]]\n```\n"
            "- 💡 Example (filled in): [A completed version]\n\n"
            "Make them genuinely useful — not generic motivational filler."
        )

        try:
            return self._call_gemini("".join(prompt_parts))
        except Exception as exc:
            logger.error("Template generation failed: %s", exc)
            return f"⚠️ Template generation could not be completed: {exc}"
