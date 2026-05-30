import re


def validate(sql):
    normalized = sql.strip().upper()
    if normalized.count(";") > 1:
        return False

    normalized = normalized.rstrip(";").strip()
    if not normalized.startswith("SELECT") and not normalized.startswith("WITH"):
        return False

    dangerous = [
        "ATTACH",
        "ALTER",
        "CREATE",
        "DELETE",
        "DETACH",
        "DROP",
        "INSERT",
        "PRAGMA",
        "REINDEX",
        "REPLACE",
        "UPDATE",
        "VACUUM",
    ]
    return not any(re.search(rf"\b{word}\b", normalized) for word in dangerous)
