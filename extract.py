import os
import pandas as pd

base_dir = os.path.dirname(__file__)
source = os.path.join(base_dir,"Data")

def extract_data():


    orders_df = pd.read_csv(os.path.join(source,"orders.csv"))



    products_df = pd.read_csv(os.path.join(source,"products.csv"),sep="|")



    exchange_rates_df = pd.read_json(os.path.join(source,"exchange_rates.json"))



    returns_df = pd.read_csv(os.path.join(source,"returns.tsv"),sep="\t")



    customers_df = pd.read_json(os.path.join(source,"customers.json"))

    customers_df[["city","country"]] = pd.DataFrame(customers_df["address"].to_list())

    customers_df= customers_df.drop(columns=["address"])

    # Reordering the column names
    customers_df = customers_df[
    [
        "customer_id",
        "name",
        "email",
        "signup_date",
        "city",
        "country",
        "is_premium"
    ]
]


    web_df = pd.read_csv(os.path.join(source,"web_events.log"),
                         sep="|",
                         header=None)
    web_df.columns=[
            "timestamp",
            "session",
            "customer_id",
            "event",
            "product_id"
        ]

    def clean_rows(value):
        return value.strip().split("=")[1]

    columns =["session","customer_id","event","product_id"]

    for col in columns:
        web_df[col] = web_df[col].apply(clean_rows)


    return {
        "orders" : orders_df,
        "products":products_df,
        "customers":customers_df,
        "exchange_rates":exchange_rates_df,
        "returns" : returns_df,
        "web_events" : web_df
    }

if __name__=="__main__":
    data = extract_data()

    for name, df in data.items():
        print(f"{name}")
        print(f"Rows    : {df.shape[0]}")
        print(f"Columns : {df.shape[1]}")
        print(df.head())
        print("-" * 50)