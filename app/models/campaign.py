"""Campaign model for 30-day content plans."""

from datetime import datetime, timezone
from ..extensions import db


class Campaign(db.Model):
    __tablename__ = "campaigns"

    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey("brands.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default="draft")  # draft, generating, review, approved, exported
    style_preset = db.Column(db.String(50))
    mood_json = db.Column(db.Text)  # Mood board config
    total_cost = db.Column(db.Float, default=0.0)
    post_count = db.Column(db.Integer, default=30)
    intention = db.Column(db.String(100))  # brand_awareness, product_launch, engagement, etc.
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    posts = db.relationship("Post", backref="campaign", lazy="dynamic",
                            order_by="Post.day_number", cascade="all, delete-orphan")
    generations = db.relationship("Generation", backref="campaign", lazy="dynamic")

    @property
    def generated_count(self):
        return self.posts.filter_by(status="generated").count() + \
               self.posts.filter_by(status="approved").count()

    @property
    def approved_count(self):
        return self.posts.filter_by(status="approved").count()
