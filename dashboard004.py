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

        # 📌 **Convert "Shipping date (DateOrders)" to datetime**
        df["Shipping date (DateOrders)"] = pd.to_datetime(df["shipping date (DateOrders)"], errors='coerce')

        # 📌 **Add year filter**
        st.sidebar.markdown("### 📆 Filter by Year")
        available_years = df["Shipping date (DateOrders)"].dt.year.dropna().unique()
        selected_years = st.sidebar.multiselect("Select Year", available_years, default=available_years)
        if selected_years:
            df = df[df["Shipping date (DateOrders)"].dt.year.isin(selected_years)]

        # 📌 **Adding dynamic filters**
        st.sidebar.markdown("### 🎯 Available Filters")


        # 🔹 **Drilldown to Department**
        column_names = list(df.columns)
        filters = ["Type","Category Name","Department Name","Market","Order Region","Product Name","Shipping Mode",]
        for col in filters:
            departments = df[col].unique()
            if len(departments)<15:
                selected_departments = st.sidebar.multiselect(col, departments, default=departments)

                if selected_departments:
                    df = df[df[col].isin(selected_departments)]

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
            fig.update_traces(marker=dict(opacity=.75, line=dict(width=1, color="black")))  # Add transparency + outline

            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # 📊 **Analysis Section**
        st.markdown("### 🔍 Insights & Analysis")

        # Create two columns for better readability
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 📌 Consumer Segment")
            st.write("""
            - **Moderate delay ratio (~0.57)**
            - **Higher profit margin (~11%)**
            - Largest sales contribution (biggest bubble)
            - Less affected by delays compared to other segments
            - **Consumers** seem more resilient to shipping delays.
            """)


        with col2:
            st.markdown("#### 📌 Home Office Segment")
            st.write("""
            - **Highest delay ratio (~0.585)**
            - **Lower profit margin (~10.5%)**
            - Indicates a possible negative correlation between delays and profitability
            - May require targeted shipping improvements
            - **Home Office customers** face a sharper decline in profitability with increasing delays.
            """)

        st.markdown("---")        

        # 📊 **Grouped Bar Chart - Profitability & Delays by Payment Type & Customer Segment**
        st.markdown("### 💳 Profitability & Delays by Customer Segment & Payment Type")

        # ✅ Ensure the column exists
        if "Type" in df.columns:
            df_grouped = df.groupby(["Customer Segment", "Type"]).agg(
                avg_delay=("Delay Ratio", "mean")
            ).reset_index()

            # 📊 **Create a grouped bar chart**
            fig = px.bar(
                df_grouped,
                x="Customer Segment",
                y="avg_delay",
                color="Type",
                barmode="group",  # Group bars next to each other
                labels={"avg_delay": "Average Delay (days)", "Customer Segment": "Customer Segment"},
                # title="📊 Average Delay by Customer Segment & Payment Type",
            )


            # ✅ **Add black border around bars**
            fig.update_traces(marker=dict(
                line=dict(color="black", width=1.5)  # Black border with width 1.5
            ))
    
            # ✅ **Improve design**
            fig.update_layout(
                # yaxis=dict(tickformat=".2f", title="Average Delay (days)"),
                yaxis=dict(tickformat=".2f", title="Average Delay (days)", range=[df_grouped["avg_delay"].min() - 0.05, df_grouped["avg_delay"].max() + 0.05]),
                xaxis=dict(title="Customer Segment"),
                legend_title="Type",
            )

            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")


        # 📌 Define Groups
        g1 = {"Days for shipping (real)", "Delay Ratio"}
        g2 = {"Benefit per order", "Sales per customer", "Order Item Profit Ratio", 
              "Sales", "Order Item Total", "Order Profit Per Order"}

        # ✅ Ensure the required columns exist in the dataset
        available_g1 = [col for col in g1 if col in df.columns]
        available_g2 = [col for col in g2 if col in df.columns]

        if available_g1 and available_g2:
            # 📌 Compute all correlations between g1 and g2
            correlation_results = {}
            for col1 in available_g1:
                for col2 in available_g2:
                    correlation_value = df[col1].corr(df[col2])*100
                    correlation_results[(col1, col2)] = abs(correlation_value)  # Store absolute value for comparison

            # 📌 Find the strongest correlation (highest absolute value)
            strongest_pair = max(correlation_results, key=correlation_results.get)
            strongest_value = df[strongest_pair[0]].corr(df[strongest_pair[1]])*100

            # 📌 Compute average financial metric for min/max shipping delay
            min_delay_value = df[strongest_pair[0]].min()
            max_delay_value = df[strongest_pair[0]].max()

            avg_financial_min_delay = df[df[strongest_pair[0]] == min_delay_value][strongest_pair[1]].mean()
            avg_financial_max_delay = df[df[strongest_pair[0]] == max_delay_value][strongest_pair[1]].mean()

            # 📌 Interpretation function
            def interpret_correlation(value):
                if value > 0.3:
                    return "🔼 Positive Correlation (delays increase this metric)"
                elif value < -0.3:
                    return "🔽 Negative Correlation (delays reduce this metric)"
                else:
                    return "➖ No Significant Correlation"

            # 📌 Display KPI in Streamlit
            st.markdown("### 📊 KPI - Strongest Financial Impact of Shipping Delays")
            
            # Display KPI as a fraction
            col_kpi1, col_kpi2 = st.columns(2)

            with col_kpi1:
                st.metric(label=f"**📈 Correlation Value:** `{strongest_value:.2f}`", 
                          value=f"{avg_financial_min_delay:.2f} / {avg_financial_max_delay:.2f}" if strongest_value is not None else "N/A", 
                          delta=f"{(avg_financial_max_delay-avg_financial_min_delay)/avg_financial_min_delay*100:.2f}%" if strongest_value is not None else "N/A")

            with col_kpi2:
                st.markdown(f"""
                **📝 Interpretation:**  
                - **📈 Most Impacted Relationship:** `{strongest_pair[0]}` & `{strongest_pair[1]}`
                - 🔍 Average `{strongest_pair[1]}` when `{strongest_pair[0]}` is at its **lowest** (`{min_delay_value}` days): `{avg_financial_min_delay:.2f}`
                - 🔍 Average `{strongest_pair[1]}` when `{strongest_pair[0]}` is at its **highest** (`{max_delay_value}` days): `{avg_financial_max_delay:.2f}`
                """)

        else:
            st.warning("⚠️ Required columns are missing from the dataset. Please check your data.")


        st.markdown("---")

    else:
        st.warning("⚠️ Please upload a CSV file to view the visualizations.")
