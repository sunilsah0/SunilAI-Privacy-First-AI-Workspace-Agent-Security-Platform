# Data lifecycle

## Retention

Each person can choose to delete their conversations after N days of inactivity (1 to 3650). A job, `scripts/run_retention.py`, applies the setting. It runs with the limited app account and acts as each person in turn, so it cannot touch anyone else's data. Documents and shared organization content are not covered by retention yet.

## Export

`GET /me/export` (and the **My data** screen) returns one JSON file with the person's documents, conversations, tool permissions, activity log, organization memberships and settings. Search indexes are derived data and are not included. Shared organization documents belong to the organization.

## Deletion

| Data | When you delete your account |
|---|---|
| Your documents, chats, search data, permissions, activity log, settings | Deleted |
| Your organization memberships | Deleted |
| Shared documents you wrote for an organization | Stay with the organization, author name blanked |
| Organization audit entries and break-glass records | Stay as the organization's compliance record, your identity blanked |
| Backups | Not changed until they expire |
| Files outside the app (Ollama model files, operating-system files) | Not managed by the app |

A sole owner of an organization cannot delete their account until another owner exists.

## Deleting a single document or conversation

Deleting a document also deletes its search chunks (database cascade). Deleting a conversation deletes its messages.

## Backups

Deleted data can still exist in older backups. Decide how long you keep backups and write it down. See [BACKUP_RESTORE.md](BACKUP_RESTORE.md).
