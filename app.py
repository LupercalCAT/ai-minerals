import streamlit as st
import pandas as pd
import json

# --- CONFIGURATION ---
st.set_page_config(page_title="AI Minerals - Title Chain", layout="wide", page_icon="🪨")
VALID_TOKENS = ["investor", "demo", "admin"] # ?access=investor

# --- 1. SECURITY (Magic Link) ---
params = st.query_params
user_token = params.get("access", "").lower()

if user_token not in VALID_TOKENS:
    st.error("⛔ Access Denied.")
    st.info("Please use the secure link provided to you.")
    
    # Optional Manual Entry for lost links
    token_input = st.text_input("Enter Access Token:", type="password")
    if token_input.lower() in VALID_TOKENS:
        st.query_params["access"] = token_input.lower()
        st.rerun()
    st.stop()

# --- 2. HEADER ---
st.title("🪨 AI Minerals | Title Chain Engine")
st.markdown(f"**Status:** Connected | **User:** {user_token.upper()}")

# --- 3. DATA INGESTION (Drag & Drop) ---
st.sidebar.header("📁 Load Data")
uploaded_file = st.sidebar.file_uploader("Upload Parcel JSON", type=["json"])

if uploaded_file is None:
    st.info("👈 Upload a JSON file to visualize the title chain.")
    # Show dummy data example if nothing uploaded
    data = [
        {"parcel": "Example-Sec25", "desc": "S/2 NE/4", "type": "ROYALTY (ORRI)", "nra": 16.0, "status": "Active"},
        {"parcel": "Example-Sec25", "desc": "Deep Rights", "type": "WORKING INT", "nra": 0.0, "status": "Excluded"}
    ]
else:
    try:
        data = json.load(uploaded_file)
        # Handle if your JSON is nested (adjust key if needed)
        if isinstance(data, dict) and "parcels" in data:
            data = data["parcels"]
    except Exception as e:
        st.error(f"Error reading JSON: {e}")
        st.stop()

# --- 4. DASHBOARD LOGIC ---
df = pd.DataFrame(data)

# Summary Metrics
col1, col2, col3 = st.columns(3)
if not df.empty and 'nra' in df.columns:
    royalty_df = df[df['type'].astype(str).str.contains('ROYALTY', case=False, na=False)]
    total_nra = royalty_df['nra'].sum()
    col1.metric("Net Royalty Acres (NRA)", f"{total_nra:.2f} ac")
    col2.metric("Parcels Tracked", len(df))
    col3.metric("Data Source", "AI Analysis")

st.divider()

# Visualization
st.subheader("Asset Breakdown")
if not df.empty:
    # Color coding function
    def highlight_type(row):
        color = '#d4edda' if 'ROYALTY' in str(row.get('type', '')).upper() else '#f8d7da'
        return [f'background-color: {color}' for _ in row]

    st.dataframe(
        df.style.apply(highlight_type, axis=1),
        use_container_width=True,
        hide_index=True
    )
else:
    st.warning("JSON loaded but contained no parcel data rows.")