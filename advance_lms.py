import streamlit as st
import pandas as pd
import os
import plotly.express as px

st.set_page_config(page_title="Super Advanced LMS Dashboard", layout="wide")

# ------------------- LOAD DATA -------------------
DATA_FILE = "Main.xlsx"

@st.cache_data
def load_data(file):
    df = pd.read_excel(file, engine='openpyxl')
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
if 'page' not in st.session_state:
    st.session_state['page'] = "main"

if 'filtered_df' not in st.session_state:
    st.session_state['filtered_df'] = df.copy()

# ------------------- MAIN PAGE -------------------
def main_page():
    st.title("🟢 Super Advanced LMS Dashboard")

    # --- Filters ---
    st.sidebar.header("🔍 Filters")
    filtered_df = df.copy()
    selected_values = {}

    for col in df.columns:
        options = sorted(df[col].dropna().astype(str).unique())
        search_term = st.sidebar.text_input(f"Search in {col}", "", key=f"search_{col}")
        if search_term:
            options = [opt for opt in options if opt.lower().startswith(search_term.lower())]

        select_all = st.sidebar.checkbox(f"Select All in {col}", key=f"select_all_{col}")
        if select_all:
            selected_values[col] = options
        else:
            selected = st.sidebar.multiselect(f"{col}", options, key=f"multi_{col}", default=selected_values.get(col, []))
            if selected:
                selected_values[col] = selected

    # Apply filters
    filtered_df = df.copy()
    for col, vals in selected_values.items():
        if vals:
            filtered_df = filtered_df[filtered_df[col].astype(str).isin([str(v) for v in vals])]
    st.session_state['filtered_df'] = filtered_df

    # --- Metrics ---
    st.markdown("### 📊 Key Metrics")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Leads", df.shape[0])
    c2.metric("Filtered Leads", filtered_df.shape[0])
    c3.metric("Unique Courses", filtered_df['Course'].nunique() if 'Course' in df else 0)
    c4.metric("Unique States", filtered_df['State'].nunique() if 'State' in df else 0)

    # --- Table ---
    st.markdown("### 📄 Filtered Data")
    st.dataframe(filtered_df.head(1000), use_container_width=True)

    # --- Navigation ---
    st.markdown("---")
    if st.button("📈 Go to Analytics Page"):
        st.session_state['page'] = "analytics"

# ------------------- ANALYTICS PAGE -------------------
def analytics_page():
    st.title("📈 LMS Dashboard - Analytics Page")

    filtered_df = st.session_state['filtered_df']

    chart_cols = ['Course', 'State', 'Mode', 'Intake Year']
    for col in chart_cols:
        if col in filtered_df.columns:
            counts = filtered_df[col].value_counts().reset_index()
            counts.columns = [col, "Count"]

            st.subheader(f"Leads by {col}")
            fig_bar = px.bar(counts, x=col, y="Count", color="Count")
            fig_pie = px.pie(counts, names=col, values="Count")
            st.plotly_chart(fig_bar, use_container_width=True)
            st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")
    if st.button("⬅️ Back to Main Dashboard"):
        st.session_state['page'] = "main"

# ------------------- PAGE RENDERING -------------------
if st.session_state['page'] == "main":
    main_page()
elif st.session_state['page'] == "analytics":
    analytics_page()
