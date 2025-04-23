import datetime
import json
import uuid

from app.configs.constants import CHAT_ASSIGNMENT, SENTIMENTS
from app.configs.database import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

# Association table for Guest-Interest many-to-many relationship
guest_interest = Table(
    "guest_interests",
    Base.metadata,
    Column("guest_id", String, ForeignKey("guests.id", ondelete="CASCADE")),
    Column("interest_id", String, ForeignKey("interests.id", ondelete="CASCADE")),
)


class FileMetaData(Base):
    __tablename__ = "file_metadata"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    version = Column(Integer, nullable=False)
    mime_type = Column(String, nullable=False)
    schema = Column(String, nullable=True)


class Sheet(Base):
    __tablename__ = "sheets"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    schema = Column(String, nullable=True)
    status = Column(String(50), default="published")
    created_at = Column(DateTime, default=datetime.datetime.now)
    sample_rows = Column(JSONB, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "schema": json.loads(self.schema),
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SheetRow(Base):
    __tablename__ = "sheet_rows"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    sheet_id = Column(
        String, ForeignKey("sheets.id", ondelete="CASCADE"), nullable=False
    )
    order = Column(Integer, nullable=False)
    data = Column(JSONB, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "sheet_id": self.sheet_id,
            "order": self.order,
            "data": self.data,
        }


class Guest(Base):
    __tablename__ = "guests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    provider = Column(String(50))  # Đưa provider từ guest_info vào guest
    account_id = Column(String(50))
    # Đưa account_name từ guest_info vào guest
    account_name = Column(String(100))
    avatar = Column(Text)
    last_message_at = Column(DateTime)
    last_message = Column(JSONB)
    created_at = Column(DateTime, default=datetime.datetime.now)
    message_count = Column(Integer, default=0)
    sentiment = Column(String(50), default=SENTIMENTS.NEUTRAL.value)
    assigned_to = Column(String(50), default=CHAT_ASSIGNMENT.AI.value)

    # Thêm quan hệ one-to-one đến GuestInfo
    info_id = Column(String, ForeignKey("guest_infos.id", ondelete="CASCADE"))
    info = relationship("GuestInfo", back_populates="guest", uselist=False)

    # Quan hệ với Interest chuyển sang GuestInfo
    interests = relationship(
        "Interest", secondary=guest_interest, back_populates="guests", lazy="select"
    )

    def to_dict(self, include=None):
        """
        Convert object to dictionary representation

        Args:
            include: Optional list of related objects to include in the output
        """
        if include is None:
            include = []

        # Lấy dữ liệu từ info nếu có, ngược lại dùng None
        info = self.info

        result = {
            "id": self.id,
            "provider": self.provider,  # Lấy trực tiếp từ guest
            "account_id": self.account_id,
            "account_name": self.account_name,  # Lấy trực tiếp từ guest
            "avatar": self.avatar,
            "fullname": info.fullname if info else None,
            "gender": info.gender if info else None,
            "birthday": info.birthday.isoformat() if info and info.birthday else None,
            "phone": info.phone if info else None,
            "email": info.email if info else None,
            "address": info.address if info else None,
            "last_message_at": (
                self.last_message_at.isoformat() if self.last_message_at else None
            ),
            "last_message": self.last_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "message_count": self.message_count,
            "sentiment": self.sentiment,
            "assigned_to": self.assigned_to,
        }

        if "interests" in include and self.interests:
            result["interests"] = [
                interest.to_dict(include=[]) for interest in self.interests
            ]

        return result


class GuestInfo(Base):
    __tablename__ = "guest_infos"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    # Đã loại bỏ provider và account_name
    fullname = Column(String(255))
    gender = Column(String(20))
    birthday = Column(DateTime)
    phone = Column(String(50))
    email = Column(String(255))
    address = Column(Text)
    data = Column(JSONB)  # Trường JSONB cho full-text search
    updated_at = Column(
        DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now
    )  # Thêm trường để trigger hoạt động

    # Quan hệ ngược với Guest
    guest = relationship("Guest", back_populates="info", uselist=False)

    def to_dict(self, include=None):
        """
        Convert object to dictionary representation
        """
        if include is None:
            include = []

        result = {
            "id": self.id,
            "fullname": self.fullname,
            "gender": self.gender,
            "birthday": self.birthday.isoformat() if self.birthday else None,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
        }

        return result


class Chat(Base):
    __tablename__ = "chats"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    guest_id = Column(
        String, ForeignKey("guests.id", ondelete="CASCADE"), nullable=False
    )
    content = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "guest_id": self.guest_id,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Script(Base):
    __tablename__ = "scripts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    solution = Column(Text, nullable=False)
    status = Column(String(50), default="published")
    created_at = Column(DateTime, default=datetime.datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "solution": self.solution,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Interest(Base):
    __tablename__ = "interests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    related_terms = Column(Text, nullable=False)
    status = Column(String(50), default="published")
    created_at = Column(DateTime, default=datetime.datetime.now)

    # Relationship to Guest
    guests = relationship(
        "Guest", secondary=guest_interest, back_populates="interests", lazy="select"
    )

    def to_dict(self, include=None):
        """
        Convert object to dictionary representation

        Args:
            include: Optional list of related objects to include in the output
        """
        result = {
            "id": self.id,
            "name": self.name,
            "related_terms": self.related_terms,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        # Include related objects if specified
        if include is None:
            include = []

        if "guests" in include and self.guests:
            result["guests"] = [guest.to_dict(include=[]) for guest in self.guests]

        return result


# Đã chuyển tất cả các trigger và function definition sang app/configs/init_sql.py
