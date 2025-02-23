import streamlit as st
import subprocess

# 📊 **Dashboard Title**
st.set_page_config(page_title="Supply Chain Shipments - Delays", layout="wide")

# 🏠 **Main Title**
st.title("📦 Supply Chain Shipments - Delays")

# 📌 **Create Columns for Buttons**
col1, col2, col3 = st.columns(3)

# 🎯 **Region & Mode Dashboard**
with col1:
    st.markdown("### 📍 Region & Mode")
    if st.button("Go to Region & Mode", key="region_mode"):
        subprocess.run(["streamlit", "run", "dashboard002.py"])

# 📦 **Product Categories Dashboard**
with col2:
    st.markdown("### 🏷️ Product Category")
    if st.button("Go to Product Category", key="product_category"):
        subprocess.run(["streamlit", "run", "dashboard003.py"])

# 💰 **Profitability Analysis Dashboard**
with col3:
    st.markdown("### 💰 Profitability Analysis")
    if st.button("Go to Profitability", key="profitability_analysis"):
        subprocess.run(["streamlit", "run", "dashboard004.py"])

