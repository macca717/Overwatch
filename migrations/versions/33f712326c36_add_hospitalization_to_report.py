"""Add Hospitalization to Report

Revision ID: 33f712326c36
Revises: 79c2a0160fe4
Create Date: 2021-12-08 07:37:57.129503

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "33f712326c36"
down_revision = "79c2a0160fe4"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("seizure_reports") as batch_op:
        batch_op.add_column(
            sa.Column("hospitalization_required", sa.Boolean(), nullable=True),
        )
    with op.batch_alter_table("seizure_reports") as batch_op:
        batch_op.execute("UPDATE seizure_reports SET hospitalization_required = false")
        batch_op.alter_column("hospitalization_required", nullable=False)


def downgrade():
    with op.batch_alter_table("seizure_reports") as batch_op:
        batch_op.drop_column("hospitalization_required")
