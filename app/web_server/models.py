import sqlalchemy


# Database table definitions.
metadata = sqlalchemy.MetaData()

reports = sqlalchemy.Table(
    "seizure_reports",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("occurance_date", sqlalchemy.DateTime),
    sqlalchemy.Column("duration_minutes", sqlalchemy.Integer),
    sqlalchemy.Column("drugs_administered", sqlalchemy.BOOLEAN),
    sqlalchemy.Column("details_text", sqlalchemy.TEXT, nullable=True),
    sqlalchemy.Column(
        "hospitalization_required", sqlalchemy.BOOLEAN, default=False, nullable=False
    ),
)
