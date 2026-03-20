from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Campaign, User, campaign_users
from app.schemas.campaign import CampaignDetailResponse, CampaignSummary, CampaignUserOut
from app.schemas.common import PaginatedResponse

router = APIRouter()


@router.get(
    "/campaigns",
    response_model=PaginatedResponse[CampaignSummary],
    summary="List all campaigns",
    description="Returns a paginated list of campaigns with user count and average income. "
    "Optionally filter by upload_id.",
)
def list_campaigns(
    upload_id: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(
        Campaign.id,
        Campaign.name,
        func.count(campaign_users.c.user_id).label("users_count"),
        func.coalesce(func.avg(User.income), 0).label("average_income"),
    ).outerjoin(
        campaign_users, Campaign.id == campaign_users.c.campaign_id
    ).outerjoin(
        User, campaign_users.c.user_id == User.id
    ).group_by(Campaign.id, Campaign.name)

    if upload_id:
        query = query.filter(Campaign.upload_id == upload_id)

    count_query = db.query(func.count(Campaign.id))
    if upload_id:
        count_query = count_query.filter(Campaign.upload_id == upload_id)
    total = count_query.scalar()

    results = query.offset((page - 1) * page_size).limit(page_size).all()

    data = [
        CampaignSummary(
            id=r.id,
            name=r.name,
            users_count=r.users_count,
            average_income=round(r.average_income, 2),
        )
        for r in results
    ]

    return PaginatedResponse(data=data, page=page, page_size=page_size, total=total)


@router.get(
    "/campaigns/{campaign_id}",
    response_model=CampaignDetailResponse,
    summary="Get campaign details",
    description="Returns campaign details with a paginated list of users that belong to the campaign.",
)
def get_campaign(
    campaign_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail={
            "error": "not_found",
            "message": f"Campaign with id {campaign_id} was not found",
            "details": None,
        })

    users_count = db.query(func.count(campaign_users.c.user_id)).filter(
        campaign_users.c.campaign_id == campaign_id
    ).scalar()

    avg_income = db.query(func.coalesce(func.avg(User.income), 0)).join(
        campaign_users, User.id == campaign_users.c.user_id
    ).filter(campaign_users.c.campaign_id == campaign_id).scalar()

    total_users = users_count or 0

    users_query = db.query(User).join(
        campaign_users, User.id == campaign_users.c.user_id
    ).filter(campaign_users.c.campaign_id == campaign_id)

    users = users_query.offset((page - 1) * page_size).limit(page_size).all()

    return CampaignDetailResponse(
        campaign=CampaignSummary(
            id=campaign.id,
            name=campaign.name,
            users_count=total_users,
            average_income=round(float(avg_income), 2),
        ),
        users=PaginatedResponse(
            data=[
                CampaignUserOut(
                    id=u.id,
                    original_id=u.original_id,
                    name=u.name,
                    age=u.age,
                    city=u.city,
                    income=u.income,
                )
                for u in users
            ],
            page=page,
            page_size=page_size,
            total=total_users,
        ),
    )
