from pydantic import BaseModel

from app.schemas.common import PaginatedResponse


class CampaignSummary(BaseModel):
    id: int
    name: str
    users_count: int
    average_income: float


class CampaignUserOut(BaseModel):
    id: int
    original_id: int
    name: str
    age: int
    city: str
    income: float


class CampaignDetailResponse(BaseModel):
    campaign: CampaignSummary
    users: PaginatedResponse[CampaignUserOut]
