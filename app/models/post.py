"""Post model for individual day slots in a campaign."""

from datetime import datetime, timezone
from ..extensions import db


class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaigns.id"), nullable=False, index=True)
    day_number = db.Column(db.Integer, nullable=False)  # 1-30
    scheduled_date = db.Column(db.Date, nullable=False)
    caption = db.Column(db.Text, default="")
    image_prompt = db.Column(db.Text, default="")
    content_pillar = db.Column(db.String(100))
    image_type = db.Column(db.String(50))  # ugc, studio, detail, lifestyle, cgi, flatlay
    image_url = db.Column(db.String(500))
    image_path = db.Column(db.String(500))  # local file path
    status = db.Column(db.String(20), default="draft")  # draft, generating, generated, approved, rejected
    style_preset = db.Column(db.String(50))  # per-post override
    custom_prompt = db.Column(db.Text)  # tier 3: user-written prompt
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    generations = db.relationship("Generation", backref="post", lazy="dynamic")

    __table_args__ = (
        db.UniqueConstraint("campaign_id", "day_number", name="uq_campaign_day"),
    )
