# Airtable user synchronization

The backend can periodically enrich existing Open WebUI users from an Airtable
table. Airtable is the source of truth for the fields below. The job only updates
an existing user whose Open WebUI `email` or stored `oreegami_edu_email` matches
the Airtable `mail oreegami edu` value (case-insensitive). It does not create or
delete accounts.

## Field mapping

| Airtable column               | Open WebUI `user` column    | Type |
| ----------------------------- | --------------------------- | ---- |
| `Nom`                         | `last_name`                 | text |
| `Prénom`                      | `first_name`                | text |
| `Genre`                       | `gender`                    | text |
| `mail oreegami edu`           | `oreegami_edu_email`        | text |
| `Région du campus`            | `campus_region`             | text |
| `Session`                     | `session`                   | text |
| `Titre RNCP`                  | `rncp_title`                | text |
| `Nom Entreprise d'alternance` | `apprenticeship_company`    | text |
| `Début Alternance`            | `apprenticeship_start_date` | date |
| `Fin Alternance`              | `apprenticeship_end_date`   | date |

Empty Airtable cells clear the corresponding Open WebUI value. Records without
an Oreegami Edu email, records with invalid dates, and duplicate records sharing
the same Oreegami Edu email are skipped. Unmatched records are left untouched so
that authentication data is never created without the normal Open WebUI signup
or SSO flow.

## CRUD interfaces

The ten profile fields are available in every user write path:

- self-service signup and account settings;
- administrator user creation and editing;
- administrator CSV import;
- `POST /api/v1/auths/signup`, `POST /api/v1/auths/add`,
  `POST /api/v1/auths/update/profile`, and
  `POST /api/v1/users/{user_id}/update`.

The administrator user list groups the fields by identity, campus/session,
RNCP title, and apprenticeship, and its search covers all ten values. The CSV
template is served at `/static/user-import.csv`; it keeps the four legacy
columns first, followed by the ten fields in the mapping order above. Dates use
ISO `YYYY-MM-DD` values. Empty strings are stored as `NULL`, email matching is
case-insensitive, and an apprenticeship end date before its start date is
rejected.

When periodic synchronization is enabled, Airtable remains the source of truth:
a later sync can overwrite values changed manually in an interface.

## Configuration

Create an Airtable personal access token with read access to the selected base,
then set:

```dotenv
AIRTABLE_SYNC_ENABLED=true
AIRTABLE_API_TOKEN=pat_your_token
AIRTABLE_BASE_ID=app_your_base_id
AIRTABLE_TABLE_ID=tbl_your_table_id
AIRTABLE_VIEW=
AIRTABLE_SYNC_INTERVAL_SECONDS=3600
AIRTABLE_REQUEST_TIMEOUT_SECONDS=30
```

`AIRTABLE_TABLE_ID` can also contain the table name, although the stable `tbl...`
identifier is recommended. `AIRTABLE_VIEW` is optional. The interval has a
minimum of 60 seconds.

On startup, the database migration adds the nullable profile columns. When
synchronization is enabled, a first import runs immediately and subsequent runs
use `AIRTABLE_SYNC_INTERVAL_SECONDS`. The API token is read only from the
environment and must never be committed.
