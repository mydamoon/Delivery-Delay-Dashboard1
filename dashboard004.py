import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

def show_dashboard():
    # 📊 **Dashboard Title**
    # st.set_page_config(page_title="Impact of Shipping Delays on Profitability and Sales", layout="wide")
    st.title("📊 Impact of Shipping Delays on Profitability and Sales")

    # 📂 **Upload CSV File**
    st.sidebar.title("📂 Upload Data")
    uploaded_file = st.sidebar.file_uploader("Upload a CSV file", type="csv")

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file, encoding='latin-1')

        # 📌 **Convert Date to Datetime**
        df["Shipping date (DateOrders)"] = pd.to_datetime(df["shipping date (DateOrders)"], errors="coerce")

        # 📌 **Filters**
        st.sidebar.markdown("### 🎯 Filters")

        # 📆 **Year, Quarter, Month Filters**
        df["Year"] = df["Shipping date (DateOrders)"].dt.year
        df["Quarter"] = df["Shipping date (DateOrders)"].dt.to_period("Q")
        df["Month"] = df["Shipping date (DateOrders)"].dt.to_period("M")

        # ✅ **Vérifier que "Order Region" et "Year" ne sont pas vides**
        if "Order Region" in df.columns and df["Order Region"].notna().sum() > 0:
            selected_region = st.sidebar.multiselect("🌍 Select Region", list(df["Order Region"].dropna().unique()), default=df["Order Region"].dropna().unique())
        else:
            selected_region = []

        if "Year" in df.columns and df["Year"].notna().sum() > 0:
            selected_year = st.sidebar.multiselect("📆 Select Year", sorted(df["Year"].dropna().unique()), default=df["Year"].dropna().unique())
        else:
            selected_year = []

        # 📌 **Filtrer les données en fonction des sélections**
        if selected_region:
            df = df[df["Order Region"].isin(selected_region)]
        if selected_year:
            df = df[df["Year"].isin(selected_year)]

        # 📌 **Vérification des colonnes nécessaires**
        required_columns = ["Days for shipping (real)", "Days for shipment (scheduled)", "Order Profit Per Order", "Sales", "Customer Segment"]
        if not all(col in df.columns for col in required_columns):
            st.error("Missing required columns in the dataset!")
            st.stop()

        # ✅ **Éviter les divisions par zéro**
        df = df.replace([np.inf, -np.inf], np.nan)  # Remplace les infinis par NaN
        df = df.dropna(subset=["Days for shipping (real)", "Days for shipment (scheduled)", "Order Profit Per Order", "Sales"])

        # ✅ **Calculer les ratios uniquement pour les valeurs valides**
        df = df[df["Days for shipment (scheduled)"] > 0]  # Exclure les valeurs nulles ou 0 pour éviter division par zéro
        df["Delay Ratio"] = df["Days for shipping (real)"] - df["Days for shipment (scheduled)"]
        df["Profit Margin"] = df["Order Profit Per Order"] / df["Sales"]*100

        # ✅ **Créer un DataFrame agrégé pour la Bubble Chart**
        df_bubble = df.groupby("Customer Segment").agg(
            avg_delay_ratio=("Delay Ratio", "mean"),
            avg_profit_margin=("Profit Margin", "mean"),
            total_sales=("Sales", "sum")
        ).reset_index()

        # ✅ **Vérifier s'il y a des valeurs NaN ou vides**
        df_bubble = df_bubble.dropna(subset=["avg_delay_ratio", "avg_profit_margin", "total_sales"])

        if df_bubble.empty:
            st.warning("No data available for the selected filters!")
        else:
            # ✅ **Normalize bubble size** (éviter qu'elles soient trop petites)
            df_bubble["bubble_size"] = ((df_bubble["total_sales"] / df_bubble["total_sales"].max()) * 100 + 10)*3  # +10 pour éviter 0

            # 📊 **Bubble Chart: Profit Margin vs. Delay Ratio**
            st.markdown("### 📈 Profit Margin vs. Delay Ratio by Customer Segment")

            fig = px.scatter(df_bubble,
                             x="avg_delay_ratio",
                             y="avg_profit_margin",
                             size=df_bubble["bubble_size"],
                             color="Customer Segment",
                             hover_data=["Customer Segment", "avg_delay_ratio", "avg_profit_margin", "total_sales"],
                             labels={"avg_delay_ratio": "Delay Ratio", "avg_profit_margin": "Profit Margin"},
                             size_max=100
                             # title="Profit Margin vs. Delay Ratio by Customer Segment"
                             )

            # ✅ **Format Y-Axis as Percentage**
            fig.update_layout(
                yaxis=dict(tickformat=".2f", title="Profit Margin (%)"),
                xaxis=dict(tickformat=".4f"),
                legend_title="Customer Segment"
            )
            fig.update_traces(marker=dict(opacity=0.5, line=dict(width=1, color="black")))  # Add transparency + outline

            st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("⚠️ Please upload a CSV file to view the visualizations.")
