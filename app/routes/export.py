"""Export routes for downloading campaign content."""

import csv
import io
import os
import zipfile
from flask import Blueprint, render_template, send_file, current_app
from flask_login import login_required, current_user
from ..extensions import db
from ..models import Brand, Campaign, Post

export_bp = Blueprint("export", __name__, url_prefix="/export")


@export_bp.route("/campaigns/<int:campaign_id>", methods=["GET"])
@login_required
def preview(campaign_id):
    """Render the export preview page."""
    campaign = Campaign.query.filter_by(
        id=campaign_id, user_id=current_user.id
    ).first_or_404()

    brand = db.session.get(Brand, campaign.brand_id)

    posts = Post.query.filter_by(campaign_id=campaign.id)\
        .order_by(Post.day_number).all()

    # Count exportable posts (those with an image)
    exportable = [p for p in posts if p.image_url or p.image_path]
    total = len(posts)
    exportable_count = len(exportable)

    approved_count = sum(1 for p in posts if p.status == "approved")
    generated_count = sum(1 for p in posts if p.status in ("generated", "approved"))

    return render_template(
        "campaigns/export.html",
        campaign=campaign,
        brand=brand,
        posts=posts,
        export_posts=exportable,
        total=total,
        export_ready_count=exportable_count,
        approved_count=approved_count,
        generated_count=generated_count,
    )


@export_bp.route("/campaigns/<int:campaign_id>", methods=["POST"])
@login_required
def download(campaign_id):
    """Create a ZIP file with images and captions.csv, return as download."""
    campaign = Campaign.query.filter_by(
        id=campaign_id, user_id=current_user.id
    ).first_or_404()

    posts = Post.query.filter_by(campaign_id=campaign.id)\
        .order_by(Post.day_number).all()

    # Create an in-memory ZIP file
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # Build the captions CSV in memory
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(["day", "date", "caption", "filename"])

        for post in posts:
            filename = ""
            date_str = post.scheduled_date.strftime("%Y-%m-%d") if post.scheduled_date else ""

            # Resolve the image file path
            resolved_path = None
            if post.image_path and os.path.exists(post.image_path):
                resolved_path = post.image_path
            elif post.image_url and post.image_url.startswith("/static/"):
                # Resolve /static/... URL to filesystem path
                static_rel = post.image_url[len("/static/"):]
                candidate = os.path.join(current_app.static_folder, static_rel)
                if os.path.exists(candidate):
                    resolved_path = candidate
            elif post.image_url and not post.image_url.startswith("http") and os.path.exists(post.image_url):
                resolved_path = post.image_url

            if resolved_path:
                ext = os.path.splitext(resolved_path)[1] or ".png"
                filename = f"day_{post.day_number:03d}{ext}"
                zf.write(resolved_path, f"images/{filename}")
            elif post.image_url:
                filename = post.image_url

            # Write CSV row for every post (even those without images)
            writer.writerow([
                post.day_number,
                date_str,
                post.caption or "",
                filename,
            ])

        # Add the CSV to the ZIP
        csv_content = csv_buffer.getvalue()
        zf.writestr("captions.csv", csv_content)

    zip_buffer.seek(0)

    # Generate a safe filename
    safe_name = "".join(c if c.isalnum() or c in "-_ " else "" for c in campaign.name)
    safe_name = safe_name.strip().replace(" ", "_") or "campaign"
    download_name = f"{safe_name}_export.zip"

    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name=download_name,
    )
