import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
import itertools
import os

st.set_page_config(page_title="LMS Dashboard - Analytics", layout="wide")
st.title("📈 LMS Dashboard - Analytics Page")

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

# ------------------- SIDEBAR FILTERS -------------------
st.sidebar.header("🔍 Filters (Analytics Page)")
filtered_df = df.copy()
selected_values = {}

def apply_filters(df, selections):
    temp_df = df
    for col, vals in selections.items():
        if vals:
            temp_df = temp_df[temp_df[col].astype(str).isin([str(v) for v in vals])]
    return temp_df

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

filtered_df = apply_filters(df, selected_values)
st.session_state['filtered_df'] = filtered_df  # Share filtered data with main page if needed

# ------------------- BACK BUTTON -------------------
st.markdown("---")
if st.button("⬅️ Back to Main Dashboard"):
    st.session_state['page'] = "main"

# ------------------- ANALYTICS -------------------
st.header("📊 Analytics & Reports")
chart_cols = ['Course', 'State', 'Mode', 'Intake Year', 'Counsellor', 'Target Country']

for col in chart_cols:
    if col in filtered_df.columns:
        counts = filtered_df[col].value_counts().reset_index()
        counts.columns = [col, "Count"]

        st.subheader(f"Leads by {col}")

        # Bar chart
        fig_bar = px.bar(counts, x=col, y="Count", color="Count", text="Count", title=f"Leads by {col}")
        fig_bar.update_layout(xaxis_title=col, yaxis_title="Count")
        st.plotly_chart(fig_bar, use_container_width=True)

        # Pie chart
        fig_pie = px.pie(counts, names=col, values="Count", title=f"{col} Distribution")
        st.plotly_chart(fig_pie, use_container_width=True)

# ------------------- PREDICTION & LEAD CONVERSION -------------------
pred_cols = ['Course', 'State', 'Mode', 'Intake Year']
target_col = "Number_Course"

# Train regressor
@st.cache_data
def train_regressor(df):
    df = df.dropna(subset=pred_cols + [target_col]).copy()
    df[target_col] = pd.to_numeric(df[target_col].astype(str).str.extract(r'(\d+\.?\d*)')[0], errors='coerce')
    df = df.dropna(subset=[target_col])
    if df.empty: return None, None

    le_dict = {}
    X = pd.DataFrame()
    for col in pred_cols:
        le = LabelEncoder()
        X[col] = le.fit_transform(df[col])
        le_dict[col] = le
    y = df[target_col].astype(float)

    model = RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)
    model.fit(X, y)
    return model, le_dict

reg_model, reg_le_dict = train_regressor(filtered_df)

if reg_model:
    st.subheader("🔮 Predict Future Lead Counts")
    new_entry = {col: st.multiselect(f"{col}", filtered_df[col].unique().tolist()) for col in pred_cols}
    if st.button("Predict Future Leads"):
        combos = list(itertools.product(*[new_entry[col] for col in pred_cols if new_entry[col]]))
        if combos:
            pred_X = pd.DataFrame([{col: reg_le_dict[col].transform([val])[0] for col, val in zip(pred_cols, combo)} for combo in combos])
            predictions = reg_model.predict(pred_X)
            results = pd.DataFrame(list(combos), columns=pred_cols)
            results["Predicted Leads"] = predictions
            st.dataframe(results.sort_values("Predicted Leads", ascending=False), use_container_width=True)
            st.download_button("📥 Download Predictions", results.to_csv(index=False).encode("utf-8"), "predicted_leads.csv")
