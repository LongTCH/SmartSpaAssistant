from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from app.configs.database import Base
import uuid
import datetime


class FileMetaData(Base):
    __tablename__ = "file_metadata"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    version = Column(Integer, nullable=False)
    mime_type = Column(String, nullable=False)
    schema = Column(String, nullable=True)


class SheetRow(Base):
    __tablename__ = "sheet_rows"

    id = Column(String, primary_key=True, index=True,
                default=lambda: str(uuid.uuid4()))
    file_id = Column(String, ForeignKey(
        "file_metadata.id", ondelete="CASCADE"), nullable=False)
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

    def to_dict(self):
        return {
            'id': self.id,
            'provider': self.provider,
            'account_id': self.account_id,
            'account_name': self.account_name,
            'avatar': self.avatar,
            'fullname': self.fullname,
            'gender': self.gender,
            'birthday': self.birthday.isoformat() if self.birthday else None,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'last_message_at': self.last_message_at.isoformat() if self.last_message_at else None,
            'last_message': self.last_message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Chat(Base):
    __tablename__ = "chats"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    guest_id = Column(String, ForeignKey(
        "guests.id", ondelete="CASCADE"), nullable=False)
    content = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)
