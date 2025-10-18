
"""
SQL Beginner to Advanced — Python Script for Executing All Queries
Dataset: bike_store.db
Author: Pranshul Bhatnagar
Description:
    This script connects to the bike_store.db SQLite database
    and runs a collection of beginner-to-advanced SQL queries
    including subqueries, CTEs, window functions, and analytics.
"""


import pandas as pd
import sqlite3
import os


def create_database():
    db_path = os.path.join(os.path.dirname(__file__), '..', 'Data', 'bike_store.db')
    connection = sqlite3.connect(db_path)

    brands = pd.read_csv('Data/CSV_files/brands.csv')
    categories = pd.read_csv('Data/CSV_files/categories.csv')
    customers = pd.read_csv('Data/CSV_files/customers.csv')
    order_items = pd.read_csv('Data/CSV_files/order_items.csv')
    orders = pd.read_csv('Data/CSV_files/orders.csv')
    products = pd.read_csv('Data/CSV_files/products.csv')
    staffs = pd.read_csv('Data/CSV_files/staffs.csv')
    stocks = pd.read_csv('Data/CSV_files/stocks.csv')
    stores = pd.read_csv('Data/CSV_files/stores.csv')

    brands.to_sql('brands', connection, if_exists='replace', index=False)
    categories.to_sql('categories', connection, if_exists='replace', index=False)
    customers.to_sql('customers', connection, if_exists='replace', index=False)
    order_items.to_sql('order_items', connection, if_exists='replace', index=False)
    orders.to_sql('orders', connection, if_exists='replace', index=False)
    products.to_sql('products', connection, if_exists='replace', index=False)
    staffs.to_sql('staffs', connection, if_exists='replace', index=False)
    stocks.to_sql('stocks', connection, if_exists='replace', index=False)
    stores.to_sql('stores', connection, if_exists='replace', index=False)
    connection.close()

    return db_path


def run_query(query, description):
    """Executes a SQL query and prints the first few rows as a DataFrame."""
    print("\n" + "="*80)
    print(f"🔹 {description}")
    print("="*80)
    try:
        df = pd.read_sql_query(query, connection)
        print(df.head(10))  # Display first 10 rows for brevity
    except Exception as e:
        print(f"⚠️ Error running query: {e}")

def main(): 
    #CREATE DATABASE AND ESTABLISH CONNECTION
    db_path = create_database()
    global connection
    connection = sqlite3.connect(db_path)
    print("✅ Database connected successfully!")


    # --- Basic SELECT and Filtering ---
    run_query("""
    SELECT * FROM customers LIMIT 5;
    """, "Preview of the 'customers' table")

    run_query("""
    SELECT first_name, last_name, email FROM customers WHERE city = 'New York';
    """, "List of customers from New York")

    # --- Aggregations ---
    run_query("""
    SELECT city, COUNT(customer_id) AS total_customers
    FROM customers
    GROUP BY city
    ORDER BY total_customers DESC;
    """, "Customer count by city")

    # --- Joins ---
    run_query("""
    SELECT 
        customers.first_name || ' ' || customers.last_name AS customer_name,
        orders.order_id,
        orders.order_date
    FROM customers
    INNER JOIN orders ON customers.customer_id = orders.customer_id
    LIMIT 10;
    """, "Customers and their orders")

    # --- Subqueries ---
    run_query("""
    SELECT 
        *
    FROM 
        products
    WHERE
        model_year = 2019
    AND
        list_price > (
                    SELECT
                        AVG(list_price)
                    FROM
                        products
                    WHERE
                        model_year = 2019
                    );
    """, "Products from 2019 with price above 2019 average")

    run_query("""
    SELECT 
        DISTINCT
        order_id,
        customer_id
    FROM 
        orders
    WHERE
        order_id IN (
                    SELECT
                        DISTINCT
                        order_id
                    FROM
                        order_items
                    INNER JOIN
                        products
                    ON
                        order_items.product_id = products.product_id
                    AND
                        brand_id = 9
                    AND
                        discount >= .20
                    );
    """, "Orders with brand_id=9 products discounted >= 20%")

    run_query("""
    SELECT 
        DISTINCT
        order_id,
        customer_id
    FROM 
        orders
    WHERE
        EXISTS (
                SELECT
                    1
                FROM
                    order_items
                WHERE
                    discount >= .20
                AND
                    order_items.order_id = orders.order_id
                );
    """, "Orders that have any item with discount >= 20%")

    # --- Common Table Expressions (CTEs) ---
    run_query("""
    WITH category_sales AS (
        SELECT
            DISTINCT
            order_id,
            order_items.product_id,
            quantity,
            order_items.list_price,
            quantity * order_items.list_price AS line_subtotal,
            category_id
        FROM
            order_items
        INNER JOIN
            products
        ON
            order_items.product_id = products.product_id
    )

    SELECT
        category_id,
        SUM(line_subtotal) AS revenue,
        SUM(quantity) AS units_sold,
        COUNT(DISTINCT order_id) AS total_orders
    FROM 
        category_sales
    GROUP BY
        1
    ORDER BY
        2 DESC;
    """, "CTE: Revenue, units sold, and total orders per category")

    # --- Recursive CTE ---
    run_query("""
    WITH RECURSIVE employee_hierarchy AS (
        SELECT
            staff_id,
            manager_id,
            first_name || ' ' || last_name AS full_name
        FROM
            staffs t1
        WHERE
            manager_id IS NULL
        UNION ALL
        SELECT
            t2.staff_id,
            t2.manager_id,
            t2.first_name || ' ' || t2.last_name AS full_name
        FROM
            staffs t2
        INNER JOIN
            employee_hierarchy eh
        ON
            t2.manager_id = eh.staff_id  
    )

    SELECT
        *
    FROM
        employee_hierarchy;
    """, "Recursive CTE: Employee hierarchy")

    # --- Window Functions ---
    run_query("""
    WITH daily_orders AS (
        SELECT
            order_date,
            store_id,
            COUNT(*) AS orders
        FROM
            orders
        GROUP BY
            1,2
    )

    SELECT
        order_date,
        store_id,
        AVG(orders) OVER(PARTITION BY store_id 
                        ORDER BY order_date ASC
                        ROWS BETWEEN 14 PRECEDING AND 15 FOLLOWING) AS moving_avg_30d
    FROM
        daily_orders;
    """, "30-day moving average of orders by store")

    # --- Customer Segmentation ---
    run_query("""
    WITH customer_stats AS (
        SELECT
            customer_id,
            SUM(quantity * list_price * (1 - discount)) AS total_spent,
            COUNT(DISTINCT orders.order_id) AS total_orders,
            julianday('2018-12-29') - julianday(MAX(order_date)) AS days_since_last_purchase
        FROM
            orders
        INNER JOIN
            order_items
        ON
            orders.order_id = order_items.order_id
        GROUP BY
            1
    )

    SELECT
        customer_id,
        CASE WHEN total_orders > 1 THEN 'repeat buyer'
            ELSE 'one-time buyer'
            END AS purchase_frequency,
        CASE WHEN days_since_last_purchase < 90 THEN 'recent buyer'
            ELSE 'not recent buyer'
            END AS purchase_recency,
        CASE WHEN total_spent/(SELECT MAX(total_spent) FROM customer_stats) >= .65 THEN 'big spender'
            WHEN total_spent/(SELECT MAX(total_spent) FROM customer_stats) <= .30 THEN 'low spender'
            ELSE 'average spender' 
            END AS buying_power
    FROM
        customer_stats;
    """, "Customer segmentation based on spending, frequency, and recency")

    # --- Seasonality Analysis ---
    run_query("""
    WITH product_categories AS (
        SELECT
            product_id,
            category_name
        FROM
            products
        INNER JOIN
            categories
        ON
            products.category_id = categories.category_id
    ),

    product_sales_ym AS (
        SELECT
            strftime('%Y', order_date) AS year,
            strftime('%m', order_date) AS month,
            product_id,
            SUM(quantity) AS units_sold
        FROM
            orders
        INNER JOIN
            order_items
        ON
            orders.order_id = order_items.order_id
        GROUP BY
            1,2,3
    )

    SELECT
        month,
        category_name,
        AVG(units_sold) AS avg_units_sold
    FROM
        product_sales_ym
    INNER JOIN
        product_categories
    ON
        product_sales_ym.product_id = product_categories.product_id
    GROUP BY
        1,2;
    """, "Seasonality: Average monthly sales per category")

    # --- Customer Ranking ---
    run_query("""
    SELECT
        c.first_name || ' ' || c.last_name AS customer_name,
        COUNT(s.order_id) AS total_transactions,
        RANK() OVER (ORDER BY COUNT(s.order_id) DESC) AS rank
    FROM
        orders s
    INNER JOIN
        customers c 
    ON 
        s.customer_id = c.customer_id
    GROUP BY
        1
    ORDER BY
        2 DESC;
    """, "Ranking customers by total transactions")

    # --- Market Basket Analysis ---
    run_query("""
    SELECT
        product_a,
        product_b,
        co_purchase_count
    FROM 
        (
        SELECT
            p1.product_name AS product_a,
            p2.product_name AS product_b,
            COUNT(*) AS co_purchase_count
        FROM
            order_items s1
        INNER JOIN
            order_items s2 ON s1.order_id = s2.order_id AND s1.product_id <> s2.product_id
        INNER JOIN
            products p1 ON s1.product_id = p1.product_id
        INNER JOIN
            products p2 ON s2.product_id = p2.product_id
        GROUP BY
            p1.product_id, p2.product_id
        ) subquery
    ORDER BY
        co_purchase_count DESC;
    """, "Frequently co-purchased product pairs")

    # --- Purchase Interval Analysis ---
    run_query("""
    SELECT
        customer_id,
        AVG(julianday(order_date) - julianday(prev_order_date)) AS avg_days_between_purchases
    FROM 
        (
        SELECT
            c.customer_id,
            order_date,
            LAG(order_date) OVER (PARTITION BY c.customer_id ORDER BY order_date) AS prev_order_date
        FROM
            orders o
        INNER JOIN
            customers c ON o.customer_id = c.customer_id
        ) subquery
    WHERE 
        prev_order_date IS NOT NULL
    GROUP BY
        1;
    """, "Average days between consecutive purchases per customer")


    connection.close()
    print("\n✅ All queries executed successfully!")

if __name__ == "__main__":
    main()