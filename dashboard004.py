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
                yaxis=dict(tickformat=".2f", title="Average Delay (days)", range=[0.45, df_grouped["avg_delay"].max() + 0.05]),
                xaxis=dict(title="Customer Segment"),
                legend_title="Type",
            )

            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # 📊 **KPI - Correlation Between Shipping Delays and Profitability**
        st.markdown("### 📈 KPI - Correlation Analysis Between Shipping Delays and Profitability")

        # ✅ List of required columns
        required_columns = [
            "Days for shipping (real)", "Days for shipment (scheduled)", 
            "Benefit per order", "Sales per customer", "Order Item Profit Ratio", 
            "Sales", "Order Item Total", "Order Profit Per Order"
        ]

        # ✅ Keep only available columns
        available_columns = [col for col in required_columns if col in df.columns]

        # ✅ Ensure necessary columns exist
        if len(available_columns) == len(required_columns):  

            # 📌 **Calculate Delay Measures**
            df["Shipping Delay"] = df["Days for shipping (real)"] - df["Days for shipment (scheduled)"]

            # 🔍 **Check for NaN values & Convert to numeric**
            df = df[required_columns + ["Shipping Delay"]].copy()  # Keep only relevant columns
            df = df.apply(pd.to_numeric, errors="coerce")  # Convert everything to numbers
            df = df.dropna()  # Remove rows with NaN

            # 📌 **List of financial indicators**
            financial_metrics = [
                "Benefit per order", "Sales per customer", "Order Item Profit Ratio",
                "Sales", "Order Item Total", "Order Profit Per Order"
            ]

            # 📌 **Compute Correlations**
            correlation_results = {}
            for metric in financial_metrics:
                correlation_results[metric] = {
                    "Corr. with Shipping Delay": df["Shipping Delay"].corr(df[metric]),
                    "Corr. with Days for shipping (real)": df["Days for shipping (real)"].corr(df[metric])
                }

            # 📌 **Create Correlation Table**
            correlation_df = pd.DataFrame(correlation_results).T
            correlation_df.columns = ["Corr. with Shipping Delay", "Corr. with Days for shipping (real)"]

            # 📌 **Interpret the results**
            def interpret_correlation(value):
                value=value*100
                if value > 0.3:
                    return "🔼 Positive Correlation (delays increase this metric)"
                elif value < -0.3:
                    return "🔽 Negative Correlation (delays reduce this metric)"
                else:
                    return "➖ No Significant Correlation"

            correlation_df["Interpretation (Shipping Delay)"] = correlation_df["Corr. with Shipping Delay"].apply(interpret_correlation)
            correlation_df["Interpretation (Days for shipping)"] = correlation_df["Corr. with Days for shipping (real)"].apply(interpret_correlation)

            # # 📌 **Show correlation table in Streamlit**
            # st.markdown("### 📊 Correlation Results")
            # st.dataframe(correlation_df)

            # 📌 **Summary KPI Interpretation in Two Columns**
            # st.markdown("### 📌 KPI - Correlation Analysis")

            # 🟢 **Split Financial Metrics into Two Columns**
            col1, col2 = st.columns(2)
            metrics_split = len(financial_metrics) // 2

            with col1:
                st.markdown("#### 📊 Correlation with **Shipping Delay**")
                for metric in financial_metrics:
                    shipping_corr = correlation_results[metric]["Corr. with Shipping Delay"]
                    st.markdown(f"**📌 {metric}:** `{shipping_corr*100:.2f}%` → {interpret_correlation(shipping_corr)}")

            with col2:
                st.markdown("#### 📊 Correlation with **Absolute Shipping Time**")
                for metric in financial_metrics:
                    real_days_corr = correlation_results[metric]["Corr. with Days for shipping (real)"]
                    st.markdown(f"**📌 {metric}:** `{real_days_corr*100:.2f}%` → {interpret_correlation(real_days_corr)}")

        else:
            missing_columns = [col for col in required_columns if col not in df.columns]
            st.warning(f"⚠️ Required columns missing: {', '.join(missing_columns)}. Please check your dataset.")

    else:
        st.warning("⚠️ Please upload a CSV file to view the visualizations.")
