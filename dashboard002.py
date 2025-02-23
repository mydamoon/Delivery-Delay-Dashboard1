import streamlit as st
import pandas as pd
import folium
import matplotlib.pyplot as plt
import numpy as np
from streamlit_folium import st_folium
from folium.plugins import HeatMap
import branca.colormap as cm
import json
import requests
import os

# 📂 **Loading the JSON file containing country translations**
translation_file = "country_translation.json"

if os.path.exists(translation_file):
    with open(translation_file, "r", encoding="utf-8") as f:
        country_translation = json.load(f)
else:
    st.error("⚠️ File country_translation.json not found! Make sure it is in the script folder.")
    st.stop()

# 📌 **Loading country borders via GeoJSON**
geojson_url = "https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json"
geojson_data = requests.get(geojson_url).json()

# 📊 **Dashboard Configuration**
st.set_page_config(page_title="Dashboard - Delivery Delays", layout="wide")

# 📂 **Uploading CSV file**
st.sidebar.title("📂 Upload Data")
uploaded_file = st.sidebar.file_uploader("Upload a CSV file", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, encoding='latin-1')

    # 📌 **Convert "Shipping date (DateOrders)" to datetime**
    df["Shipping date (DateOrders)"] = pd.to_datetime(df["shipping date (DateOrders)"], errors='coerce')

    # 📌 **Add year filter**
    st.sidebar.markdown("### 📆 Filter by Year")
    available_years = df["Shipping date (DateOrders)"].dt.year.dropna().unique()
    selected_year = st.sidebar.selectbox("Select Year", ["All"] + sorted(available_years))

    # Apply year filter
    if selected_year != "All":
        df = df[df["Shipping date (DateOrders)"].dt.year == selected_year]

    # 📌 **Adding dynamic filters**
    st.sidebar.markdown("### 🎯 Available Filters")

    filters = {
        "Type": st.sidebar.selectbox("Transaction Type", ["All"] + list(df["Type"].unique())),
        "Category Name": st.sidebar.selectbox("Product Category", ["All"] + list(df["Category Name"].unique())),
        "Department Name": st.sidebar.selectbox("Department", ["All"] + list(df["Department Name"].unique())),
        "Market": st.sidebar.selectbox("Market", ["All"] + list(df["Market"].unique())),
        "Order Region": st.sidebar.selectbox("Order Region", ["All"] + list(df["Order Region"].unique())),
        "Product Name": st.sidebar.selectbox("Product Name", ["All"] + list(df["Product Name"].unique())),
        "Shipping Mode": st.sidebar.selectbox("Shipping Mode", ["All"] + list(df["Shipping Mode"].unique()))
    }

    # 📌 **Applying filters**
    for col, value in filters.items():
        if value != "All":
            df = df[df[col] == value]

    # 📌 **Converting geographic coordinates**
    df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
    df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")
    df = df.dropna(subset=["Latitude", "Longitude"])

    # ⏳ **Calculating delivery delay**
    df["Delay"] = df["Days for shipping (real)"] - df["Days for shipment (scheduled)"]

    # 📌 **Categorizing delay levels**
    df["Delay Category"] = pd.cut(df["Delay"], bins=[-np.inf, -1, 1, np.inf], labels=["Low", "Medium", "High"])

    # 📌 **Client delivery delays (Delivery Point Map)**
    abs_max_clients = df["Delay"].max()
    abs_min_clients = df["Delay"].min()
    df["norm_delay"] = (
        (df["Delay"] - abs_min_clients) / (abs_max_clients - abs_min_clients) if abs_max_clients != abs_min_clients else 0.5
    )

    # 📌 **Average delays by country**
    df["Order Country"] = df["Order Country"].map(country_translation).fillna(df["Order Country"])
    df_country_avg = df.groupby("Order Country")["Delay"].mean().reset_index()
    abs_max_countries = df_country_avg["Delay"].max()
    abs_min_countries = df_country_avg["Delay"].min()
    country_delay_dict = dict(zip(df_country_avg["Order Country"], df_country_avg["Delay"]))

    # 🎨 **Defining colormaps**
    colormap_clients = cm.LinearColormap(
        colors=["blue", "green", "red"],
        index=[abs_min_clients, 0, abs_max_clients],
        vmin=abs_min_clients, vmax=abs_max_clients,
        caption="⏳ Delivery Delay (days)"
    )

    colormap_countries = cm.LinearColormap(
        colors=["blue", "green", "red"],
        index=[abs_min_countries, 0, abs_max_countries],
        vmin=abs_min_countries, vmax=abs_max_countries,
        caption="⏳ Average Delivery Delay (days)"
    )

    def country_color(feature):
        country_name = feature["properties"]["name"]
        delay = country_delay_dict.get(country_name, None)
        if delay is None:
            return {"fillColor": "gray", "color": "black", "weight": 0.5, "fillOpacity": 0.3}
        return {
            "fillColor": colormap_countries(delay),
            "color": "black",
            "weight": 0.5,
            "fillOpacity": 0.3
        }

    st.markdown("---")
    st.title("📊 Dashboard - Delivery Delays")
    st.markdown("---")
    ## 🗺️ **1️⃣ Client Map | Country Map**
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🗺️ Heatmap of Delivery Delays (Inbound Logistics)")
        m = folium.Map(location=[df["Latitude"].mean(), df["Longitude"].mean()], zoom_start=4)
        heat_data = df[["Latitude", "Longitude", "norm_delay"]].values.tolist()
        HeatMap(heat_data, gradient={"0.0": "blue", "0.5": "green", "1.0": "red"}, radius=10, blur=10, min_opacity=0.5).add_to(m)
        colormap_clients.add_to(m)
        st_folium(m, width="100%", height=500)

    # with col2:
    #     st.markdown("### 🌍 Average Delivery Delays by Country")
    #     m3 = folium.Map(location=[20, 0], zoom_start=2)
    #     folium.GeoJson(
    #         geojson_data,
    #         style_function=country_color,
    #         tooltip=folium.GeoJsonTooltip(fields=["name"], aliases=["Country"])
    #     ).add_to(m3)
    #     colormap_countries.add_to(m3)
    #     st_folium(m3, width="100%", height=500)

    with col2:
        st.markdown("### 🌍 Average Delivery Delays by Country (Outbound Logistics)")
        
        # Création de la carte Folium
        m3 = folium.Map(location=[20, 0], zoom_start=2)

        # Ajouter les informations de retard moyen arrondi dans le GeoJSON
        for feature in geojson_data["features"]:
            country_name = feature["properties"]["name"]
            delay = country_delay_dict.get(country_name, None)

            # Vérifier si on a une valeur de retard valide, sinon afficher "No data"
            if delay is not None:
                feature["properties"]["delay"] = f"{round(delay, 2)} days"
            else:
                feature["properties"]["delay"] = "No data"

        # Ajouter le GeoJSON avec le tooltip
        folium.GeoJson(
            geojson_data,
            style_function=country_color,
            tooltip=folium.GeoJsonTooltip(
                fields=["name", "delay"],
                aliases=["Country", "Avg Delay (days)"]
            )
        ).add_to(m3)

        # Ajouter la légende
        colormap_countries.add_to(m3)

        # Afficher la carte avec Streamlit
        st_folium(m3, width="100%", height=500)

    st.markdown("---")

    # ## 📊 **2️⃣ Client Histogram | Country Histogram**
    # col3, col4 = st.columns(2)

    # with col3:
    #     st.markdown("### 📊 Distribution of Delivery Delays (Clients)")
    #     bins = np.arange(df["Delay"].min(), df["Delay"].max() + 1) - 0.5
    #     colors = ['blue' if x < -0.5 else 'red' if x > -0.5 else 'gray' for x in bins[:-1]]

    #     fig, ax = plt.subplots(figsize=(8, 5))
    #     n, bins, patches = plt.hist(df["Delay"], bins=bins, alpha=0.5, edgecolor="black")

    #     for patch, color in zip(patches, colors):
    #         patch.set_facecolor(color)

    #     plt.axvline(0, color='black', linestyle='dashed', linewidth=1.5)
    #     plt.xlabel("Delivery Delay (days)")
    #     plt.ylabel("Number of Deliveries")
    #     plt.title("Distribution of Delivery Delays (Clients)")
    #     st.pyplot(fig)

    # with col4:
    #     st.markdown("### 📊 Distribution of Average Delivery Delays by Country")
    #     fig, ax = plt.subplots(figsize=(8, 5))
    #     n, bins, patches = plt.hist(df_country_avg["Delay"], bins=bins, alpha=0.5, edgecolor="black")

    #     for patch, color in zip(patches, colors):
    #         patch.set_facecolor(color)

    #     plt.axvline(0, color='black', linestyle='dashed', linewidth=1.5)
    #     plt.xlabel("Average Delivery Delay (days)")
    #     plt.ylabel("Number of Countries")
    #     plt.title("Distribution of Average Delivery Delays by Country")
    #     st.pyplot(fig)

    # st.markdown("---")

    # st.title("📊 Dashboard - Delivery Delays")

    ## 📊 **2️⃣ Stacked Bar Chart - Delay Count by Shipping Mode | Line Chart - Delay Trend Over Time**
    col5, col6 = st.columns(2)

    with col5:
        st.markdown("### 📊 Delay Count by Shipping Mode")

        df_delay_ratio = df.groupby(["Shipping Mode", "Delay Category"]).size().unstack(fill_value=0)

        fig, ax = plt.subplots(figsize=(8, 5))
        df_delay_ratio.plot(kind="bar", stacked=True, color=["blue", "green", "red"], edgecolor="black", ax=ax, alpha=0.5)

        plt.xlabel("Shipping Mode")
        plt.ylabel("Number of Deliveries")
        plt.title("Delay Count by Shipping Mode")
        plt.legend(title="Delay Category")
        plt.xticks(rotation=0)  # Set x-axis labels horizontally
        st.pyplot(fig)

    with col6:
        st.markdown("### 📈 Delay Trend Over Time")

        df["Shipping Month"] = df["Shipping date (DateOrders)"].dt.to_period("M")
        df_delay_trend = df.groupby(["Shipping Month", "Delay Category"]).size().unstack(fill_value=0)

        fig, ax = plt.subplots(figsize=(8, 5))
        df_delay_trend.plot(kind="line", marker="o", ax=ax, color=["blue", "green", "red"], alpha=0.5)

        plt.xlabel("Shipping Month")
        plt.ylabel("Number of Deliveries")
        plt.title("Delay Trend Over Time")
        plt.legend(title="Delay Category")
        plt.xticks(rotation=45)  # Rotate x-axis labels for better readability
        st.pyplot(fig)

    st.markdown("---")

    ## 📝 **3️⃣ Client Analysis | Country Analysis**
    col7, col8 = st.columns(2)

    with col7:
        st.markdown("### 📝 Analysis of Inbound Logistics")
        st.markdown("""
        - 📍 **Major cities** like **Los Angeles, New York, Washington, and Chicago** have **more delays**.
        - 🌍 **Suburban areas** tend to have **faster deliveries**.
        - 🚛 **Possible explanation:**
            - 📦 Congested logistics centers in urban zones.
            - 🚦 Traffic congestion.
            - 📍 Better logistics flow in suburban areas, leading to faster deliveries.
        """)

    with col8:
        st.markdown("### 📝 Analysis of Outbound Logistics")
        st.markdown("""
        - 📍 **General trends:** Most countries are **light green**, indicating slight average delays.
        - 🔵 **Advance deliveries (blue):** Some countries like **French Guiana and parts of Africa** receive shipments early.
        - 🔴 **Significant delays (deep red):** Found in **Central Asia and South America**.
        """)

    st.markdown("---")
else:
    st.warning("⚠️ Please upload a CSV file to view the visualizations.")
