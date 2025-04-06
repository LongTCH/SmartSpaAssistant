from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from app.configs.database import Base
import uuid


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
