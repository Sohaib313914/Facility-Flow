# utils/repository.py
"""Database access for the `issues` table (existing schema, no migrations).

The Supabase client is passed in, so the functions can be tested with a fake.
"""
TABLE = "issues"


class IssueUpdateError(RuntimeError):
    """An update did not change any row."""


def fetch_issues(client):
    response = client.table(TABLE).select("*").order("created_at", desc=True).execute()
    return response.data or []


def fetch_issue(client, issue_id):
    response = client.table(TABLE).select("*").eq("id", issue_id).execute()
    return response.data[0] if response.data else None


def update_issue(client, issue_id, fields):
    """Update one issue and confirm that a row was really changed."""
    response = client.table(TABLE).update(fields).eq("id", issue_id).execute()
    if not response.data:
        raise IssueUpdateError(
            f"No changes were saved for issue {issue_id}. "
            "It may have been deleted, or you may not have permission to edit it."
        )
    return response.data[0]


def insert_issue(client, row):
    response = client.table(TABLE).insert(row).execute()
    return response.data[0] if response.data else row
