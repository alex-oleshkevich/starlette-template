"""users

Revision ID: 9223d07a31d3
Revises:
Create Date: 2024-11-02 18:13:25.998428

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9223d07a31d3"
down_revision = "initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password", sa.String(), nullable=False),
        sa.Column("first_name", sa.String(), server_default="", nullable=False),
        sa.Column("last_name", sa.String(), server_default="", nullable=False),
        sa.Column("photo", sa.String(), server_default="", nullable=False),
        sa.Column("language", sa.String(), server_default="en", nullable=False),
        sa.Column("timezone", sa.String(), server_default="UTC", nullable=False),
        sa.Column("is_service", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("last_sign_in", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("email_confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("users")
    # ### end Alembic commands ###
