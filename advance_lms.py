import streamlit as st
import pandas as pd
import os
import plotly.express as px

# ------------------- PAGE CONFIG -------------------
st.set_page_config(page_title="✨ Super Advanced LMS Dashboard", layout="wide")

# ------------------- LOAD DATA -------------------
DATA_FILE = "Main.xlsx"

@st.cache_data
def load_data(file):
    df = pd.read_excel(file, engine="openpyxl")
    for col in df.columns:
        if "date" in col.lower():
            df[col] = pd.to_datetime(df[col], errors="coerce")
    df.fillna("", inplace=True)
    return df

if not os.path.exists(DATA_FILE):
    st.error(f"❌ `{DATA_FILE}` not found.")
    st.stop()

df = load_data(DATA_FILE)

# ------------------- SESSION STATE -------------------
if "page" not in st.session_state:
    st.session_state["page"] = "main"

# Resettable states
reset_keys = ["filtered_df", "selected_values", "date_ranges", "page_number", "select_all_state"]
for key in reset_keys:
    if key not in st.session_state:
        if key == "filtered_df":
            st.session_state[key] = df.copy()
        elif key == "selected_values":
            st.session_state[key] = {}
        elif key == "date_ranges":
            st.session_state[key] = {}
        elif key == "page_number":
            st.session_state[key] = 0
        else:
            st.session_state[key] = {}

# ------------------- CUSTOM CSS -------------------
st.markdown(
    """
<style>
.filter-heading { font-size: 18px; font-weight: bold; color: #1f77b4; margin-top: 15px; margin-bottom: 5px; border-bottom: 2px solid #1f77b4; padding-bottom: 3px;}
.small-widget .stTextInput>div>div>input, .small-widget .stMultiSelect>div>div>div>div>div>div>input { font-size: 13px; padding: 3px;}
.stMetric { transition: transform 0.3s ease; }
.stMetric:hover { transform: scale(1.05); }
.dataframe { font-size: 14px; }
</style>
""",
    unsafe_allow_html=True,
)

# ------------------- MAIN DASHBOARD -------------------
def main_page():
    st.markdown("<h1 style='color:#1f77b4;'>🟢 Super Advanced LMS Dashboard</h1>", unsafe_allow_html=True)
    st.sidebar.header("🔍 Filters")

    # Sidebar Navigation
    if st.sidebar.button("📈 Go to Analytics Page"):
        st.session_state["page"] = "analytics"
        st.stop()

    if st.sidebar.button("🧹 Clear Filters"):
        # Reset everything including widget values
        for key in reset_keys:
            if key == "filtered_df":
                st.session_state[key] = df.copy()
            elif key == "selected_values":
                st.session_state[key] = {}
            elif key == "date_ranges":
                st.session_state[key] = {}
            elif key == "page_number":
                st.session_state[key] = 0
            else:
                st.session_state[key] = {}
        st.rerun()   # force UI refresh

    # Start with full df
    filtered_df = df.copy()
    selected_values = st.session_state["selected_values"]
    date_ranges = st.session_state["date_ranges"]
    select_all_state = st.session_state["select_all_state"]

    # ------------------- FILTER LOGIC -------------------
    # Iterate over columns, but update options dynamically
    for col in df.columns:
        st.sidebar.markdown(f'<div class="filter-heading">{col}</div>', unsafe_allow_html=True)

        # Date filter
        if "date" in col.lower():
            min_date, max_date = df[col].min(), df[col].max()
            start_date, end_date = st.sidebar.date_input(
                f"{col} range",
                value=date_ranges.get(col, [min_date, max_date]),
                min_value=min_date,
                max_value=max_date,
                key=f"date_{col}",
            )
            date_ranges[col] = [start_date, end_date]
            filtered_df = filtered_df[
                (filtered_df[col] >= pd.to_datetime(start_date))
                & (filtered_df[col] <= pd.to_datetime(end_date))
            ]
        else:
            # 🔑 Options based on current filtered_df (cascading behavior)
            options = sorted(filtered_df[col].dropna().astype(str).unique())

            # Search box
            search_term = st.sidebar.text_input(f"Search {col}", "", key=f"search_{col}")
            if search_term:
                options = [opt for opt in options if search_term.lower() in opt.lower()]

            # Select all checkbox
            select_all = st.sidebar.checkbox(
                f"Select All {col}",
                key=f"select_all_{col}",
                value=select_all_state.get(col, False),
            )
            select_all_state[col] = select_all

            # Multiselect
            if select_all:
                selected_values[col] = options
            else:
                selected = st.sidebar.multiselect(
                    f"Select {col}",
                    options,
                    default=selected_values.get(col, []),
                    key=f"multi_{col}",
                )
                if selected:
                    selected_values[col] = selected
                elif col in selected_values:
                    selected_values.pop(col)

            # Apply filter immediately
            if col in selected_values and selected_values[col]:
                filtered_df = filtered_df[filtered_df[col].astype(str).isin(selected_values[col])]

    # Save state
    st.session_state["filtered_df"] = filtered_df
    st.session_state["selected_values"] = selected_values
    st.session_state["date_ranges"] = date_ranges
    st.session_state["select_all_state"] = select_all_state

    filtered_df = filtered_df.iloc[::-1].reset_index(drop=True)

    # ------------------- PAGINATION -------------------
    PAGE_SIZE = 1000
    page_number = st.session_state["page_number"]
    start_idx = page_number * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    page_data = filtered_df.iloc[start_idx:end_idx]

    # ------------------- METRICS -------------------
    st.markdown("### 📊 Key Metrics")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Leads", df.shape[0])
    c2.metric("Filtered Leads", filtered_df.shape[0])
    c3.metric("Unique Courses", filtered_df["Course"].nunique() if "Course" in df.columns else 0)
    c4.metric("Unique States", filtered_df["State"].nunique() if "State" in df.columns else 0)

    # ------------------- DOWNLOAD -------------------
    st.markdown("### 💾 Download Data")
    col1, col2 = st.columns(2)
    col1.download_button(
        "Download Filtered Data",
        filtered_df.to_csv(index=False).encode("utf-8"),
        "filtered_data.csv",
    )
    col2.download_button(
        "Download All Data",
        df.to_csv(index=False).encode("utf-8"),
        "all_data.csv",
    )

    # ------------------- TABLE -------------------
    st.markdown(
        f"### 📄 Filtered Data Preview ({start_idx+1} to {min(end_idx, len(filtered_df))} of {len(filtered_df)})"
    )
    st.dataframe(page_data, use_container_width=True)

    # Pagination
    col_prev, col_next = st.columns(2)
    if col_prev.button("⬅️ Previous Page") and page_number > 0:
        st.session_state["page_number"] -= 1
        st.rerun()
    if col_next.button("Next Page ➡️") and end_idx < len(filtered_df):
        st.session_state["page_number"] += 1
        st.rerun()

# ------------------- ANALYTICS PAGE -------------------
def analytics_page():
    st.markdown("<h1 style='color:#1f77b4;'>📈 LMS Dashboard - Analytics</h1>", unsafe_allow_html=True)
    filtered_df = st.session_state["filtered_df"]
    chart_cols = ["Course", "State", "Mode", "Intake Year"]

    for col in chart_cols:
        if col in filtered_df.columns:
            counts = filtered_df[col].value_counts().reset_index()
            counts.columns = [col, "Count"]

            st.subheader(f"Leads by {col}")
            fig_bar = px.bar(counts, x=col, y="Count", color="Count", text="Count")
            fig_bar.update_traces(marker_line_width=1.5, marker_line_color="black")
            fig_pie = px.pie(counts, names=col, values="Count")

            st.plotly_chart(fig_bar, use_container_width=True)
            st.plotly_chart(fig_pie, use_container_width=True)

    if st.button("⬅️ Back to Main Dashboard"):
        st.session_state["page"] = "main"
        st.rerun()

# ------------------- PAGE RENDER -------------------
if st.session_state["page"] == "main":
    main_page()
else:
    analytics_page()
