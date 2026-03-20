import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Campaign, User, campaign_users
from app.services.sse_manager import sse_manager

logger = logging.getLogger(__name__)

SEGMENTATION_RULES = {
    "Starter": lambda u: u.age < 30 and u.income < 3000,
    "Growth": lambda u: 30 <= u.age <= 50 and 3000 <= u.income <= 10000,
    "Premium": lambda u: u.age > 50 or u.income > 10000,
    "High Value Youth": lambda u: u.age < 30 and u.income > 5000,
}


def generate_campaigns(db: Session, upload_id: str) -> None:
    from app.models import Upload

    upload = db.query(Upload).filter(Upload.id == upload_id).first()
    if not upload:
        logger.error("Upload %s not found", upload_id)
        return

    try:
        upload.status = "processing"
        db.commit()
        logger.info("Campaign generation started for upload_id=%s", upload_id)

        sse_manager.publish(upload_id, {
            "status": "processing",
            "upload_id": upload_id,
        })

        users = db.query(User).filter(User.upload_id == upload_id).all()

        db.query(campaign_users).filter(
            campaign_users.c.campaign_id.in_(
                db.query(Campaign.id).filter(Campaign.upload_id == upload_id)
            )
        ).delete(synchronize_session=False)
        db.query(Campaign).filter(Campaign.upload_id == upload_id).delete()
        db.commit()

        campaigns_map = {}
        for name in SEGMENTATION_RULES:
            campaign = Campaign(name=name, upload_id=upload_id)
            db.add(campaign)
            campaigns_map[name] = campaign

        db.flush()

        for user in users:
            for name, rule in SEGMENTATION_RULES.items():
                if rule(user):
                    campaigns_map[name].users.append(user)

        upload.status = "completed"
        upload.processed_at = datetime.now(timezone.utc)
        db.commit()

        for name, campaign in campaigns_map.items():
            logger.info(
                "Campaign '%s' generated with %d users for upload_id=%s",
                name, len(campaign.users), upload_id,
            )

        logger.info("Campaign generation completed for upload_id=%s", upload_id)

        sse_manager.publish(upload_id, {
            "status": "completed",
            "upload_id": upload_id,
            "total_rows": upload.total_rows,
            "valid_rows": upload.valid_rows,
            "invalid_rows": upload.invalid_rows,
            "processed_at": upload.processed_at.isoformat() if upload.processed_at else None,
        })

    except Exception:
        db.rollback()
        upload = db.query(Upload).filter(Upload.id == upload_id).first()
        if upload:
            upload.status = "failed"
            db.commit()

        sse_manager.publish(upload_id, {
            "status": "failed",
            "upload_id": upload_id,
        })

        logger.exception("Campaign generation failed for upload_id=%s", upload_id)
        raise
