import sqlite3
import pandas as pd
import streamlit as st
import config

# Database Connection

conn = sqlite3.connect(config.DATABASE_PATH)

# Dashboard Queries


total_revenue = pd.read_sql(("""
        SELECT ROUND(SUM(net_revenue),2) AS total_revenue
        FROM fact_sales;
    """), conn)

return_rate = pd.read_sql("""
        SELECT ROUND(
                   SUM(CASE WHEN is_returned = 1 THEN 1 ELSE 0 END ) * 100.0 / COUNT(*),2
                   ) AS return_rate
        FROM fact_sales;
    """, conn)

revenue_country = pd.read_sql("""
            SELECT
            c.country,
            SUM(f.net_revenue) AS revenue
            FROM fact_sales f
            JOIN dim_customers c
            ON f.customer_id=c.customer_id
            GROUP BY c.country
            ORDER BY revenue;
            """, conn)

revenue_tier = pd.read_sql("""
        SELECT price_tier, ROUND(SUM(net_revenue),2) AS revenue
        FROM fact_sales
        GROUP BY price_tier
        ORDER BY revenue ;
    """, conn)

revenue_time = pd.read_sql("""
        SELECT DATE(order_date) as order_date, ROUND(SUM(net_revenue),2) AS revenue
        FROM fact_sales
        GROUP BY order_date
        ORDER BY order_date;
    """, conn)

conn.close()

# Dashboard

st.set_page_config(
    page_title="E-Commerce Dashboard",
    layout="wide"
)

st.title("E-Commerce Sales Dashboard")

# KPI Cards

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "Total Revenue",
        f"${total_revenue.iloc[0]['total_revenue']:,.2f}"
    )

with col2:
    st.metric(
        "Return Rate",
        f"{return_rate.iloc[0]['return_rate']} %"
    )

st.divider()

# Revenue Over Time

st.subheader("Revenue Over Time")

st.line_chart(
    revenue_time.set_index("order_date")
)

col3, col4 = st.columns(2)

with col3:

    st.subheader("Revenue by Country")

    st.bar_chart(
        revenue_country.set_index("country")
    )

with col4:

    st.subheader("Revenue by Price Tier")

    st.bar_chart(
        revenue_tier.set_index("price_tier")
    )