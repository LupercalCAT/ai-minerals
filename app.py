import streamlit as st
import pandas as pd
import json
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="Spacing App Dashboard", layout="wide", page_icon="🛢️")

# --- DATA LOADING FUNCTIONS ---
@st.cache_data
def load_data():
    """
    Loads the application metadata and dynamic party files.
    """
    # 1. Load Application Metadata
    try:
        with open('application.json', 'r') as f:
            app_meta = json.load(f)
    except FileNotFoundError:
        st.error("⚠️ Critical Error: 'application.json' not found.")
        st.stop()

    # 2. Load Parties
    # In a production app, you might use os.listdir() to find all 'party_*.json' files
    # For this specific setup, we map the known files.
    parties_map = {}
    
    # We define the specific filenames corresponding to our split
    file_mapping = {
        "Nieblas Stabel Trust": "party_nieblas.json",
        "Alan Watada": "party_watada.json"
    }

    for party_name in app_meta.get('parties', []):
        filename = file_mapping.get(party_name)
        if filename and os.path.exists(filename):
            with open(filename, 'r') as f:
                parties_map[party_name] = json.load(f)
        else:
            # Fallback if a file is missing
            parties_map[party_name] = {
                "search_name": party_name,
                "status_in_unit": "Data Pending",
                "narrative": "File not found.",
                "total_confirmed_net_mineral_acres": 0,
                "addresses": [],
                "consolidated_parcels": [],
                "consolidated_parcels_outside_area": []
            }
            
    return app_meta, parties_map

# Load the data
APP_METADATA, PARTIES_DATA = load_data()

# --- DASHBOARD LAYOUT ---

# 1. HEADER SECTION
st.title("📑 Spacing Application Dashboard")
st.markdown(f"**Docket No:** `{APP_METADATA.get('docket', 'N/A')}` | **Applicant:** {APP_METADATA.get('applicant', 'Unknown')}")

with st.expander("Show Application Lands & Details", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Target Formations")
        st.write(", ".join(APP_METADATA.get('formations', [])))
        st.subheader("Location")
        st.info(APP_METADATA.get('location_desc', ''))
    with c2:
        st.subheader("Sections Involved")
        for s in APP_METADATA.get('sections', []):
            st.code(s, language="text")

st.divider()

# 2. INTERESTED PARTIES SECTION
st.subheader("👥 Interested Parties Analysis")

# Layout: List on Left (1/3), Details on Right (2/3)
col_list, col_details = st.columns([1, 2])

with col_list:
    st.write("Select a party to view mineral ownership:")
    
    # Get list from the loaded JSON
    party_names = APP_METADATA.get('parties', [])
    
    if party_names:
        selected_party_name = st.radio("Parties Identified", party_names, index=0)
        # Quick stats
        st.info(f"Total Parties Tracked: {len(party_names)}")
    else:
        st.warning("No parties listed in application.json")
        st.stop()

with col_details:
    # Get data for selected party
    party = PARTIES_DATA.get(selected_party_name, {})
    
    # Header for the Detail View
    st.markdown(f"### 👤 {party.get('search_name', selected_party_name)}")
    
    # Top Metrics for the Party
    m1, m2, m3 = st.columns(3)
    m1.metric("Net Mineral Acres (In Unit)", f"{party.get('total_confirmed_net_mineral_acres', 0)} NMA")
    m2.metric("Status", party.get('status_in_unit', 'Unknown'))
    m3.metric("Addresses Found", len(party.get('addresses', [])))

    # Tabs for Organization
    tab1, tab2, tab3 = st.tabs(["📄 Narrative", "📍 Parcels (In Unit)", "🗺️ Parcels (Outside Unit)"])

    with tab1:
        st.markdown("**Executive Summary:**")
        st.write(party.get('narrative', 'No narrative available.'))
        
        addresses = party.get('addresses', [])
        if addresses:
            st.markdown("**Mailing Addresses:**")
            for addr in addresses:
                st.code(addr, language="text")

    with tab2:
        st.success(f"**Holdings Inside Spacing Unit ({APP_METADATA.get('docket')})**")
        parcels_in = party.get('consolidated_parcels', [])
        if parcels_in:
            df_in = pd.DataFrame(parcels_in)
            st.dataframe(
                df_in,
                column_config={
                    "parcel": "Parcel ID",
                    "description": "Legal Description",
                    "net_mineral_acres": st.column_config.NumberColumn("NMA", format="%.4f"),
                    "grantor": "Grantor"
                },
                use_container_width=True,
                hide_index=True
            )
