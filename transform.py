import pandas as pd
import datetime as dt
import extract 
import config

class Transform:

    def __init__(self,data):

        copy_data={}
        for name, df in data.items():
            copy_data[name] = df.copy()

        self.data = data # original data

        self.tables = copy_data # copied version of data

        self.reject_logs = {
                "orders": pd.DataFrame(),
                "customers": pd.DataFrame(),
                "products": pd.DataFrame(),
                "returns": pd.DataFrame(),
                "web_events": pd.DataFrame()
                }

    def add_rejects(self, rejected_rows, table_name, reason):

        if rejected_rows.empty:
            return

        rejected = rejected_rows.copy()

        rejected["table_name"] = table_name
        rejected["row_number"] = rejected.index
        rejected["reject_reason"] = reason

        original_cols = self.data[table_name].columns.tolist()
        extra_cols = ["table_name", "row_number", "reject_reason"]

        rejected = rejected[original_cols + extra_cols]

        self.reject_logs[table_name] = pd.concat(
            [self.reject_logs[table_name], rejected],
            ignore_index=True
        )

    def clean_strip(self,df):
        str_columns = df.select_dtypes(include=object).columns
        for column in str_columns:
            df[column] = df[column].str.strip()


    def standardize_columns(self,df):
        str_columns = df.select_dtypes(include = ["object"]).columns

        for column in str_columns:

            if column in config.upper_columns:
                df[column] = df[column].str.upper()

            elif column in config.title_columns:
                df[column] = df[column].str.title()
            
            elif column in config.lower_columns:
                df[column] = df[column].str.lower()

            elif column in config.capitalize_columns:
                df[column] = df[column].str.capitalize()


    # 2) log and remove Duplicates records of order_id (keep first) 
    def remove_duplicates(self):

        ord_df = self.tables["orders"]

        duplicates = ord_df[ord_df["order_id"].duplicated(keep="first")]
    
        # logging Duplicates in DataFrame
        self.add_rejects(duplicates,"orders","duplicate order_id")

        # Drop duplicates
        self.tables["orders"] = ord_df.drop_duplicates(
            subset="order_id",
            keep="first",
        )


    # 3) validate null records

    def validate_null(self):

        for table_name , validate_columns in config.validate_null_columns.items():

            df = self.tables[table_name]

            null_rows =  df[df[validate_columns].isnull().any(axis=1)]

            # Identify which column is null in the particular row
            for index , row in null_rows.iterrows():
                missing = [] 

                for col in validate_columns:
                    if pd.isna(row[col]):
                        missing.append(col)

                # logging null_rows in DataFrame
                self.add_rejects(null_rows.loc[[index]],table_name,f" Missing values in : {' , '.join(missing)}")

            # Drop null_rows
            self.tables[table_name] = df.drop(index=null_rows.index)
    

    # 4) customer_id must be present and exist in customers

    def validate_customers(self):

        cust_df = self.tables["customers"]

        val_customers = set(cust_df["customer_id"])

        for table_name , customer_id_col in config.validate_customer_id.items():
            
            df = self.tables[table_name]

            invalid_customers =  df[
                ~df[customer_id_col].isin(val_customers)
                ]
            
            # logging invalid customers in DataFrame
            self.add_rejects(invalid_customers,table_name,"customer_id not present in the customer table")

            # Drop invalid_customers            
            self.tables[table_name] = df.drop(index=invalid_customers.index)


    # 5) Quantity is greater and equal to zero  

    def validate_quantity(self):

        ord_df = self.tables["orders"]

        invalid_quantity = ord_df[
            ord_df["quantity"] < 0
        ]

        self.add_rejects(invalid_quantity,"orders","Quantity less than Zero")

        self.tables["orders"] = ord_df.drop(index=invalid_quantity.index)


    # 6) Validate price Must be numeric and ≥ 0 (not blank)

    def validate_amount(self):

        ord_df = self.tables["orders"]

        ord_df["amount"] = pd.to_numeric(ord_df["amount"],errors="coerce")

        invalid_amounts = ord_df[
            (ord_df["amount"] < 0 ) | (ord_df["amount"].isnull())
        ]

        self.add_rejects(invalid_amounts,"orders","amount is invalid")

        self.tables["orders"] = ord_df.drop(index = invalid_amounts.index)

    # 7) Parse to a real date from any of 3 formats (YYYY-MM-DD, DD/MM/YYYY, MM-DD-YYYY)

    def type_cast_date(self):

        ord_df = self.tables["orders"]

        formats = [
                "%Y-%m-%d",
                "%d/%m/%Y",
                "%m-%d-%Y"
            ]

        rejected_indexes=[]
        

        for index , row in ord_df.iterrows():

            date = str(row["order_date"])
            valid = False

            for fmt in formats:
                try:
                    parsed_date = dt.datetime.strptime(date,fmt)
                    ord_df.loc[index,"order_date"] = parsed_date
                    valid = True
                    break

                except ValueError:
                    continue

            if not valid:
                rejected_indexes.append(index)
        
        rejected_date_rows = ord_df.loc[rejected_indexes]

        self.add_rejects(rejected_date_rows,"orders","invalid date")

        self.tables["orders"] = ord_df.drop(index=rejected_date_rows.index)

        self.tables["orders"]["order_date"] = pd.to_datetime(self.tables["orders"]["order_date"])

    # 8 ) Standardise country Map variants to canonical (USA / India / UK / Germany)  

    def standardise_country(self):

        cust_df = self.tables["customers"]

        country_map =config.country_map
        
        self.tables["customers"]["country"] = cust_df["country"].apply(lambda x : country_map.get(x))

    # 9 ) Add email_present 
    def add_email_present(self):
      self.tables["customers"]["email_present"] = ~self.tables["customers"]["email"].isnull()


    # 10) Join exchange_rates -> (amount_usd = amount × rate_to_usd)

    def join_exchange_rates(self):

        exrates_df = self.tables["exchange_rates"]
        ord_df = self.tables["orders"]
        new_exchange_rate = pd.DataFrame(exrates_df,columns=["rates"])

        ord_df = pd.merge(
                left = ord_df,
                right = new_exchange_rate,
                how = "left",
                left_on = "currency",
                right_index = True,
            )

        ord_df["amount_usd"] = (ord_df["amount"] * ord_df["rates"]).round(2)

        invalid_exchange_rate = ord_df[ord_df["rates"].isnull()]
        
        self.add_rejects(invalid_exchange_rate,"orders","invalid currency")

        self.tables["orders"] = ord_df.drop(index=invalid_exchange_rate.index , columns=["rates"])


        prod_df = self.tables["products"]

        prod_df = pd.merge(
        left = prod_df,
        right = new_exchange_rate,
        how = "left",
        left_on = "currency",
        right_index = True,
        )

        prod_df["unit_price_usd"] = (prod_df["unit_price"] * prod_df["rates"]).round(2)

        invalid_exchange_rate = prod_df[prod_df["rates"].isnull()]
        
        self.add_rejects(invalid_exchange_rate,"products","invalid currency")

        self.tables["products"] = prod_df.drop(index=invalid_exchange_rate.index , columns=["rates"])


    

    # 11)  Business Rule :
    # * total = qty×price -> amount(already satisfy in orginal table)
    # * discount_value = total × discount/100 ;
    # * net_revenue = total − discount_value ;

    def business_rule(self):

        ord_df = self.tables["orders"]

        ord_df["discount_value"] = (ord_df["amount"] * config.discount) / 100

        ord_df["net_revenue"] = ord_df["amount"] - ord_df["discount_value"]

        self.tables["orders"] = ord_df.drop(columns=["discount_value"])

        


    # 12) price_tier : low <10, medium 10–<100, high ≥ 100 

    def price_tier(self):
        
        product_df  = self.tables["products"]

        product_df["price_tier"] = "High"

        product_df.loc[product_df["unit_price"]<10 , "price_tier"] = "Low"

        product_df.loc[(product_df["unit_price"]>=10) & (product_df["unit_price"]<100) , "price_tier"] = "Medium"

        self.tables["products"] = product_df

        self.tables["orders"] =  pd.merge(
            self.tables["orders"],
            product_df[["product_id","price_tier"]],
            how = "left",
            on = "product_id"
        )

        


    # 13) product_id of prodcuts must exist in product_id of orders

    def valid_product_id(self):
        
        product_df  = self.tables["products"]
        valid_product_id = set(product_df["product_id"])

        for table_name , df in config.validate_product_id.items():

            df = self.tables[table_name]
            
            invalid_product_id = df[
                ~df["product_id"].isin(valid_product_id) ]
            
            self.add_rejects(invalid_product_id,table_name,"invalid product_id")

            self.tables[table_name] = df.drop(index = invalid_product_id.index)

    
    # 14) Left-join returns → add is_returned flag (keep non-returned) 
    
    def is_returned_flag(self):

        ord_df = self.tables["orders"]
        returns_df = self.tables["returns"]

        ord_df["is_returned"] = ord_df["order_id"].isin(returns_df["order_id"])

        self.tables["orders"] = ord_df

    
    # 15) Aggregate per customer_id

    def aggregate_customers(self):

        ord_df = self.tables["orders"]
        today_date = pd.Timestamp.now()

        feature_customers_df = ord_df.groupby("customer_id").agg(
            total_orders = ("order_id","count"),
            total_spend_usd = ("amount_usd","sum"),
            avg_order_value = ("amount_usd","mean"),
            return_rate = ("is_returned","mean"),
            max_order_date = ("order_date","max")
        )

        feature_customers_df["days_since_last_order"] = today_date - feature_customers_df["max_order_date"]

        feature_customers_df["days_since_last_order"] = (
                feature_customers_df["days_since_last_order"].dt.days
                )

        feature_customers_df["return_rate"] = (
            (feature_customers_df["return_rate"]).round(2)
            )
        
        feature_customers_df = feature_customers_df.drop(columns=["max_order_date"])


        return feature_customers_df

    
    def web_session_count(self,feature_customers_df):

        web_df = self.tables["web_events"]

        web_session_count = web_df.groupby("customer_id").agg(
                    sessions_count = ("session", "nunique")
                    )
        web_session_count = web_session_count.reset_index() 

        feature_customers_df = pd.merge(
            feature_customers_df,
            web_session_count,
            how ="left",
            on = "customer_id"
        )
        return feature_customers_df
    

    def final_tables(self,feature_customers_df):

        fact_sales = self.tables["orders"]
        fact_sales = fact_sales[config.facts_sales]

        dim_customers  = self.tables["customers"]
        dim_customers=dim_customers[config.dim_customers]
        
        dim_products = self.tables["products"]
        dim_products = dim_products[config.dim_products]

        feature_customers = feature_customers_df
        feature_customers = feature_customers_df[config.feature_customers_df]
        return{
            "fact_sales" : fact_sales ,
            "dim_customers": dim_customers,
            "dim_products" : dim_products,
            "feature_customers" :feature_customers
        }
    


    def run(self):


        for df in self.tables.values():
            self.clean_strip(df)
            self.standardize_columns(df)

        self.remove_duplicates()

        self.validate_null()

        self.validate_customers()

        self.validate_quantity()

        self.validate_amount()

        self.type_cast_date()

        self.standardise_country()

        self.add_email_present()

        self.join_exchange_rates()

        self.business_rule()

        self.price_tier()

        self.valid_product_id()
        
        self.is_returned_flag()

        feature_customers_df = self.aggregate_customers()

        feature_customers_df = self.web_session_count(feature_customers_df)

        return self.final_tables(feature_customers_df)

    

if __name__ =="__main__":

    data = extract.extract_data()
    transform  = Transform(data)

    final_tables = transform.run()

    print(final_tables["fact_sales"])
    print(final_tables["dim_customers"])
    print(final_tables["dim_products"])
    print(final_tables["feature_customers"])


    cleaned_tables = transform.tables

    for df in cleaned_tables.values():
        print(df)
        print("="*75)

    print(transform.reject_logs["orders"])
    print("="*75)
    print(transform.reject_logs["products"])
    print("="*75)
    print(transform.reject_logs["customers"])
    print("="*75)
    print(transform.reject_logs["returns"])
    print("="*75)
    print(transform.reject_logs["web_events"])



    



