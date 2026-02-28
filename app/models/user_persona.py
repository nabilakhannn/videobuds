"""UserPersona model — stores a user's brand voice, tone, and personality profile.

Each user can create multiple personas (e.g., one per brand or content style).
The persona powers AI script generation with the user's authentic voice.
"""

import json
from datetime import datetime, timezone
from ..extensions import db


class UserPersona(db.Model):
    __tablename__ = "user_personas"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)  # e.g. "My Professional Voice"
    is_default = db.Column(db.Boolean, default=False)

    # Voice & tone
    tone = db.Column(db.String(60))  # e.g. "casual", "professional", "energetic"
    voice_style = db.Column(db.Text)  # Free-text description of how they speak/write
    bio = db.Column(db.Text)  # What they do, who they are, their story
    industry = db.Column(db.String(120))  # e.g. "SaaS", "E-commerce", "Fitness"
    target_audience = db.Column(db.Text)  # Who they're talking to

    # Structured preferences (stored as JSON)
    brand_keywords_json = db.Column(db.Text, default="[]")  # Words they always use
    avoid_words_json = db.Column(db.Text, default="[]")  # Words they never use
    sample_phrases_json = db.Column(db.Text, default="[]")  # Example phrases in their voice
    writing_guidelines = db.Column(db.Text)  # Dos and don'ts as free text

    # AI-generated summary used to prime the script agent
    ai_prompt_summary = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # --- JSON helpers (same pattern as Brand model) ---

    @property
    def brand_keywords(self):
        return json.loads(self.brand_keywords_json) if self.brand_keywords_json else []

    @brand_keywords.setter
    def brand_keywords(self, value):
        self.brand_keywords_json = json.dumps(value)

    @property
    def avoid_words(self):
        return json.loads(self.avoid_words_json) if self.avoid_words_json else []

    @avoid_words.setter
    def avoid_words(self, value):
        self.avoid_words_json = json.dumps(value)

    @property
    def sample_phrases(self):
        return json.loads(self.sample_phrases_json) if self.sample_phrases_json else []

    @sample_phrases.setter
    def sample_phrases(self, value):
        self.sample_phrases_json = json.dumps(value)

    def __repr__(self):
        return f"<UserPersona {self.id} '{self.name}' user={self.user_id}>"
