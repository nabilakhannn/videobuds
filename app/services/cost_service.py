"""Cost tracking service for image/video generation billing."""

from tools.config import get_cost
from app.extensions import db
from app.models.generation import Generation


def get_generation_cost(model="nano-banana", provider="google"):
    """Return the retail unit cost for a single generation."""
    return get_cost(model, provider)


def get_user_cost(user_id, use_retail=True):
    """
    Sum generation costs for a user.
    use_retail=True returns retail costs (for regular users).
    use_retail=False returns actual costs (for admins).
    """
    col = Generation.retail_cost if use_retail else Generation.cost
    result = (
        db.session.query(db.func.coalesce(db.func.sum(col), 0.0))
        .filter(Generation.user_id == user_id, Generation.status == "success")
        .scalar()
    )
    return float(result)


def get_campaign_cost(campaign_id, use_retail=True):
    """Sum generation costs for a campaign."""
    col = Generation.retail_cost if use_retail else Generation.cost
    result = (
        db.session.query(db.func.coalesce(db.func.sum(col), 0.0))
        .filter(Generation.campaign_id == campaign_id, Generation.status == "success")
        .scalar()
    )
    return float(result)


def get_brand_cost(brand_id, use_retail=True):
    """Sum generation costs for a brand."""
    col = Generation.retail_cost if use_retail else Generation.cost
    result = (
        db.session.query(db.func.coalesce(db.func.sum(col), 0.0))
        .filter(Generation.brand_id == brand_id, Generation.status == "success")
        .scalar()
    )
    return float(result)


def estimate_campaign_cost(post_count, model="nano-banana", provider="google"):
    """Estimate the retail cost of generating images for a campaign."""
    unit_cost = get_cost(model, provider)
    return unit_cost * post_count
