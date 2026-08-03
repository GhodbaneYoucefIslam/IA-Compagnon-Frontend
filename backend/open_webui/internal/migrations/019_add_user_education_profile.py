"""Add Oreegami education and apprenticeship fields to users."""

import peewee as pw
from peewee_migrate import Migrator


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    migrator.add_fields(
        "user",
        last_name=pw.CharField(max_length=255, null=True),
        first_name=pw.CharField(max_length=255, null=True),
        gender=pw.CharField(max_length=255, null=True),
        oreegami_edu_email=pw.CharField(max_length=255, null=True),
        campus_region=pw.CharField(max_length=255, null=True),
        session=pw.CharField(max_length=255, null=True),
        rncp_title=pw.CharField(max_length=255, null=True),
        apprenticeship_company=pw.CharField(max_length=255, null=True),
        apprenticeship_start_date=pw.DateField(null=True),
        apprenticeship_end_date=pw.DateField(null=True),
    )


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    migrator.remove_fields(
        "user",
        "last_name",
        "first_name",
        "gender",
        "oreegami_edu_email",
        "campus_region",
        "session",
        "rncp_title",
        "apprenticeship_company",
        "apprenticeship_start_date",
        "apprenticeship_end_date",
    )
