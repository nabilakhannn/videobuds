"""Style Cloner — analyse a reference video and reproduce its style.

Based on the R51 "The Creative Cloner AI Agent" n8n workflow.
"""

from .base import BaseRecipe, InputField


class StyleCloner(BaseRecipe):
    slug = "style-cloner"
    name = "Style Cloner"
    short_description = "Show the AI a video you love — it recreates the same style for your brand."
    description = (
        "Found a video ad, Reel, or TikTok whose style you love? Upload it "
        "or paste the link. The AI watches it, breaks down the visual style "
        "(colours, pacing, transitions, mood), and generates new images, "
        "videos, and even a matching soundtrack — all in that same style, "
        "but for *your* brand."
    )
    category = "video_studio"
    icon = "🎨"
    estimated_cost = "$0.20 – $0.80 per project"
    is_active = False  # Stub — not yet wired to backend

    how_to_use = """\
### How to use Style Cloner

1. **Paste a video URL** or **upload the video** you want to clone the style of.
2. **Describe your brand / product** — the AI will apply the cloned style to your brief.
3. **Choose what to generate** — images only, video only, or full package.
4. Click **Generate** — the AI analyses and reproduces.
5. Review and download your on-brand assets in the cloned style.

**What happens behind the scenes:**
- Step 1: AI watches the reference video frame by frame
- Step 2: Style DNA is extracted (colour palette, transitions, pacing, mood)
- Step 3: Your brand brief is merged with the style DNA
- Step 4: New images, videos, and/or music are generated
- Step 5: Assets are packaged and ready for download

**What the AI extracts from the reference:**
- 🎨 Colour palette & grading
- 🎬 Cut rhythm & transition style
- 📐 Composition & framing
- 🎵 Music mood & tempo
- ✍️ Typography & text overlay style

**Tips:**
- Use short reference videos (under 60 seconds) for best analysis.
- The more distinctive the style, the better the clone.
"""

    def get_input_fields(self):
        return [
            InputField(
                name="reference_url",
                label="Reference Video URL",
                field_type="text",
                required=False,
                placeholder="https://www.tiktok.com/@brand/video/...",
                help_text="Paste a TikTok, Instagram, or YouTube link.",
            ),
            InputField(
                name="reference_video",
                label="Or Upload Reference Video",
                field_type="file",
                required=False,
                accept="video/*",
            ),
            InputField(
                name="brand_brief",
                label="Your Brand / Product Brief",
                field_type="textarea",
                required=True,
                placeholder="e.g. Organic coffee brand targeting millennials, earthy tones, cozy vibe",
                help_text="The AI will apply the cloned style to this brief.",
            ),
            InputField(
                name="output_type",
                label="What to Generate",
                field_type="select",
                default="full",
                options=[
                    {"value": "images", "label": "Images only"},
                    {"value": "video", "label": "Video only"},
                    {"value": "full", "label": "Full package (images + video + music)"},
                ],
            ),
        ]

    def get_steps(self):
        return [
            "Downloading reference video",
            "Analysing visual style",
            "Extracting style DNA",
            "Generating new content",
            "Packaging assets",
        ]

    def execute(self, inputs, run_id, user_id, on_progress=None,
                brand=None, persona=None):
        self.report_progress(on_progress, 0, "Downloading reference video…")
        # TODO: Wire to tools/analyze_video.py + generation pipeline
        return {"outputs": [{"type": "text", "title": "Coming Soon", "value": "This recipe is under development and will be available soon. Stay tuned!"}], "cost": 0.0}
