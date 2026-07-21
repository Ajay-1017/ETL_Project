import sqlite3
import config
import datetime as dt

def load_data(final_tables):
    conn = sqlite3.connect(config.DATABASE_PATH)

    # Load all tables
    for table_name, df in final_tables.items():

        df.to_sql(
            name=table_name,
            con=conn,
            if_exists="replace",
            index=False
        )

    cursor = conn.cursor()

    print("=" * 70)
    print("Tables Created")
    print("=" * 70)

    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table';
    """)

    tables = cursor.fetchall()

    for table in tables:
        print(table[0])

    print("\n" + "=" * 70)
    print("Dashboard Queries")
    print("=" * 70)


    # KPI : Total Revenue

    cursor.execute("""
        SELECT SUM(net_revenue) AS total_revenue
        FROM fact_sales;
    """)

    print("\nTotal Revenue")
    print(cursor.fetchall())


    # KPI : Return Rate
    cursor.execute("""
        SELECT ROUND(
                   SUM(CASE WHEN is_returned = 1 THEN 1 ELSE 0 END ) * 100.0 / COUNT(*),2
                   ) AS return_rate
        FROM fact_sales;
    """)

    print("\nReturn Rate")
    print(cursor.fetchall())

    # ----------------------------------------------------
    # Revenue by Price Tier
    # ----------------------------------------------------
    cursor.execute("""
        SELECT price_tier, ROUND(SUM(net_revenue),2) AS revenue
        FROM fact_sales
        GROUP BY price_tier
        ORDER BY revenue ;
    """)

    print("\nRevenue By Price Tier")

    for row in cursor.fetchall():
        print(row)

    # ----------------------------------------------------
    # Revenue by Country
    # ----------------------------------------------------
    cursor.execute("""
        SELECT c.country, ROUND(SUM(f.net_revenue),2) AS revenue
        FROM fact_sales f
        JOIN dim_customers c
        ON f.customer_id = c.customer_id
        GROUP BY c.country
        ORDER BY revenue DESC;
    """)

    print("\nRevenue By Country")

    for row in cursor.fetchall():
        print(row)

    # ----------------------------------------------------
    # Revenue Over Time
    # ----------------------------------------------------
        cursor.execute("""
            SELECT DATE(order_date), ROUND(SUM(net_revenue),2) AS revenue
            FROM fact_sales
            GROUP BY order_date
            ORDER BY order_date;
        """)

    print("\nRevenue Over Time")

    for row in cursor.fetchall():
        print(row)

    conn.close()