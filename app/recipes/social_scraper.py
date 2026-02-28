"""Social Scraper — extract content & data from any social media post.

Based on the R46 "Ultimate Extract" n8n workflow.
"""

from .base import BaseRecipe, InputField


class SocialScraper(BaseRecipe):
    slug = "social-scraper"
    name = "Social Media Scraper"
    short_description = "Paste any social link — get the video, text, stats, and metadata."
    description = (
        "Paste a link from TikTok, YouTube, Instagram, LinkedIn, X (Twitter), "
        "Reddit, or Meta Ads Library and the AI extracts everything: "
        "video file, caption, hashtags, engagement stats, and more — "
        "saved into a Google Sheet or downloaded as a file."
    )
    category = "research"
    icon = "🔍"
    estimated_cost = "Free"
    is_active = False  # Stub — not yet wired to backend

    how_to_use = """\
### How to use Social Media Scraper

1. **Paste one or more social media URLs** — one per line.
2. **Choose the output** — Google Sheet, CSV download, or both.
3. Click **Extract**.
4. The AI visits each link, grabs the content, and organises it for you.

**Supported platforms:**
- TikTok
- YouTube / YouTube Shorts
- Instagram (posts, reels, stories)
- LinkedIn
- X (Twitter)
- Reddit
- Meta Ads Library

**What you'll get:**
| Field | Example |
|-------|---------|
| Video/Image file | Direct download link |
| Caption | Full text of the post |
| Hashtags | #fitness #workout |
| Views / Likes / Comments | 1.2M / 45K / 320 |
| Author | @username |
| Posted date | 2025-01-15 |

**Tips:**
- Paste up to 20 URLs at once for batch extraction.
- Use this to research competitors or save content for inspiration.
"""

    def get_input_fields(self):
        return [
            InputField(
                name="urls",
                label="Social Media URLs",
                field_type="textarea",
                required=True,
                placeholder="https://www.tiktok.com/@user/video/...\nhttps://www.youtube.com/watch?v=...",
                help_text="Paste one URL per line (up to 20).",
            ),
            InputField(
                name="output_format",
                label="Output Format",
                field_type="select",
                default="csv",
                options=[
                    {"value": "csv", "label": "CSV Download"},
                    {"value": "google_sheet", "label": "Google Sheet"},
                    {"value": "both", "label": "Both"},
                ],
            ),
        ]

    def get_steps(self):
        return [
            "Validating URLs",
            "Extracting content",
            "Organising data",
            "Generating output",
        ]

    def execute(self, inputs, run_id, user_id, on_progress=None,
                brand=None, persona=None):
        self.report_progress(on_progress, 0, "Validating URLs…")
        # TODO: Wire to scraping service
        return {"outputs": [{"type": "text", "title": "Coming Soon", "value": "This recipe is under development and will be available soon. Stay tuned!"}], "cost": 0.0}
