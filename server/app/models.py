import datetime
import uuid
from typing import List

from app.configs.constants import CHAT_ASSIGNMENT, SENTIMENTS
from app.configs.database import Base
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Table,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, relationship

# Association table for Guest-Interest many-to-many relationship
guest_interests = Table(
    "guest_interests",
    Base.metadata,
    Column("guest_id", String, ForeignKey("guests.id", ondelete="CASCADE")),
    Column("interest_id", String, ForeignKey("interests.id", ondelete="CASCADE")),
)

# Association table for Script-Script self-referential many-to-many relationship
script_attachments = Table(
    "script_attachments",
    Base.metadata,
    Column("parent_script_id", String, ForeignKey("scripts.id", ondelete="CASCADE")),
    Column("attached_script_id", String, ForeignKey("scripts.id", ondelete="CASCADE")),
)

# Association table for Script-Sheet many-to-many relationship
script_sheets = Table(
    "script_sheets",
    Base.metadata,
    Column("script_id", String, ForeignKey("scripts.id", ondelete="CASCADE")),
    Column("sheet_id", String, ForeignKey("sheets.id", ondelete="CASCADE")),
)


class Sheet(Base):
    """
    column_config: [
        {
            "column_name": "",
            "column_type": "",
            "description": "",
            "is_index": ""
        }
    ]
    """

    __tablename__ = "sheets"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    column_config = Column(JSONB, nullable=False)
    table_name = Column(String, nullable=True)
    status = Column(String(50), default="published")
    created_at = Column(DateTime, default=datetime.datetime.now)

    # Relationship to Script với cấu hình back_populates rõ ràng
    related_scripts = relationship(
        "Script",
        secondary=script_sheets,
        lazy="select",
        cascade="save-update, merge, expunge",
        back_populates="related_sheets",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "column_config": self.column_config,
            "table_name": self.table_name,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
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


class GuestInfo(Base):
    __tablename__ = "guest_infos"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    fullname = Column(String(255))
    gender = Column(String(20))
    birthday = Column(DateTime)
    phone = Column(String(50))
    email = Column(String(255))
    address = Column(Text)
    updated_at = Column(DateTime, default=datetime.datetime.now)

    # Thêm khóa ngoại guest_id để liên kết với Guest
    guest_id = Column(
        String, ForeignKey("guests.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    # Quan hệ ngược với Guest, chỉ định foreign_keys
    # uselist=False is implicit for one-to-one when guest_id is unique
    guest = relationship("Guest", back_populates="info", foreign_keys=[guest_id])

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


class Guest(Base):
    __tablename__ = "guests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    provider = Column(String(50))  # Đưa provider từ guest_info vào guest
    account_id = Column(String(50))
    account_name = Column(String(100))
    avatar = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.now)
    message_count = Column(Integer, default=0)
    sentiment = Column(String(50), default=SENTIMENTS.NEUTRAL.value)
    assigned_to = Column(String(50), default=CHAT_ASSIGNMENT.AI.value)

    # Foreign Keys for relationships
    last_message_id = Column(
        String, ForeignKey("chats.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    # uselist=False được thêm vào để đảm bảo mối quan hệ một-một từ phía Guest
    info: Mapped[GuestInfo] = relationship(
        "GuestInfo", back_populates="guest", uselist=False
    )

    # Quan hệ với Interest chuyển sang GuestInfo
    interests: Mapped[List["Interest"]] = relationship(
        "Interest", secondary=guest_interests, back_populates="guests", lazy="select"
    )
    last_chat_message: Mapped[Chat] = relationship(
        "Chat", foreign_keys=[last_message_id], uselist=False, lazy="select"
    )

    def to_dict(self, include=None):
        """
        Convert object to dictionary representation

        Args:
            include: Optional list of related objects to include in the output
        """
        if include is None:
            include = []

        # Tạo dict kết quả trước, không truy cập lazy relationship trực tiếp
        result = {
            "id": self.id,
            "provider": self.provider,
            "account_id": self.account_id,
            "account_name": self.account_name,
            "avatar": self.avatar,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "message_count": self.message_count,
            "sentiment": self.sentiment,
            "assigned_to": self.assigned_to,
        }

        # Chỉ truy cập thuộc tính info nếu nó đã được tải trước đó
        # Cách này giúp tránh lỗi greenlet_spawn
        if "info" in include and "info" in self.__dict__ and self.info is not None:
            # Call GuestInfo's to_dict method
            result["info"] = self.info.to_dict()

        if "interests" in include and "interests" in self.__dict__ and self.interests:
            result["interests"] = [
                interest.to_dict(include=[]) for interest in self.interests
            ]

        if (
            "last_chat_message" in include
            and "last_chat_message" in self.__dict__
            and self.last_chat_message
        ):
            result["last_chat_message"] = self.last_chat_message.to_dict()

        return result


class Script(Base):
    __tablename__ = "scripts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    solution = Column(Text, nullable=False)
    status = Column(String(50), default="published")
    created_at = Column(DateTime, default=datetime.datetime.now)

    # Relationship to self for related scripts with cascade delete-orphan
    related_scripts: Mapped[List["Script"]] = relationship(
        "Script",
        secondary=script_attachments,
        primaryjoin=id == script_attachments.c.parent_script_id,
        secondaryjoin=id == script_attachments.c.attached_script_id,
        back_populates="attached_scripts",
        cascade="save-update, merge, expunge",
    )

    # Relationship to access scripts that are attached to this script
    attached_scripts: Mapped[List["Script"]] = relationship(
        "Script",
        secondary=script_attachments,
        primaryjoin=id == script_attachments.c.attached_script_id,
        secondaryjoin=id == script_attachments.c.parent_script_id,
        back_populates="related_scripts",
        cascade="save-update, merge, expunge",
    )

    # Relationship to Sheet với back_populates rõ ràng
    related_sheets: Mapped[List[Sheet]] = relationship(
        "Sheet",
        secondary=script_sheets,
        lazy="select",
        back_populates="related_scripts",
    )

    def to_dict(self, include=None):
        """
        Convert object to dictionary representation

        Args:
            include: Optional list of related objects to include in the output
        """
        if include is None:
            include = []

        result = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "solution": self.solution,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        # Include related scripts if specified
        if "related_scripts" in include and hasattr(self, "related_scripts"):
            result["related_scripts"] = [
                script.to_dict(include=[]) for script in self.related_scripts
            ]

        # Include related sheets if specified
        if "related_sheets" in include and hasattr(self, "related_sheets"):
            result["related_sheets"] = [
                sheet.to_dict() for sheet in self.related_sheets
            ]

        if "attached_scripts" in include and hasattr(self, "attached_scripts"):
            result["attached_scripts"] = [
                script.to_dict(include=[]) for script in self.attached_scripts
            ]

        return result


class Interest(Base):
    __tablename__ = "interests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    related_terms = Column(Text, nullable=False)
    status = Column(String(50), default="published")
    color = Column(String(50), default="#000000")
    created_at = Column(DateTime, default=datetime.datetime.now)

    # Relationship to Guest
    guests: Mapped[List[Guest]] = relationship(
        "Guest", secondary=guest_interests, back_populates="interests", lazy="select"
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
            "color": self.color,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        # Include related objects if specified
        if include is None:
            include = []

        if "guests" in include and self.guests:
            result["guests"] = [guest.to_dict(include=[]) for guest in self.guests]

        return result


class ChatHistory(Base):
    __tablename__ = "chat_histories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    guest_id = Column(String, nullable=False)
    content = Column(LargeBinary, nullable=False)
    summary = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)


class Notification(Base):
    """
    params: [
        {
            "index": "",
            "param_name": "",
            "param_type": "",
            "description": ""
        }
    ]
    """

    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    label = Column(String, nullable=False)
    status = Column(String(50), default="published")
    color = Column(String(50), default="#000000")
    description = Column(Text, nullable=False)
    params = Column(JSONB, nullable=True)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)

    # Relationship to Alert
    alerts = relationship("Alert", back_populates="notification")

    def to_dict(self, include=None):
        if include is None:
            include = []
        result = {
            "id": self.id,
            "label": self.label,
            "status": self.status,
            "color": self.color,
            "description": self.description,
            "params": self.params,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if "alerts" in include and self.alerts:
            result["alerts"] = [alert.to_dict() for alert in self.alerts]
        return result


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    guest_id = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)
    notification_id = Column(String, ForeignKey("notifications.id"))

    # Relationship to Notification
    notification = relationship("Notification", back_populates="alerts")

    def to_dict(self):
        return {
            "id": self.id,
            "guest_id": self.guest_id,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "notification_id": self.notification_id,
        }
