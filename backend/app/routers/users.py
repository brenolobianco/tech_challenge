from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserOut

router = APIRouter()


@router.get(
    "/users",
    response_model=PaginatedResponse[UserOut],
    summary="List and filter users",
    description="Returns a paginated list of users with optional filters: name (case-insensitive), "
    "age range (min_age, max_age), and income range (min_income, max_income).",
)
def list_users(
    name: str | None = None,
    min_age: int | None = None,
    max_age: int | None = None,
    min_income: float | None = None,
    max_income: float | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(User)

    if name:
        query = query.filter(User.name.ilike(f"%{name}%"))
    if min_age is not None:
        query = query.filter(User.age >= min_age)
    if max_age is not None:
        query = query.filter(User.age <= max_age)
    if min_income is not None:
        query = query.filter(User.income >= min_income)
    if max_income is not None:
        query = query.filter(User.income <= max_income)

    total = query.count()
    users = query.offset((page - 1) * page_size).limit(page_size).all()

    data = [
        UserOut(
            id=u.id,
            original_id=u.original_id,
            name=u.name,
            age=u.age,
            city=u.city,
            income=u.income,
            upload_id=u.upload_id,
        )
        for u in users
    ]

    return PaginatedResponse(data=data, page=page, page_size=page_size, total=total)
