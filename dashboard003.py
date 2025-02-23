import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 📊 **Dashboard Configuration**
st.set_page_config(page_title="Dashboard Screen 2: Product Categories & Delays", layout="wide")

# 📂 **Uploading CSV file**
st.sidebar.title("📂 Upload Data")
uploaded_file = st.sidebar.file_uploader("Upload a CSV file", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, encoding='latin-1')

    # 📌 **Convert "Shipping date (DateOrders)" to datetime**
    df["Shipping date (DateOrders)"] = pd.to_datetime(df["shipping date (DateOrders)"], errors='coerce')

    # 📌 **Filters**
    st.sidebar.markdown("### 📆 Filters")

    # 🔹 **Filter by Year**
    available_years = df["Shipping date (DateOrders)"].dt.year.dropna().unique()
    selected_years = st.sidebar.multiselect("Select Year", available_years, default=available_years)

    if selected_years:
        df = df[df["Shipping date (DateOrders)"].dt.year.isin(selected_years)]

    # 🔹 **Drilldown to Department**
    st.sidebar.markdown("### 🔍 Drilldown to Product Type")
    departments = df["Department Name"].unique()
    selected_departments = st.sidebar.multiselect("Select Department", departments, default=departments)

    if selected_departments:
        df = df[df["Department Name"].isin(selected_departments)]

    # ⏳ **Calculating delivery delay**
    df["Delay"] = df["Days for shipping (real)"] - df["Days for shipment (scheduled)"]

    # 📌 **Normalize the Delay Values**
    min_delay = df["Delay"].min()
    max_delay = df["Delay"].max()
    df["Normalized Delay"] = df["Delay"]

    # if max_delay != min_delay:  # Avoid division by zero
    #     df["Normalized Delay"] = (df["Delay"] - min_delay) / (max_delay - min_delay)
    # else:
    #     df["Normalized Delay"] = 0.5  # Default mid-value if no variation

    st.markdown("---")
    st.title("📊 Relationship Between Product Categories and Delays")
    st.markdown("---")

    # # 🟢 Normalisation du délai pour obtenir des valeurs entre 0 et 1
    # df["Normalized Delay"] = (df["Delay"] - df["Delay"].min()) / (df["Delay"].max() - df["Delay"].min())

    # 🟢 Création du Treemap
    st.markdown("### 🌳 Delay Ratio by Category & Product")
    fig = px.treemap(
        df,
        path=["Category Name", "Product Name"],  # Catégorie -> Produit
        values="Sales",  # Taille basée sur le retard normalisé
        color="Delay",  # Couleur basée sur le retard normalisé
        color_continuous_scale=[
            "rgb(0, 0, 255)",   # Bleu pour retard faible
            "rgb(255, 255, 255)",  # Blanc pour retard moyen
            "rgb(255, 0, 0)"    # Rouge pour retard élevé
        ],
        # title="📊 Delay Ratio by Category & Product",
        labels={"Delay": "Delay"},
    )

    # 🟢 Améliorations pour un affichage propre
    fig.update_traces(
        hovertemplate="<b>Delay:</b> %{color:.2f} days<extra></extra>",  # ✅ Affiche uniquement le retard
        textinfo="label+percent parent",  # ✅ Affiche Catégorie + % (évite surcharge)
        textfont=dict(size=14),  # ✅ Texte plus grand et lisible
    )

    # 🟢 Ajustements pour **forcer un fond blanc**
    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),  # ✅ Réduit l'espace perdu
        template="plotly_white",  # ✅ Force un thème blanc
    )

    # 🟢 Afficher le graphique dans Streamlit
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("---")

    ## 📊 **2️⃣ Pie Chart - Top 5 Products with Highest Delays**
    st.markdown("### 🏆 Top 5 Products with Highest Delays")

    top_5_delayed_products = df.groupby("Product Name")["Delay"].mean().nlargest(5).reset_index()

    fig = px.pie(
        top_5_delayed_products,
        names="Product Name",
        values="Delay",
        # title="Top 5 Products with Highest Delays",
        color_discrete_sequence=px.colors.qualitative.Set3
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

else:
    st.warning("⚠️ Please upload a CSV file to view the visualizations.")
