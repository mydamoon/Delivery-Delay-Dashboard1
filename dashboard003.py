import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

def show_dashboard():
    # 📊 Dashboard Configuration
    # st.set_page_config(page_title="Dashboard Screen 2: Product Categories & Delays", layout="wide")

    # 📂 Uploading CSV file
    st.sidebar.title("📂 Upload Data")
    uploaded_file = st.sidebar.file_uploader("Upload a CSV file", type="csv")

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file, encoding='latin-1')

        # 📌 Convert "Shipping date (DateOrders)" to datetime
        df["Shipping date (DateOrders)"] = pd.to_datetime(df["shipping date (DateOrders)"], errors='coerce')

        # 📌 Filters
        st.sidebar.markdown("### 📆 Filters")

        # 🔹 Filter by Year
        available_years = df["Shipping date (DateOrders)"].dt.year.dropna().unique()
        selected_years = st.sidebar.multiselect("Select Year", available_years, default=available_years)

        if selected_years:
            df = df[df["Shipping date (DateOrders)"].dt.year.isin(selected_years)]

        # 🔹 Drilldown to Department
        st.sidebar.markdown("### 🔍 Drilldown to Product Type")
        departments = df["Department Name"].unique()
        selected_departments = st.sidebar.multiselect("Select Department", departments, default=departments)

        if selected_departments:
            df = df[df["Department Name"].isin(selected_departments)]

        # ⏳ Calculating delivery delay
        df["Delay"] = df["Days for shipping (real)"] - df["Days for shipment (scheduled)"]

        # 📌 Aggregate total delay per Department and Category
        df_agg = df.groupby(["Department Name", "Category Name"]).agg(
            total_delay=("Delay", "sum"),  # Total delay for each category
            avg_delay=("Delay", "mean")  # Average delay for color scale
        ).reset_index()
        print(df_agg)

        # 📌 Normalize Delay Values for Color Scale
        min_delay = df_agg["avg_delay"].min()
        max_delay = df_agg["avg_delay"].max()

        if max_delay != min_delay:
            df_agg["Normalized Delay"] = (df_agg["avg_delay"] - min_delay) / (max_delay - min_delay)
        else:
            df_agg["Normalized Delay"] = 0.5  # Default mid-value if no variation

        st.markdown("---")
        st.title("📊 Relationship Between Product Categories and Delays")
        st.markdown("---")

        # 🟢 Treemap with Delay as Size
        st.markdown("### 🌳 Delay Ratio by Category & Product")

        fig = px.treemap(
            df_agg,
            path=["Department Name", "Category Name"],  # Hierarchy: Department -> Category
            values="total_delay",  # 🔹 Size based on total delay
            color="avg_delay",  # 🔹 Color based on average delay
            color_continuous_scale=[
                "rgb(0, 0, 255)",   # Blue for low delay
                "rgb(255, 255, 255)",  # White for medium delay
                "rgb(255, 0, 0)"    # Red for high delay
            ],
            labels={"avg_delay": "Average Delay (days)", "total_delay": "Total Delay (days)"},
        )

        # # 🟢 Améliorations pour un affichage propre
        # fig.update_traces(
        #     hovertemplate="<b>Delay:</b> %{color:.2f} days<extra></extra>",  # ✅ Affiche uniquement le retard
        #     textinfo="label+percent parent",  # ✅ Affiche Catégorie + % (évite surcharge)
        #     textfont=dict(size=14),  # ✅ Texte plus grand et lisible
        # )

        # # 🟢 Ajustements pour forcer un fond blanc
        # fig.update_layout(
        #     margin=dict(l=10, r=10, t=40, b=10),  # ✅ Réduit l'espace perdu
        #     template="plotly_white",  # ✅ Force un thème blanc
        # )

        # 🟢 Afficher le graphique dans Streamlit
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("---")

        st.markdown("### 🏆 Top 5 Products with Highest Delays")
        col5, col6 = st.columns(2)
        with col5:

            top_5_delayed_products = df.groupby("Product Name")["Delay"].mean().nlargest(5).reset_index()

            # Création du Pie Chart avec contours noirs et police agrandie
            fig = go.Figure(data=[go.Pie(
                labels=top_5_delayed_products["Product Name"],
                values=top_5_delayed_products["Delay"],
                marker=dict(line=dict(color="black", width=1)),  # Contours noirs
                textinfo="percent",
                textfont=dict(size=12),  # Agrandissement des labels
                pull=[0.02, 0.02, 0.02, 0.02, 0.02]  # Met en avant le premier élément légèrement
            )])

            fig.update_layout(
                showlegend=True,
                legend_title="<b>Product Name</b>",
                legend=dict(font=dict(size=16)),  # Agrandir la police de la légende
            )

            # Affichage du graphique dans Streamlit
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        with col6:
            # 🏆 Top 5 Products with Highest Delays
            # st.markdown("### 🏆 Top 5 Products with Highest Delays")
            st.markdown("""
            - The pie chart highlights **the top 5 most delayed products**, contributing significantly to total shipment delays.
            - **Key Observations**:
                - 🚨 High-impact products like SOLE E25 Elliptical & Nike Men's Fingertrap Max Training Shoe contribute to over 21% of total delays.
                - 📌 Garmin Approach S4 GPS Watch & Titleist Club Glove Travel Cover are also affected, possibly due to supplier issues or inventory shortages.
                - 🚚 Yakima DoubleDown Hitch Mount Bike Rack suggests delays related to bulky or specialized shipping requirements.
            """)

        col7, col8 = st.columns(2)
        with col7:
            # 🌳 Treemap Analysis (Department → Category)
            st.markdown("### 🌳 Delay Ratio by Department & Category")

            st.markdown("""
            - **🔍 Interpretation of the Treemap:**  
              - **Size of rectangles** = Total accumulated delay (sum of delay days).  
              - **Color intensity** = Average delay per category (🔵 blue = low delay, 🔴 red = high delay).  

            - **🚨 Departments with the Highest Total Delays:**  
              - **📌 Fan Shop** is also highly affected, especially **Indoor/Outdoor Games (10,898 days)** and **Water Sports (8,816 days)**.  
              - **📌 Apparel** has the longest total delay, with **Cleats (14,165 days)** and **Men’s Footwear (12,551 days)** being the most impacted.  

            - **📌 Categories:**  
              - **🚨 Most Delayed:**  
                - Golf Bags & Carts (0.77 avg delay)  
                - Soccer (0.71 avg delay)  
                - Pet Supplies (0.71 avg delay)  
              - **🔵 Shortest Delays:**  
                - Technology - Computers (0.45 avg delay)  
                - Outdoors - Men’s Golf Clubs (0.32 avg delay)  
            """)
        with col8:
            # 📌 Recommendations for Improvement
            st.markdown("### 📌 Recommendations for Improvement")
            st.markdown("""
            1. **Target High-Impact Departments** 🚨  
               - Apparel, Fan Shop, and Golf have the most accumulated delays.  
               - 🔹 Action Plan: Work with suppliers and logistics teams to prioritize high-delay categories.

            2. **Identify Best Practices from Low-Delay Categories** ✅ 
               - Computers and Men's Golf Clubs have lower average delays.  
               - 🔹 Next Steps: Study their logistics efficiency and apply similar practices across other departments.

            3. **Improve Shipping for Long-Delay Products** 📌 
               - The top 5 delayed products suggest potential inventory shortages or supplier delays.  
               - 🔹 Solution: Improve demand forecasting, buffer stock management, and alternative supplier sourcing.
            """)

    else:
        st.warning("⚠️ Please upload a CSV file to view the visualizations.")
