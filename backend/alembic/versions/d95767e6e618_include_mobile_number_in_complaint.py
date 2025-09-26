"""include mobile number in complaint

Revision ID: d95767e6e618
Revises:
Create Date: 2025-09-19 04:09:11.690635

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d95767e6e618"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "districts",
        sa.Column(
            "id",
            sa.INTEGER(),
            server_default=sa.text("nextval('districts_id_seq'::regclass)"),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("name", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("description", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint("id", name="districts_pkey"),
        sa.UniqueConstraint(
            "name", name="districts_name_key", postgresql_include=[], postgresql_nulls_not_distinct=False
        ),
        postgresql_ignore_search_path=False,
    )
    op.create_table(
        "blocks",
        sa.Column(
            "id",
            sa.INTEGER(),
            server_default=sa.text("nextval('blocks_id_seq'::regclass)"),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("name", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("district_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("description", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(["district_id"], ["districts.id"], name="blocks_district_id_fkey"),
        sa.PrimaryKeyConstraint("id", name="blocks_pkey"),
        sa.UniqueConstraint(
            "name",
            "district_id",
            name="uq_block_name_district",
            postgresql_include=[],
            postgresql_nulls_not_distinct=False,
        ),
        postgresql_ignore_search_path=False,
    )
    op.create_table(
        "villages",
        sa.Column(
            "id",
            sa.INTEGER(),
            server_default=sa.text("nextval('villages_id_seq'::regclass)"),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("name", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("block_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("district_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("description", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(["block_id"], ["blocks.id"], name="villages_block_id_fkey"),
        sa.ForeignKeyConstraint(["district_id"], ["districts.id"], name="villages_district_id_fkey"),
        sa.PrimaryKeyConstraint("id", name="villages_pkey"),
        sa.UniqueConstraint(
            "name", "block_id", name="uq_village_name_block", postgresql_include=[], postgresql_nulls_not_distinct=False
        ),
        postgresql_ignore_search_path=False,
    )
    op.create_table(
        "roles",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("name", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("description", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("roles_pkey")),
        sa.UniqueConstraint(
            "name", name=op.f("roles_name_key"), postgresql_include=[], postgresql_nulls_not_distinct=False
        ),
    )
    op.create_table(
        "users",
        sa.Column(
            "id",
            sa.INTEGER(),
            server_default=sa.text("nextval('users_id_seq'::regclass)"),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("username", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("email", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column("hashed_password", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("is_active", sa.BOOLEAN(), autoincrement=False, nullable=False),
        sa.PrimaryKeyConstraint("id", name="users_pkey"),
        sa.UniqueConstraint(
            "email", name="users_email_key", postgresql_include=[], postgresql_nulls_not_distinct=False
        ),
        sa.UniqueConstraint(
            "username", name="users_username_key", postgresql_include=[], postgresql_nulls_not_distinct=False
        ),
        postgresql_ignore_search_path=False,
    )
    op.create_table(
        "user_position_holders",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("role_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("village_id", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("block_id", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("district_id", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("user_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("first_name", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("middle_name", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column("last_name", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(["block_id"], ["blocks.id"], name=op.f("user_position_holders_block_id_fkey")),
        sa.ForeignKeyConstraint(["district_id"], ["districts.id"], name=op.f("user_position_holders_district_id_fkey")),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], name=op.f("user_position_holders_role_id_fkey")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("user_position_holders_user_id_fkey")),
        sa.ForeignKeyConstraint(["village_id"], ["villages.id"], name=op.f("user_position_holders_village_id_fkey")),
        sa.PrimaryKeyConstraint("id", name=op.f("user_position_holders_pkey")),
    )
    op.create_table(
        "complaint_types",
        sa.Column(
            "id",
            sa.INTEGER(),
            server_default=sa.text("nextval('complaint_types_id_seq'::regclass)"),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("name", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("description", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint("id", name="complaint_types_pkey"),
        sa.UniqueConstraint(
            "name", name="complaint_types_name_key", postgresql_include=[], postgresql_nulls_not_distinct=False
        ),
        postgresql_ignore_search_path=False,
    )

    op.create_table(
        "complaint_statuses",
        sa.Column(
            "id",
            sa.INTEGER(),
            server_default=sa.text("nextval('complaint_statuses_id_seq'::regclass)"),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("name", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("description", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint("id", name="complaint_statuses_pkey"),
        sa.UniqueConstraint(
            "name", name="complaint_statuses_name_key", postgresql_include=[], postgresql_nulls_not_distinct=False
        ),
        postgresql_ignore_search_path=False,
    )
    op.create_table(
        "complaint_type_geographical_eligibilities",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("complaint_type_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("district_id", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("block_id", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("village_id", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("active", sa.BOOLEAN(), server_default=sa.text("true"), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ["block_id"], ["blocks.id"], name=op.f("complaint_type_geographical_eligibilities_block_id_fkey")
        ),
        sa.ForeignKeyConstraint(
            ["complaint_type_id"],
            ["complaint_types.id"],
            name=op.f("complaint_type_geographical_eligibilitie_complaint_type_id_fkey"),
        ),
        sa.ForeignKeyConstraint(
            ["district_id"], ["districts.id"], name=op.f("complaint_type_geographical_eligibilities_district_id_fkey")
        ),
        sa.ForeignKeyConstraint(
            ["village_id"], ["villages.id"], name=op.f("complaint_type_geographical_eligibilities_village_id_fkey")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("complaint_type_geographical_eligibilities_pkey")),
    )
    op.create_table(
        "complaints",
        sa.Column(
            "id",
            sa.INTEGER(),
            server_default=sa.text("nextval('complaints_id_seq'::regclass)"),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("complaint_type_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("village_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("block_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("district_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("description", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("status_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.Column("mobile_number", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(["block_id"], ["blocks.id"], name="complaints_block_id_fkey"),
        sa.ForeignKeyConstraint(
            ["complaint_type_id"], ["complaint_types.id"], name="complaints_complaint_type_id_fkey"
        ),
        sa.ForeignKeyConstraint(["district_id"], ["districts.id"], name="complaints_district_id_fkey"),
        sa.ForeignKeyConstraint(["status_id"], ["complaint_statuses.id"], name="complaints_status_id_fkey"),
        sa.ForeignKeyConstraint(["village_id"], ["villages.id"], name="complaints_village_id_fkey"),
        sa.PrimaryKeyConstraint("id", name="complaints_pkey"),
        postgresql_ignore_search_path=False,
    )
    op.create_table(
        "complaint_comments",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("complaint_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("user_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("comment", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("commented_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], name=op.f("complaint_comments_complaint_id_fkey")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("complaint_comments_user_id_fkey")),
        sa.PrimaryKeyConstraint("id", name=op.f("complaint_comments_pkey")),
    )

    op.create_table(
        "complaint_media",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("complaint_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("media_url", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("uploaded_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], name=op.f("complaint_media_complaint_id_fkey")),
        sa.PrimaryKeyConstraint("id", name=op.f("complaint_media_pkey")),
    )

    op.create_table(
        "complaint_assignments",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("complaint_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("user_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("assigned_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ["complaint_id"], ["complaints.id"], name=op.f("complaint_assignments_complaint_id_fkey")
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("complaint_assignments_user_id_fkey")),
        sa.PrimaryKeyConstraint("id", name=op.f("complaint_assignments_pkey")),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###

    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("complaint_assignments")
    op.drop_table("users")
    op.drop_table("blocks")
    op.drop_table("roles")
    op.drop_table("complaint_media")
    op.drop_table("complaints")
    op.drop_table("districts")
    op.drop_table("villages")
    op.drop_table("complaint_statuses")
    op.drop_table("complaint_comments")
    op.drop_table("complaint_type_geographical_eligibilities")
    op.drop_table("complaint_types")
    op.drop_table("user_position_holders")
    # ### end Alembic commands ###
