"""add case lantern automation

Revision ID: d31b9ac7e401
Revises: a4a07e67dfb1
Create Date: 2026-08-17
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d31b9ac7e401"
down_revision: str | None = "a4a07e67dfb1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "media_brands",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("platform", sa.String(length=40), nullable=False),
        sa.Column("handle", sa.String(length=100), nullable=False),
        sa.Column("niche", sa.String(length=200), nullable=False),
        sa.Column("audience", sa.String(length=300), nullable=False),
        sa.Column("bio", sa.String(length=300), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("brand_config", sa.JSON(), nullable=False),
        sa.Column("human_approval_required", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_media_brands_created_at"), "media_brands", ["created_at"], unique=False)
    op.create_index(op.f("ix_media_brands_handle"), "media_brands", ["handle"], unique=False)
    op.create_index(op.f("ix_media_brands_slug"), "media_brands", ["slug"], unique=True)
    op.create_index(op.f("ix_media_brands_status"), "media_brands", ["status"], unique=False)

    op.create_table(
        "story_projects",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("brand_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("story_type", sa.String(length=60), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("hook", sa.String(length=400), nullable=False),
        sa.Column("synopsis", sa.Text(), nullable=False),
        sa.Column("script", sa.Text(), nullable=False),
        sa.Column("caption", sa.Text(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("risk_level", sa.String(length=32), nullable=False),
        sa.Column("factual_confidence", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("quality_report", sa.JSON(), nullable=False),
        sa.Column("visual_plan", sa.JSON(), nullable=False),
        sa.Column("voice_config", sa.JSON(), nullable=False),
        sa.Column("media_uri", sa.Text(), nullable=True),
        sa.Column("export_uri", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["brand_id"], ["media_brands.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_story_projects_brand_id"), "story_projects", ["brand_id"], unique=False)
    op.create_index(op.f("ix_story_projects_created_at"), "story_projects", ["created_at"], unique=False)
    op.create_index("ix_story_projects_queue", "story_projects", ["status", "scheduled_for"], unique=False)
    op.create_index(op.f("ix_story_projects_slug"), "story_projects", ["slug"], unique=True)
    op.create_index(op.f("ix_story_projects_status"), "story_projects", ["status"], unique=False)

    op.create_table(
        "story_sources",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("publisher", sa.String(length=160), nullable=False),
        sa.Column("source_type", sa.String(length=60), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("credibility_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("verified", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["story_projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "url", name="uq_story_source_url"),
    )
    op.create_index(op.f("ix_story_sources_created_at"), "story_sources", ["created_at"], unique=False)
    op.create_index(op.f("ix_story_sources_project_id"), "story_sources", ["project_id"], unique=False)
    op.create_index(op.f("ix_story_sources_source_type"), "story_sources", ["source_type"], unique=False)

    op.create_table(
        "story_claims",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("claim_text", sa.Text(), nullable=False),
        sa.Column("source_ids", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("risk_category", sa.String(length=60), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["story_projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_story_claims_created_at"), "story_claims", ["created_at"], unique=False)
    op.create_index(op.f("ix_story_claims_project_id"), "story_claims", ["project_id"], unique=False)
    op.create_index(op.f("ix_story_claims_status"), "story_claims", ["status"], unique=False)

    op.create_table(
        "social_publications",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("platform", sa.String(length=40), nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("idempotency_key", sa.String(length=100), nullable=False),
        sa.Column("external_id", sa.String(length=160), nullable=True),
        sa.Column("external_url", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["story_projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("platform", "idempotency_key", name="uq_social_publication_key"),
    )
    op.create_index(op.f("ix_social_publications_created_at"), "social_publications", ["created_at"], unique=False)
    op.create_index(op.f("ix_social_publications_platform"), "social_publications", ["platform"], unique=False)
    op.create_index(op.f("ix_social_publications_project_id"), "social_publications", ["project_id"], unique=False)
    op.create_index(op.f("ix_social_publications_status"), "social_publications", ["status"], unique=False)


def downgrade() -> None:
    for table in ("social_publications", "story_claims", "story_sources", "story_projects", "media_brands"):
        op.drop_table(table)
