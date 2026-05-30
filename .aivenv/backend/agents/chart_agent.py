import pandas as pd


def looks_like_date_column(df, column):
    name = column.lower()
    if not any(part in name for part in ["date", "time", "month", "year"]):
        return False

    parsed = pd.to_datetime(df[column], errors="coerce")
    return parsed.notna().sum() >= max(1, len(df) // 2)


def recommend_chart(rows):
    df = pd.DataFrame(rows)
    if df.empty:
        return {"type": "table"}

    numeric_cols = list(df.select_dtypes(include="number").columns)
    non_numeric_cols = [col for col in df.columns if col not in numeric_cols]

    if len(df) == 1 and len(numeric_cols) == 1:
        return {"type": "metric", "value": numeric_cols[0], "label": numeric_cols[0]}

    date_cols = []
    for col in non_numeric_cols:
        if looks_like_date_column(df, col):
            date_cols.append(col)

    if date_cols and numeric_cols:
        return {"type": "line", "x": date_cols[0], "y": numeric_cols[0]}

    if non_numeric_cols and numeric_cols:
        return {"type": "bar", "x": non_numeric_cols[0], "y": numeric_cols[0]}

    if numeric_cols:
        return {"type": "line", "y": numeric_cols[0]}

    return {"type": "table"}
