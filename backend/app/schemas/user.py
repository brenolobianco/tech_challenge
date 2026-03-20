from pydantic import BaseModel


class UserOut(BaseModel):
    id: int
    original_id: int
    name: str
    age: int
    city: str
    income: float
    upload_id: str
