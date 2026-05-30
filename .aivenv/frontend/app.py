import re
import os
from pathlib import Path

import pandas as pd
import requests
import streamlit as st


API_BASE_URL = "http://localhost:8000"


def load_env_file():
    app_file = Path(__file__).resolve()
    app_root = app_file.parents[1]
    project_root = app_file.parents[2]
    env_paths = (
        project_root / ".env",
        app_root / ".env",
        Path.cwd() / ".env",
        Path.cwd() / ".aivenv" / ".env",
    )

    for env_path in env_paths:
        if not env_path.exists():
            continue

        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if not os.environ.get(key):
                os.environ[key] = value


def api_headers():
    api_key = os.getenv("AGENTIC_BI_API_KEY", "").strip()
    if not api_key:
        return {}
    return {"X-API-Key": api_key}


def api_get(path, **params):
    response = requests.get(f"{API_BASE_URL}{path}", params=params, headers=api_headers(), timeout=30)
    response.raise_for_status()
    return response.json()


def api_post(path, payload, timeout=90):
    response = requests.post(f"{API_BASE_URL}{path}", json=payload, headers=api_headers(), timeout=timeout)
    response.raise_for_status()
    return response.json()


def safe_table_name(filename):
    name = re.sub(r"\W+", "_", filename.rsplit(".", 1)[0].lower()).strip("_")
    if not name:
        name = "uploaded_data"
    if name[0].isdigit():
        name = f"data_{name}"
    return name


def read_uploaded_file(uploaded_file):
    filename = uploaded_file.name.lower()
    if filename.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    if filename.endswith(".xlsx"):
        return pd.read_excel(uploaded_file)
    raise ValueError("Upload a CSV or XLSX file.")


def render_chart(df, chart):
    chart_type = chart.get("type", "table")
    if df.empty or chart_type == "table":
        return False

    if chart_type == "metric":
        value_col = chart.get("value")
        if value_col in df.columns:
            st.metric(chart.get("label", value_col), df.iloc[0][value_col])
            return True
        return False

    x_col = chart.get("x")
    y_col = chart.get("y")
    if y_col not in df.columns:
        return False

    chart_df = df.copy()
    chart_df[y_col] = pd.to_numeric(chart_df[y_col], errors="coerce")
    chart_df = chart_df.dropna(subset=[y_col])
    if chart_df.empty:
        return False

    if x_col in df.columns:
        parsed_x = pd.to_datetime(chart_df[x_col], errors="coerce")
        if parsed_x.notna().sum() >= max(1, len(chart_df) // 2):
            chart_df[x_col] = parsed_x
            chart_df = chart_df.sort_values(x_col)
        chart_df = chart_df.set_index(x_col)[[y_col]]
    else:
        chart_df = chart_df[[y_col]]

    if chart_type == "bar":
        st.bar_chart(chart_df)
        return True
    elif chart_type == "line":
        st.line_chart(chart_df)
        return True

    return False


def load_tables():
    try:
        st.session_state.api_error = ""
        return api_get("/tables").get("tables", [])
    except requests.exceptions.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else None
        if status_code == 401:
            st.session_state.api_error = "Backend rejected the API key. Check AGENTIC_BI_API_KEY in .env."
        elif status_code == 500:
            st.session_state.api_error = "Backend authentication is not configured. Add AGENTIC_BI_API_KEY to .env."
        else:
            st.session_state.api_error = f"Backend request failed: {exc}"
        return []
    except requests.exceptions.RequestException:
        st.session_state.api_error = "Backend API is not running on http://localhost:8000."
        return []


st.set_page_config(page_title="Agentic BI Assistant", layout="wide")
st.title("Agentic BI Assistant")
load_env_file()

if not os.getenv("AGENTIC_BI_API_KEY", "").strip():
    st.error("AGENTIC_BI_API_KEY is missing. Add it to the project .env file and restart the backend/frontend.")
    st.stop()

if "history" not in st.session_state:
    st.session_state.history = []

with st.sidebar:
    st.subheader("Datasets")
    tables = load_tables()

    if not tables:
        st.error(st.session_state.get("api_error") or "No datasets available.")
        st.code(r".\.aivenv\Scripts\python.exe -m uvicorn backend.main:app --app-dir .\.aivenv --host 127.0.0.1 --port 8000")
        st.stop()

    if "active_table" not in st.session_state or st.session_state.active_table not in tables:
        st.session_state.active_table = tables[0]

    selected_table = st.selectbox(
        "Active table",
        tables,
        index=tables.index(st.session_state.active_table),
        key="selected_table",
    )
    st.session_state.active_table = selected_table

    uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])
    if uploaded_file is not None:
        try:
            uploaded_df = read_uploaded_file(uploaded_file)
            table_name = st.text_input("Table name", safe_table_name(uploaded_file.name))
        except Exception as exc:
            st.error(f"Could not read file: {exc}")
            st.stop()

        if st.button("Save dataset"):
            rows = uploaded_df.fillna("").to_dict(orient="records")
            result = api_post("/upload", {"table_name": table_name, "rows": rows})
            if result.get("error"):
                st.error(result["error"])
            else:
                st.session_state.active_table = result["table"]
                st.success(f"Saved {result['rows']} rows to {result['table']}.")
                st.rerun()

    st.subheader("Query History")
    for item in reversed(st.session_state.history[-8:]):
        st.caption(item["question"])
        st.code(item["sql"], language="sql")

try:
    schema = api_get("/schema", table=selected_table)
except requests.exceptions.RequestException as exc:
    st.error(f"Could not load schema: {exc}")
    st.stop()

left, right = st.columns([2, 1])

with right:
    st.subheader("Schema")
    schema_df = pd.DataFrame(schema["columns"])
    st.dataframe(schema_df, hide_index=True, use_container_width=True)

    st.subheader("Preview")
    st.dataframe(pd.DataFrame(schema["preview"]), hide_index=True, use_container_width=True)

with left:
    query = st.text_input("Ask your data", placeholder="Show total revenue by region")
    run_clicked = st.button("Run", type="primary")

    if run_clicked:
        if not query.strip():
            st.warning("Enter a question first.")
            st.stop()

        conversation_context = "\n".join(
            f"Q: {item['question']}\nSQL: {item['sql']}"
            for item in st.session_state.history[-3:]
        )

        payload = {
            "question": query,
            "table": selected_table,
            "conversation_context": conversation_context,
            "max_repairs": 1,
        }

        try:
            with st.spinner("Thinking through the data..."):
                data = api_post("/query", payload)
        except requests.exceptions.ConnectionError:
            st.error("Backend API is not running on http://localhost:8000.")
            st.code(r".\.aivenv\Scripts\python.exe -m uvicorn backend.main:app --app-dir .\.aivenv --host 127.0.0.1 --port 8000")
            st.stop()
        except requests.exceptions.RequestException as exc:
            st.error(f"Backend request failed: {exc}")
            st.stop()

        if data.get("error"):
            st.error(data["error"])
            if data.get("sql"):
                st.code(data["sql"], language="sql")
            st.stop()

        sql = data.get("sql", "")
        rows = data.get("data", [])
        df = pd.DataFrame(rows)
        row_count = data.get("row_count", len(rows))

        st.session_state.history.append(
            {
                "question": query,
                "sql": sql,
                "table": selected_table,
            }
        )

        if data.get("repaired"):
            st.info("The agent repaired the SQL after an execution error.")

        st.subheader("Answer")
        if row_count == 0:
            st.warning(
                "The query ran successfully but returned 0 rows. Check that the active table matches your question."
            )
        else:
            chart_rendered = render_chart(df, data.get("chart", {}))
            if not chart_rendered:
                st.info("No chart was generated for this result. Try grouping by a date, product, region, or category.")
            st.dataframe(df, hide_index=True, use_container_width=True)

        st.subheader("Insight")
        st.write(data.get("insight", "No insight available."))

        with st.expander("Agent Plan"):
            plan = data.get("plan", {})
            st.caption(plan.get("intent", "No intent available."))
            for step in plan.get("steps", []):
                st.write(f"- {step}")
            if plan.get("tools"):
                st.caption("Tools: " + ", ".join(plan["tools"]))

        with st.expander("Data Profile"):
            profile = data.get("profile") or {}
            if profile:
                st.caption(
                    f"Sampled rows: {profile.get('row_sample_size', 0)} | "
                    f"Dates: {', '.join(profile.get('date_columns', [])) or 'none'} | "
                    f"Measures: {', '.join(profile.get('measure_columns', [])) or 'none'}"
                )
                profile_df = pd.DataFrame(profile.get("columns", []))
                if not profile_df.empty:
                    st.dataframe(profile_df, hide_index=True, use_container_width=True)
                for note in profile.get("quality_notes", []):
                    st.warning(note)
            else:
                st.write("No profile available.")

        with st.expander("Agent Memory"):
            memories = data.get("memory", [])
            if memories:
                for memory in memories:
                    st.caption(memory.get("created_at", ""))
                    st.write(memory.get("question", ""))
                    st.code(memory.get("sql", ""), language="sql")
            else:
                st.write("No previous memory for this table.")

        st.subheader("Generated SQL")
        st.code(sql, language="sql")
