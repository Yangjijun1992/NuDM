"""initial_schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-24
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("username", sa.String(100), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("role", sa.String(20), server_default="user", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "data_sources",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("base_url", sa.String(500), nullable=False),
        sa.Column("api_type", sa.String(50), nullable=False),
        sa.Column("rate_limit", sa.Integer(), server_default="60", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("config", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "crawl_tasks",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_id", sa.UUID(), nullable=False),
        sa.Column("keyword", sa.String(500), nullable=False),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("papers_fetched", sa.Integer(), server_default="0", nullable=False),
        sa.Column("papers_new", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_foreign_key("fk_crawl_tasks_source", "crawl_tasks", "data_sources", ["source_id"], ["id"])

    op.create_table(
        "papers",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.String(1000), nullable=False),
        sa.Column("title_en", sa.String(1000), nullable=True),
        sa.Column("abstract", sa.Text(), nullable=True),
        sa.Column("abstract_en", sa.Text(), nullable=True),
        sa.Column("doi", sa.String(255), unique=True, nullable=True),
        sa.Column("arxiv_id", sa.String(100), unique=True, nullable=True, index=True),
        sa.Column("publish_date", sa.Date(), nullable=True),
        sa.Column("citation_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("pdf_url", sa.String(1000), nullable=True),
        sa.Column("source_url", sa.String(1000), nullable=True),
        sa.Column("language", sa.String(20), server_default="en", nullable=False),
        sa.Column("relevance_score", sa.Float(), nullable=True),
        sa.Column("hot_score", sa.Float(), nullable=True),
        sa.Column("is_hidden", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_papers_publish_date", "papers", [sa.text("publish_date DESC")])
    op.create_index("idx_papers_relevance_score", "papers", [sa.text("relevance_score DESC")])
    op.create_index("idx_papers_hot_score", "papers", [sa.text("hot_score DESC")])

    op.create_table(
        "paper_sources",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("paper_id", sa.UUID(), nullable=False),
        sa.Column("source_id", sa.UUID(), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_paper_sources_paper_source", "paper_sources", ["paper_id", "source_id"])
    op.create_foreign_key("fk_paper_sources_paper", "paper_sources", "papers", ["paper_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_paper_sources_source", "paper_sources", "data_sources", ["source_id"], ["id"])

    op.create_table(
        "authors",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("name_normalized", sa.String(200), nullable=False, index=True),
        sa.Column("affiliation", sa.String(500), nullable=True),
        sa.Column("orcid", sa.String(50), unique=True, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "paper_authors",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("paper_id", sa.UUID(), nullable=False),
        sa.Column("author_id", sa.UUID(), nullable=False),
        sa.Column("author_order", sa.Integer(), nullable=False),
    )
    op.create_unique_constraint("uq_paper_authors_paper_author", "paper_authors", ["paper_id", "author_id"])
    op.create_foreign_key("fk_paper_authors_paper", "paper_authors", "papers", ["paper_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_paper_authors_author", "paper_authors", "authors", ["author_id"], ["id"], ondelete="CASCADE")

    op.create_table(
        "institutions",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(500), unique=True, nullable=False),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "paper_institutions",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("paper_id", sa.UUID(), nullable=False),
        sa.Column("institution_id", sa.UUID(), nullable=False),
    )
    op.create_unique_constraint("uq_paper_institutions_paper_inst", "paper_institutions", ["paper_id", "institution_id"])
    op.create_foreign_key("fk_paper_institutions_paper", "paper_institutions", "papers", ["paper_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_paper_institutions_inst", "paper_institutions", "institutions", ["institution_id"], ["id"], ondelete="CASCADE")

    op.create_table(
        "topics",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(200), unique=True, nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("parent_id", sa.UUID(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("icon", sa.String(100), nullable=True),
        sa.Column("keywords", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("paper_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_foreign_key("fk_topics_parent", "topics", "topics", ["parent_id"], ["id"])

    op.create_table(
        "paper_topics",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("paper_id", sa.UUID(), nullable=False),
        sa.Column("topic_id", sa.UUID(), nullable=False),
        sa.Column("confidence", sa.Float(), server_default="1.0", nullable=False),
        sa.Column("is_ai_classified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_paper_topics_paper_topic", "paper_topics", ["paper_id", "topic_id"])
    op.create_foreign_key("fk_paper_topics_paper", "paper_topics", "papers", ["paper_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_paper_topics_topic", "paper_topics", "topics", ["topic_id"], ["id"], ondelete="CASCADE")

    op.create_table(
        "experiments",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(200), unique=True, nullable=False),
        sa.Column("full_name", sa.String(500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("topic_id", sa.UUID(), nullable=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_foreign_key("fk_experiments_topic", "experiments", "topics", ["topic_id"], ["id"])

    op.create_table(
        "paper_experiments",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("paper_id", sa.UUID(), nullable=False),
        sa.Column("experiment_id", sa.UUID(), nullable=False),
    )
    op.create_unique_constraint("uq_paper_experiments_paper_exp", "paper_experiments", ["paper_id", "experiment_id"])
    op.create_foreign_key("fk_paper_experiments_paper", "paper_experiments", "papers", ["paper_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_paper_experiments_exp", "paper_experiments", "experiments", ["experiment_id"], ["id"], ondelete="CASCADE")

    op.create_table(
        "tags",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "paper_tags",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("paper_id", sa.UUID(), nullable=False),
        sa.Column("tag_id", sa.UUID(), nullable=False),
    )
    op.create_unique_constraint("uq_paper_tags_paper_tag", "paper_tags", ["paper_id", "tag_id"])
    op.create_foreign_key("fk_paper_tags_paper", "paper_tags", "papers", ["paper_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_paper_tags_tag", "paper_tags", "tags", ["tag_id"], ["id"], ondelete="CASCADE")

    op.create_table(
        "ai_summaries",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("paper_id", sa.UUID(), unique=True, nullable=False),
        sa.Column("summary_cn", sa.Text(), nullable=True),
        sa.Column("summary_en", sa.Text(), nullable=True),
        sa.Column("keywords_extracted", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("contribution", sa.Text(), nullable=True),
        sa.Column("method", sa.Text(), nullable=True),
        sa.Column("result", sa.Text(), nullable=True),
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column("tokens_used", sa.Integer(), nullable=True),
        sa.Column("quality_flag", sa.String(20), server_default="unreviewed", nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("reviewed_by", sa.UUID(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key("fk_ai_summaries_paper", "ai_summaries", "papers", ["paper_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_ai_summaries_reviewer", "ai_summaries", "users", ["reviewed_by"], ["id"])

    op.create_table(
        "favorites",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("paper_id", sa.UUID(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_unique_constraint("uq_favorites_user_paper", "favorites", ["user_id", "paper_id"])
    op.create_foreign_key("fk_favorites_user", "favorites", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_favorites_paper", "favorites", "papers", ["paper_id"], ["id"], ondelete="CASCADE")

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("target_id", sa.UUID(), nullable=True),
        sa.Column("keyword", sa.String(500), nullable=True),
        sa.Column("frequency", sa.String(20), server_default="daily", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_foreign_key("fk_subscriptions_user", "subscriptions", "users", ["user_id"], ["id"], ondelete="CASCADE")

    op.create_table(
        "notifications",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("reference_id", sa.UUID(), nullable=True),
        sa.Column("reference_type", sa.String(50), nullable=True),
        sa.Column("is_read", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_notifications_user_unread", "notifications", ["user_id", "is_read", sa.text("created_at DESC")])
    op.create_foreign_key("fk_notifications_user", "notifications", "users", ["user_id"], ["id"], ondelete="CASCADE")

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.UUID(), nullable=True),
        sa.Column("detail", postgresql.JSONB(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_foreign_key("fk_audit_logs_user", "audit_logs", "users", ["user_id"], ["id"])

    op.create_table(
        "human_feedback",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.UUID(), nullable=False),
        sa.Column("feedback_type", sa.String(30), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("resolved_by", sa.UUID(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_foreign_key("fk_human_feedback_user", "human_feedback", "users", ["user_id"], ["id"])
    op.create_foreign_key("fk_human_feedback_resolver", "human_feedback", "users", ["resolved_by"], ["id"])


def downgrade() -> None:
    op.drop_table("human_feedback")
    op.drop_table("audit_logs")
    op.drop_table("notifications")
    op.drop_table("subscriptions")
    op.drop_table("favorites")
    op.drop_table("ai_summaries")
    op.drop_table("paper_tags")
    op.drop_table("tags")
    op.drop_table("paper_experiments")
    op.drop_table("experiments")
    op.drop_table("paper_topics")
    op.drop_table("topics")
    op.drop_table("paper_institutions")
    op.drop_table("institutions")
    op.drop_table("paper_authors")
    op.drop_table("authors")
    op.drop_table("paper_sources")
    op.drop_table("papers")
    op.drop_table("crawl_tasks")
    op.drop_table("data_sources")
    op.drop_table("users")
