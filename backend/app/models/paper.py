
import uuid
from datetime import datetime, date
from sqlalchemy import String, Integer, Boolean, Float, Date, DateTime, Text, ForeignKey, func, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.types import UUID
from app.core.database import Base


class Paper(Base):
    __tablename__ = "papers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    title_en: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    abstract: Mapped[str | None] = mapped_column(Text, nullable=True)
    abstract_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    doi: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    arxiv_id: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True, index=True)
    publish_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    citation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pdf_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    language: Mapped[str] = mapped_column(String(20), default="en", nullable=False)
    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    hot_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    sources: Mapped[list["PaperSource"]] = relationship(back_populates="paper", cascade="all, delete-orphan")
    paper_authors: Mapped[list["PaperAuthor"]] = relationship(back_populates="paper", cascade="all, delete-orphan")
    paper_institutions: Mapped[list["PaperInstitution"]] = relationship(back_populates="paper", cascade="all, delete-orphan")
    paper_topics: Mapped[list["PaperTopic"]] = relationship(back_populates="paper", cascade="all, delete-orphan")
    paper_experiments: Mapped[list["PaperExperiment"]] = relationship(back_populates="paper", cascade="all, delete-orphan")
    paper_tags: Mapped[list["PaperTag"]] = relationship(back_populates="paper", cascade="all, delete-orphan")
    ai_summary: Mapped["AISummary | None"] = relationship(back_populates="paper", cascade="all, delete-orphan", uselist=False)
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="paper", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_papers_publish_date", publish_date.desc()),
        Index("idx_papers_relevance_score", relevance_score.desc()),
        Index("idx_papers_hot_score", hot_score.desc()),
    )


class PaperSource(Base):
    __tablename__ = "paper_sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("data_sources.id"), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    paper: Mapped["Paper"] = relationship(back_populates="sources")

    __table_args__ = (
        UniqueConstraint("paper_id", "source_id", name="uq_paper_sources_paper_source"),
    )
