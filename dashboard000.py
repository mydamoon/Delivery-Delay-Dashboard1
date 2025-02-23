import streamlit as st
import pandas as pd
import dashboard002
import dashboard003
import dashboard004

# 📊 **Dashboard Title**
st.set_page_config(page_title="Supply Chain Shipments - Delays", layout="wide")
st.title("📊 Supply Chain Shipments - Delays")

# # 📂 **Upload CSV File**
# st.sidebar.title("📂 Upload Data")
# uploaded_file = st.sidebar.file_uploader("Upload a CSV file", type="csv")

# 📌 **Navigation Menu**
st.sidebar.title("📍 Navigation")
selected_dashboard = st.sidebar.radio("Go to:", 
                                      ["Home", 
                                       "Region & Mode", 
                                       "Product Categories & Delays", 
                                       "Shipping Delays & Profitability"])

# ✅ **Load Data Only Once**
# if uploaded_file is not None:
if True:
    # ✅ **Navigation Logic**
    if selected_dashboard == "Home":
        st.title("🏠 Welcome to the Supply Chain Shipments - Delays Dashboard")
        st.markdown("### Please select a dashboard from the sidebar.")

    elif selected_dashboard == "Region & Mode":
        dashboard002.show_dashboard()

    elif selected_dashboard == "Product Categories & Delays":
        dashboard003.show_dashboard()

    elif selected_dashboard == "Shipping Delays & Profitability":
        dashboard004.show_dashboard()

else:
    st.warning("⚠️ Please upload a CSV file to view the visualizations.")
