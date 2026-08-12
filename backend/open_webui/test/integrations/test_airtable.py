import asyncio
from datetime import date

import pytest

from open_webui.integrations import airtable


def _record(**fields):
    return {"id": "rec-test", "fields": fields}


def test_airtable_record_to_user_profile_maps_all_fields():
    profile = airtable.airtable_record_to_user_profile(
        _record(
            **{
                "Nom": " Dupont ",
                "Prénom": "Élodie",
                "Genre": "Femme",
                "mail oreegami edu": " ELODIE.DUPONT@OREEGAMI.COM ",
                "Région du campus": "Occitanie",
                "Session": "2026",
                "Titre RNCP": "Expert en IA",
                "Nom Entreprise d'alternance": "ODYSS'IA",
                "Début Alternance": "2026-09-01",
                "Fin Alternance": "2027-08-31",
            }
        )
    )

    assert profile == {
        "last_name": "Dupont",
        "first_name": "Élodie",
        "gender": "Femme",
        "oreegami_edu_email": "elodie.dupont@oreegami.com",
        "campus_region": "Occitanie",
        "session": "2026",
        "rncp_title": "Expert en IA",
        "apprenticeship_company": "ODYSS'IA",
        "apprenticeship_start_date": date(2026, 9, 1),
        "apprenticeship_end_date": date(2027, 8, 31),
    }


def test_airtable_record_to_user_profile_rejects_invalid_date():
    with pytest.raises(ValueError, match="Invalid Airtable date"):
        airtable.airtable_record_to_user_profile(
            _record(
                **{
                    "mail oreegami edu": "student@oreegami.com",
                    "Début Alternance": "not-a-date",
                }
            )
        )


def test_airtable_record_to_user_profile_rejects_inverted_date_range():
    with pytest.raises(ValueError, match="end date is before its start date"):
        airtable.airtable_record_to_user_profile(
            _record(
                **{
                    "mail oreegami edu": "student@oreegami.com",
                    "Début Alternance": "2027-09-01",
                    "Fin Alternance": "2027-08-31",
                }
            )
        )


def test_sync_airtable_users_counts_results(monkeypatch):
    records = [
        _record(**{"mail oreegami edu": "updated@oreegami.com"}),
        _record(**{"mail oreegami edu": "unchanged@oreegami.com"}),
        _record(**{"mail oreegami edu": "missing@oreegami.com"}),
        _record(**{"Nom": "No email"}),
        _record(**{"mail oreegami edu": "duplicate@oreegami.com"}),
        _record(**{"mail oreegami edu": "duplicate@oreegami.com"}),
    ]

    async def fake_fetch_airtable_records():
        return records

    class FakeUsersTable:
        def update_user_from_airtable_by_email(self, email, profile):
            if email == "updated@oreegami.com":
                return object(), True
            if email == "unchanged@oreegami.com":
                return object(), False
            return None, False

    monkeypatch.setattr(airtable, "fetch_airtable_records", fake_fetch_airtable_records)
    stats = asyncio.run(airtable.sync_airtable_users(FakeUsersTable()))

    assert stats == airtable.AirtableSyncStats(
        total_records=6,
        matched_users=2,
        updated_users=1,
        unchanged_users=1,
        unmatched_records=1,
        invalid_records=1,
        duplicate_records=2,
    )
