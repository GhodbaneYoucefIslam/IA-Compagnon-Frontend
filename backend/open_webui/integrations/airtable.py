import asyncio
import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Optional
from urllib.parse import quote

import aiohttp

from open_webui.env import (
    AIRTABLE_API_TOKEN,
    AIRTABLE_BASE_ID,
    AIRTABLE_REQUEST_TIMEOUT_SECONDS,
    AIRTABLE_SYNC_INTERVAL_SECONDS,
    AIRTABLE_TABLE_ID,
    AIRTABLE_VIEW,
    SRC_LOG_LEVELS,
)


log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["AIRTABLE"])


AIRTABLE_FIELD_MAP = {
    "Nom": "last_name",
    "Prénom": "first_name",
    "Genre": "gender",
    "mail oreegami edu": "oreegami_edu_email",
    "Région du campus": "campus_region",
    "Session": "session",
    "Titre RNCP": "rncp_title",
    "Nom Entreprise d'alternance": "apprenticeship_company",
    "Début Alternance": "apprenticeship_start_date",
    "Fin Alternance": "apprenticeship_end_date",
}

DATE_FIELDS = {"apprenticeship_start_date", "apprenticeship_end_date"}


class AirtableSyncError(RuntimeError):
    pass


@dataclass(frozen=True)
class AirtableSyncStats:
    total_records: int
    matched_users: int
    updated_users: int
    unchanged_users: int
    unmatched_records: int
    invalid_records: int
    duplicate_records: int


def get_missing_airtable_configuration() -> list[str]:
    configuration = {
        "AIRTABLE_API_TOKEN": AIRTABLE_API_TOKEN,
        "AIRTABLE_BASE_ID": AIRTABLE_BASE_ID,
        "AIRTABLE_TABLE_ID": AIRTABLE_TABLE_ID,
    }
    return [name for name, value in configuration.items() if not value]


def _normalize_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, list):
        value = ", ".join(str(item).strip() for item in value if item is not None)
    else:
        value = str(value)

    value = value.strip()
    return value or None


def _normalize_date(value: Any) -> Optional[date]:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError as exc:
            raise ValueError(f"Invalid Airtable date: {value!r}") from exc
    raise ValueError(f"Unsupported Airtable date value: {value!r}")


def airtable_record_to_user_profile(record: dict[str, Any]) -> dict[str, Any]:
    fields = record.get("fields")
    if not isinstance(fields, dict):
        raise ValueError("Airtable record has no fields object")

    profile = {}
    for airtable_field, user_field in AIRTABLE_FIELD_MAP.items():
        value = fields.get(airtable_field)
        profile[user_field] = (
            _normalize_date(value)
            if user_field in DATE_FIELDS
            else _normalize_text(value)
        )

    if profile["oreegami_edu_email"]:
        profile["oreegami_edu_email"] = profile["oreegami_edu_email"].lower()

    if (
        profile["apprenticeship_start_date"]
        and profile["apprenticeship_end_date"]
        and profile["apprenticeship_end_date"]
        < profile["apprenticeship_start_date"]
    ):
        raise ValueError("Airtable apprenticeship end date is before its start date")

    return profile


async def fetch_airtable_records() -> list[dict[str, Any]]:
    table_path = quote(AIRTABLE_TABLE_ID, safe="")
    url = f"https://api.airtable.com/v0/{quote(AIRTABLE_BASE_ID, safe='')}/{table_path}"
    headers = {"Authorization": f"Bearer {AIRTABLE_API_TOKEN}"}
    timeout = aiohttp.ClientTimeout(total=AIRTABLE_REQUEST_TIMEOUT_SECONDS)
    records: list[dict[str, Any]] = []
    offset: Optional[str] = None
    seen_offsets: set[str] = set()

    async with aiohttp.ClientSession(timeout=timeout) as session:
        while True:
            params: list[tuple[str, str]] = [("pageSize", "100")]
            params.extend(("fields[]", field) for field in AIRTABLE_FIELD_MAP)
            if AIRTABLE_VIEW:
                params.append(("view", AIRTABLE_VIEW))
            if offset:
                params.append(("offset", offset))

            async with session.get(url, headers=headers, params=params) as response:
                if response.status >= 400:
                    raise AirtableSyncError(
                        f"Airtable API returned HTTP {response.status}"
                    )
                payload = await response.json(content_type=None)

            page_records = payload.get("records")
            if not isinstance(page_records, list):
                raise AirtableSyncError("Airtable response has no records list")
            records.extend(page_records)

            offset = payload.get("offset")
            if not offset:
                return records
            if offset in seen_offsets:
                raise AirtableSyncError(
                    "Airtable returned a repeated pagination offset"
                )
            seen_offsets.add(offset)


async def sync_airtable_users(users_table=None) -> AirtableSyncStats:
    records = await fetch_airtable_records()

    profiles_by_email: dict[str, list[dict[str, Any]]] = {}
    invalid_records = 0
    for record in records:
        try:
            profile = airtable_record_to_user_profile(record)
        except (TypeError, ValueError):
            invalid_records += 1
            log.warning("Skipping an Airtable record with invalid profile data")
            continue

        email = profile.get("oreegami_edu_email")
        if not email:
            invalid_records += 1
            log.warning("Skipping an Airtable record without an Oreegami Edu email")
            continue
        profiles_by_email.setdefault(email, []).append(profile)

    if users_table is None:
        from open_webui.models.users import Users

        users_table = Users

    matched_users = 0
    updated_users = 0
    unchanged_users = 0
    unmatched_records = 0
    duplicate_records = 0

    for email, profiles in profiles_by_email.items():
        if len(profiles) > 1:
            duplicate_records += len(profiles)
            log.warning(
                "Skipping duplicate Airtable records for the same Oreegami Edu email"
            )
            continue

        user, changed = users_table.update_user_from_airtable_by_email(
            email, profiles[0]
        )
        if user is None:
            unmatched_records += 1
            continue

        matched_users += 1
        if changed:
            updated_users += 1
        else:
            unchanged_users += 1

    stats = AirtableSyncStats(
        total_records=len(records),
        matched_users=matched_users,
        updated_users=updated_users,
        unchanged_users=unchanged_users,
        unmatched_records=unmatched_records,
        invalid_records=invalid_records,
        duplicate_records=duplicate_records,
    )
    log.info(
        "Airtable user sync completed: total=%d matched=%d updated=%d "
        "unchanged=%d unmatched=%d invalid=%d duplicates=%d",
        stats.total_records,
        stats.matched_users,
        stats.updated_users,
        stats.unchanged_users,
        stats.unmatched_records,
        stats.invalid_records,
        stats.duplicate_records,
    )
    return stats


async def periodic_airtable_user_sync():
    missing_configuration = get_missing_airtable_configuration()
    if missing_configuration:
        log.error(
            "Airtable user sync is enabled but configuration is missing: %s",
            ", ".join(missing_configuration),
        )
        return

    while True:
        try:
            await sync_airtable_users()
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("Airtable user sync failed; it will be retried later")

        await asyncio.sleep(AIRTABLE_SYNC_INTERVAL_SECONDS)
