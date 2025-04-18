import datetime
import uuid

from app.configs.constants import CHAT_ASSIGNMENT, SENTIMENTS
from app.configs.database import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB


class FileMetaData(Base):
    __tablename__ = "file_metadata"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    version = Column(Integer, nullable=False)
    mime_type = Column(String, nullable=False)
    schema = Column(String, nullable=True)


class SheetRow(Base):
    __tablename__ = "sheet_rows"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    file_id = Column(
        String, ForeignKey("file_metadata.id", ondelete="CASCADE"), nullable=False
    )
    data = Column(JSONB, nullable=False)


class Guest(Base):
    __tablename__ = "guests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    provider = Column(String(50))
    account_id = Column(String(50))
    account_name = Column(String(100))
    avatar = Column(Text)
    fullname = Column(String(255))
    gender = Column(String(20))
    birthday = Column(DateTime)
    phone = Column(String(50))
    email = Column(String(255))
    address = Column(Text)
    last_message_at = Column(DateTime)  # Using string format
    last_message = Column(JSONB)
    created_at = Column(DateTime, default=datetime.datetime.now)
    message_count = Column(Integer, default=0)
    sentiment = Column(String(50), default=SENTIMENTS.NEUTRAL.value)
    assigned_to = Column(String(50), default=CHAT_ASSIGNMENT.AI.value)

    def to_dict(self):
        return {
            "id": self.id,
            "provider": self.provider,
            "account_id": self.account_id,
            "account_name": self.account_name,
            "avatar": self.avatar,
            "fullname": self.fullname,
            "gender": self.gender,
            "birthday": self.birthday.isoformat() if self.birthday else None,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "last_message_at": (
                self.last_message_at.isoformat() if self.last_message_at else None
            ),
            "last_message": self.last_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "message_count": self.message_count,
            "sentiment": self.sentiment,
            "assigned_to": self.assigned_to,
        }


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
