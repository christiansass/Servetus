"""
Migration: schema_version 1 → 2

Changes applied:
  - servitus.schema_version bumped to 2
  - provenance block added to every file that is missing one (all nulls)
  - provenance.session_jsonl_path: null added to files that have session_id
    but are missing session_jsonl_path
"""

EMPTY_PROVENANCE = {
    "session_id": None,
    "session_jsonl": None,
    "session_jsonl_path": None,
    "extracted": None,
}


def up(fm: dict, body: str) -> tuple[dict, str, list[str]]:
    changes = []

    # Ensure servitus block exists
    if "servitus" not in fm or not isinstance(fm["servitus"], dict):
        fm["servitus"] = {}

    # Only process if already at version 1
    current = fm["servitus"].get("schema_version", 0)
    if int(current) != 1:
        return fm, body, changes

    provenance = fm.get("provenance")

    if not isinstance(provenance, dict):
        # File has no provenance block — add one with all nulls
        fm["provenance"] = dict(EMPTY_PROVENANCE)
        changes.append("provenance block added (all null — pre-provenance file)")
    else:
        # File has a partial provenance block — fill in missing fields
        for field, default in EMPTY_PROVENANCE.items():
            if field not in provenance:
                provenance[field] = default
                changes.append(f"provenance.{field}: null (added)")

    # Bump schema version
    fm["servitus"]["schema_version"] = 2
    changes.append("servitus.schema_version: 1 → 2")

    return fm, body, changes
