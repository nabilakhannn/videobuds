"""Brand model for client brand profiles."""

import json
from datetime import datetime, timezone
from ..extensions import db


class Brand(db.Model):
    __tablename__ = "brands"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    tagline = db.Column(db.String(300))
    logo_path = db.Column(db.String(500))
    colors_json = db.Column(db.Text, default="[]")
    voice_json = db.Column(db.Text, default="{}")
    target_audience = db.Column(db.Text)
    content_pillars = db.Column(db.Text, default="[]")  # JSON array
    visual_style = db.Column(db.Text)
    never_do = db.Column(db.Text)
    hashtags = db.Column(db.Text, default="[]")  # JSON array
    caption_template = db.Column(db.Text)
    brand_doc = db.Column(db.Text)  # Full markdown brand guidelines
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    campaigns = db.relationship("Campaign", backref="brand", lazy="dynamic")
    questionnaire = db.relationship("BrandQuestionnaire", backref="brand", lazy="dynamic")

    @property
    def colors(self):
        return json.loads(self.colors_json) if self.colors_json else []

    @colors.setter
    def colors(self, value):
        self.colors_json = json.dumps(value)

    @property
    def pillars(self):
        return json.loads(self.content_pillars) if self.content_pillars else []

    @pillars.setter
    def pillars(self, value):
        self.content_pillars = json.dumps(value)
