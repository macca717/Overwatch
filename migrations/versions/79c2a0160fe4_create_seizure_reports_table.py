"""Create seizure reports table

Revision ID: 79c2a0160fe4
Revises: 
Create Date: 2021-10-28 10:12:49.704606

"""
from alembic import op
import sqlalchemy


# revision identifiers, used by Alembic.
revision = "79c2a0160fe4"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "seizure_reports",
        sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
        sqlalchemy.Column("occurance_date", sqlalchemy.DateTime),
        sqlalchemy.Column("duration_minutes", sqlalchemy.Integer),
        sqlalchemy.Column("drugs_administered", sqlalchemy.BOOLEAN),
        sqlalchemy.Column("details_text", sqlalchemy.TEXT, nullable=True),
    )


def downgrade():
    op.drop_table("seizure_reports")
