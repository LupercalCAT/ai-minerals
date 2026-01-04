import streamlit as st
import pandas as pd
import json
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="O&G Application Dashboard", layout="wide", page_icon="🛢️")

# --- CUSTOM CSS FOR POLISH ---
st.markdown("""
    <style>
        /* Tighten up top padding */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        /* Style the 'Formations' pills */
        .formation-tag {
            background-color: #262730;
            border: 1px solid #4B4B4B;
            border-radius: 15px;
            padding: 4px 12px;
            margin-right: 6px;
            font-size: 0.85rem;
            color: #FAFAFA;
            display: inline-block;
            margin-bottom: 6px;
        }
        /* Style the metrics to look cleaner */
        [data-testid="stMetricValue"] {
            font-size: 1.8rem;
            font-weight: 600;
            color: green;
        }
        /* Custom card styling helper */
        .card-header {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: #FAFAFA;
        }
    </style>
""", unsafe_allow_html=True)

# --- DATA LOADING (Same as before) ---
@st.cache_data
def load_data():
    try:
        with open('application.json', 'r') as f:
            app_meta = json.load(f)
    except FileNotFoundError:
        st.error("⚠️ Critical Error: 'application.json' not found.")
        st.stop()

    parties_map = {}
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
            parties_map[party_name] = {"search_name": party_name, "status_in_unit": "Pending", "narrative": "File not found."}
            
    return app_meta, parties_map

APP_METADATA, PARTIES_DATA = load_data()

# --- DASHBOARD HEADER ---
with st.container(border=True):
    col_head_1, col_head_2 = st.columns([3, 1])
    with col_head_1:
        st.caption("APPLICATION STATUS: SPACING")
        st.title(f"Docket No. {APP_METADATA.get('docket', 'N/A')}")
        st.markdown(f"**Applicant:** {APP_METADATA.get('applicant', 'Unknown')}")
    with col_head_2:
        st.metric("Total Acres", APP_METADATA.get('total_acres', 'N/A'))

st.write("") # Spacer

# --- APPLICATION DETAILS CARD ---
with st.container(border=True):
    st.markdown('<div class="card-header">📍 Application Lands & Scope</div>', unsafe_allow_html=True)
    
    c1, c2 = st.columns([1, 1.5])
    
    with c1:
        st.caption("TARGET FORMATIONS")
        # Render formations as pill tags using HTML
        formations_html = "".join([f'<span class="formation-tag">{f}</span>' for f in APP_METADATA.get('formations', [])])
        st.markdown(formations_html, unsafe_allow_html=True)
        
        st.write("") # Spacer
        st.caption("GENERAL LOCATION")
        st.info(APP_METADATA.get('location_desc', 'N/A'), icon="🗺️")

    with c2:
        st.caption("SECTIONS INVOLVED")
        # Convert list of strings to a clean DataFrame
        sections_data = [{"Section Description": s} for s in APP_METADATA.get('sections', [])]
        st.dataframe(
            pd.DataFrame(sections_data), 
            use_container_width=True, 
            hide_index=True
        )

st.write("") # Spacer

# --- INTERESTED PARTIES SECTION ---
st.markdown("### 👥 Interested Parties Analysis")

main_col_1, main_col_2 = st.columns([1, 2.5])

# LEFT COLUMN: Party Selector
with main_col_1:
    with st.container(border=True):
        st.markdown("#### Select Owner")
        party_names = APP_METADATA.get('parties', [])
        
        if not party_names:
            st.warning("No parties found.")
            st.stop()

        # Initialize selection in session state if needed
        if 'selected_party_name' not in st.session_state:
            st.session_state.selected_party_name = party_names[0]

        # Render list of buttons acting as a menu
        for p in party_names:
            if st.button(
                p, 
                key=f"btn_{p}", 
                use_container_width=True, 
                type="primary" if st.session_state.selected_party_name == p else "secondary"
            ):
                st.session_state.selected_party_name = p
                st.rerun()
        
        # Ensure the generic variable is set for downstream usage
        selected_party_name = st.session_state.selected_party_name
        
        st.divider()
        st.caption(f"Total Parties Tracked: {len(party_names)}")

# RIGHT COLUMN: Party Details
with main_col_2:
    party = PARTIES_DATA.get(selected_party_name, {})
    
    # Party Header Card
    with st.container(border=True):
        h1, h2 = st.columns([3, 1])
        with h1:
            st.subheader(party.get('search_name', selected_party_name))
            st.caption(f"Status: {party.get('status_in_unit', 'Unknown')}")
        with h2:
            st.metric("Net Acres", f"{party.get('total_confirmed_net_mineral_acres', 0):.2f}")

    # Details Tabs
    tab1, tab2, tab3 = st.tabs(["Summary", "Holdings (In Unit)", "Holdings (Outside Unit)"])

    with tab1:
        st.markdown(party.get('narrative', 'No narrative available.'))
        
        addresses = party.get('addresses', [])
        if addresses:
            st.divider()
            st.caption("MAILING ADDRESSES ON RECORD")
            for addr in addresses:
                st.code(addr, language="text")

    with tab2:
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
        else:
            st.info("No confirmed parcels inside the unit.")

    with tab3:
        parcels_out = party.get('consolidated_parcels_outside_area', [])
        if parcels_out:
            df_out = pd.DataFrame(parcels_out)
            st.dataframe(
                df_out,
                column_config={
                    "parcel": "Parcel ID",
                    "description": "Legal Description",
                    "net_mineral_acres": st.column_config.NumberColumn("NMA", format="%.4f")
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.caption("No other holdings identified.")

# Footer
st.markdown("---")
st.markdown("<center><small>Powered by AI Minerals Title Engine</small></center>", unsafe_allow_html=True)