from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from .base import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    original_filename = Column(String, nullable=True)

    source_type = Column(String, nullable=True)  # pdf_text, scanned_pdf, image
    extracted_text = Column(Text, nullable=True)

    report_json = Column(Text, nullable=True)
    xlsx_path = Column(String, nullable=True)

    status = Column(String, default="uploaded")
    # uploaded / text_extracted / formatted / exported / modified / deleted

    deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    delete_reason = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())