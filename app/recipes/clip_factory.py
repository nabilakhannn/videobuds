"""Clip Factory — chop a long video into viral short clips.

Based on the R32 "AI Clip Factory" n8n workflow.
"""

from .base import BaseRecipe, InputField


class ClipFactory(BaseRecipe):
    slug = "clip-factory"
    name = "Clip Factory"
    short_description = "Turn a long video into short, viral-ready clips."
    description = (
        "Upload a long-form video (podcast, webinar, interview, vlog) and "
        "the AI will find the most engaging moments, cut them into short "
        "clips, add captions, and format them for TikTok, Reels, and Shorts."
    )
    category = "repurpose"
    icon = "✂️"
    estimated_cost = "$0.10 – $0.30 per clip"
    is_active = False  # Stub — not yet wired to backend

    how_to_use = """\
### How to use Clip Factory

1. **Upload your video** or paste a YouTube / Vimeo URL.
2. **Set the target clip length** — 15s, 30s, or 60s.
3. **Choose how many clips** you want the AI to find (1–10).
4. Click **Generate** and wait while the AI watches the whole video.
5. Preview each clip, download, or auto-post.

**What happens behind the scenes:**
- Step 1: AI transcribes the full video
- Step 2: AI scores each segment for "viral potential"
- Step 3: Top segments are cut into clips
- Step 4: Captions & formatting are applied
- Step 5: Clips are ready for download

**Tips:**
- Videos under 60 minutes work best.
- Podcasts with dynamic conversations produce the best clips.
"""

    def get_input_fields(self):
        return [
            InputField(
                name="video_source",
                label="Video File or URL",
                field_type="text",
                required=True,
                placeholder="Paste a YouTube URL or upload below",
                help_text="YouTube, Vimeo, or direct video link.",
            ),
            InputField(
                name="video_file",
                label="Or Upload Video",
                field_type="file",
                required=False,
                accept="video/*",
            ),
            InputField(
                name="clip_length",
                label="Target Clip Length",
                field_type="select",
                default="30",
                options=[
                    {"value": "15", "label": "15 seconds"},
                    {"value": "30", "label": "30 seconds"},
                    {"value": "60", "label": "60 seconds"},
                ],
            ),
            InputField(
                name="clip_count",
                label="How many clips?",
                field_type="number",
                default=3,
                min_val=1,
                max_val=10,
            ),
        ]

    def get_steps(self):
        return [
            "Downloading / reading video",
            "Transcribing audio",
            "Finding best moments",
            "Cutting clips",
            "Adding captions",
        ]

    def execute(self, inputs, run_id, user_id, on_progress=None,
                brand=None, persona=None):
        self.report_progress(on_progress, 0, "Downloading / reading video…")
        # TODO: Wire to video processing pipeline
        return {"outputs": [{"type": "text", "title": "Coming Soon", "value": "This recipe is under development and will be available soon. Stay tuned!"}], "cost": 0.0}
