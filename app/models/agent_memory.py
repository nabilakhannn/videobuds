"""Per-brand AI agent memory — stores briefs, preferences, and campaign plans."""

from datetime import datetime, timezone
from ..extensions import db


class AgentMemory(db.Model):
    __tablename__ = "agent_memory"

    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey("brands.id"), index=True, nullable=False)
    memory_type = db.Column(db.String(50), nullable=False)  # brand_brief | preference | campaign_plan
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaigns.id"), nullable=True, index=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<AgentMemory {self.memory_type} brand={self.brand_id}>"
