import pandas as pd

from backend.agents.executor import execute
from backend.db.schema import get_table_schema, quote_identifier


def _column_semantic_type(name, series):
    lower_name = name.lower()
    if any(part in lower_name for part in ["date", "time", "month", "year"]):
        parsed = pd.to_datetime(series, errors="coerce")
        if parsed.notna().sum() >= max(1, len(series) // 2):
            return "date"

    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().sum() >= max(1, len(series) // 2):
        if any(part in lower_name for part in ["sales", "revenue", "amount", "price", "cost", "profit"]):
            return "measure"
        return "number"

    if series.nunique(dropna=True) <= min(30, max(5, len(series) // 4)):
        return "category"

    return "text"


def profile_table(table_name, sample_limit=1000):
    quoted_table = quote_identifier(table_name)
    df = execute(f"SELECT * FROM {quoted_table} LIMIT {int(sample_limit)};")
    schema = get_table_schema(table_name)

    profile = {
        "table": table_name,
        "row_sample_size": len(df),
        "columns": [],
        "date_columns": [],
        "measure_columns": [],
        "category_columns": [],
        "quality_notes": [],
    }

    if df.empty:
        profile["quality_notes"].append("The selected table has no rows in the sampled data.")
        return profile

    for column in df.columns:
        series = df[column]
        missing_count = int(series.isna().sum() + (series.astype(str).str.strip() == "").sum())
        semantic_type = _column_semantic_type(str(column), series)
        examples = [str(value) for value in series.dropna().astype(str).head(3).tolist()]

        column_profile = {
            "name": str(column),
            "declared_type": next((col["type"] for col in schema if col["name"] == column), ""),
            "semantic_type": semantic_type,
            "missing_count": missing_count,
            "unique_count": int(series.nunique(dropna=True)),
            "examples": examples,
        }
        profile["columns"].append(column_profile)

        if semantic_type == "date":
            profile["date_columns"].append(str(column))
        elif semantic_type == "measure":
            profile["measure_columns"].append(str(column))
        elif semantic_type == "category":
            profile["category_columns"].append(str(column))

        if missing_count:
            profile["quality_notes"].append(f"{column} has {missing_count} missing/blank sampled values.")

    if not profile["date_columns"]:
        profile["quality_notes"].append("No obvious date column was detected; trend analysis may need an explicit time column.")
    if not profile["measure_columns"]:
        profile["quality_notes"].append("No obvious sales/revenue measure was detected; numeric questions may need exact column names.")

    return profile


def profile_to_text(profile):
    lines = [
        f"Table profile for {profile['table']}:",
        f"Sampled rows: {profile['row_sample_size']}",
        f"Date columns: {', '.join(profile['date_columns']) or 'none'}",
        f"Measure columns: {', '.join(profile['measure_columns']) or 'none'}",
        f"Category columns: {', '.join(profile['category_columns']) or 'none'}",
    ]
    for column in profile["columns"]:
        lines.append(
            f"- {column['name']}: {column['semantic_type']}, examples={column['examples']}"
        )
    if profile["quality_notes"]:
        lines.append("Quality notes: " + " ".join(profile["quality_notes"]))
    return "\n".join(lines)
