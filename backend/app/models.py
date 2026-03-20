import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from app.database import Base

campaign_users = Table(
    "campaign_users",
    Base.metadata,
    Column("campaign_id", Integer, ForeignKey("campaigns.id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
)


def generate_uuid():
    return str(uuid.uuid4())


class Upload(Base):
    __tablename__ = "uploads"

    id = Column(String, primary_key=True, default=generate_uuid)
    filename = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    total_rows = Column(Integer, default=0)
    valid_rows = Column(Integer, default=0)
    invalid_rows = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    processed_at = Column(DateTime, nullable=True)

    users = relationship("User", back_populates="upload")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    original_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    city = Column(String, nullable=False)
    income = Column(Float, nullable=False)
    upload_id = Column(String, ForeignKey("uploads.id"), nullable=False)

    upload = relationship("Upload", back_populates="users")
    campaigns = relationship("Campaign", secondary=campaign_users, back_populates="users")


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    upload_id = Column(String, ForeignKey("uploads.id"), nullable=False)

    users = relationship("User", secondary=campaign_users, back_populates="campaigns")
