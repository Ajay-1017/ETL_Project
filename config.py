
import os

upper_columns = {
            "order_id",
            "customer_id",
            "product_id",
            "currency",
            "return_id"
            }

title_columns = {
            "product_name",
            "category",
            "name",
            "city"
            }     

lower_columns ={
            "email",
            "event",
            "country"
            }

capitalize_columns = {
            "reason"
            }

validate_null_columns = {
    "orders": [
        "order_id",
        "product_id",
        "order_date"
    ],

    "products": [
        "product_id"
    ],

    "customers": [
        "customer_id"
    ],

    "returns": [
        "order_id"
    ],


}

validate_customer_id = {
    "orders" : "customer_id",
    "web_events" : "customer_id",
}

country_map ={
        "uk" : "UK",
        "united kingdom" : "UK",
        "united states" : "USA",
        "usa" : "USA" ,
        "u.s.a" : "USA" ,
        "de" : "Germany" ,
        "germany" : "Germany",
        "india" : "India",
        "in" : "India",  
        }

validate_product_id = {
    "orders" : "product_id",
    "web_events" : "product_id"
}

discount = 10

facts_sales = [ "order_id",
            "customer_id",
            "product_id",
            "quantity",	
            "amount",	
            "currency",	
            "amount_usd",	
            "order_date",	
            "price_tier",	
            "net_revenue",	
            "is_returned" 
            ]


dim_customers=[
    "customer_id",	
    "name",	
    "email_present",	
    "city",	
    "country",	
    "is_premium",	
    "signup_date"
]

dim_products=[
"product_id",	
"product_name",	
"category",	
"unit_price",	
"currency",	
"unit_price_usd",	
"price_tier"
]

feature_customers_df=[
    "customer_id",
    "total_orders",
    "total_spend_usd",
    "avg_order_value",
    "return_rate",
    "days_since_last_order",
    "sessions_count",
]


BASE_DIR = os.path.dirname(__file__)

DATABASE_PATH = os.path.join(BASE_DIR,"Database","etl_cart.db")

LOG_PATH =  os.path.join(BASE_DIR,"log","reject_logs.log")