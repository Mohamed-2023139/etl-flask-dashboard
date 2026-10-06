import io
import pandas as pd
import requests
from sqlalchemy import create_engine

# ==========================================
# 1. EXTRACT
# ==========================================

# Load local files
customers_df = pd.read_csv("customers.csv")
orders_df = pd.read_parquet("orders.parquet")

# Retrieve Products CSV from API endpoint
PRODUCTS_URL = "https://raw.githubusercontent.com/MohammedHameds/test1455/refs/heads/main/products.csv"
response = requests.get(PRODUCTS_URL)
response.raise_for_status()
products_df = pd.read_csv(io.StringIO(response.text))


# ==========================================
# 2. TRANSFORM
# ==========================================

# --- Clean Customers ---
customers_df = customers_df.drop_duplicates()

if "city" in customers_df.columns:
    customers_df["city"] = customers_df["city"].astype(str).str.strip().str.title()

if "age" in customers_df.columns:
    customers_df = customers_df[(customers_df["age"] > 0) & (customers_df["age"] < 120)]

if "email" in customers_df.columns:
    customers_df["email"] = customers_df["email"].fillna("N/A")

# Create full_name column
if "first_name" in customers_df.columns and "last_name" in customers_df.columns:
    customers_df["full_name"] = (
        customers_df["first_name"].astype(str).str.strip()
        + " "
        + customers_df["last_name"].astype(str).str.strip()
    )
elif "name" in customers_df.columns:
    customers_df["full_name"] = customers_df["name"].astype(str).str.strip()
else:
    customers_df["full_name"] = "Customer " + customers_df["customer_id"].astype(str)


# --- Clean Orders ---
orders_df = orders_df.drop_duplicates(subset=["order_id"])
orders_df = orders_df[orders_df["quantity"] > 0]
orders_df["order_date"] = pd.to_datetime(orders_df["order_date"], errors="coerce")
orders_df = orders_df.dropna(subset=["order_date"])

# Validate customer_id exists in customers dataset
orders_df = orders_df[orders_df["customer_id"].isin(customers_df["customer_id"])]


# --- Clean Products ---
products_df = products_df.drop_duplicates()

prod_col = "product" if "product" in products_df.columns else "product_name"
if prod_col in products_df.columns:
    products_df[prod_col] = products_df[prod_col].astype(str).str.strip().str.title()

if "category" in products_df.columns:
    products_df["category"] = products_df["category"].astype(str).str.strip().str.title()

# Convert unit_price to numeric & validate
products_df["unit_price"] = pd.to_numeric(products_df["unit_price"], errors="coerce")
products_df = products_df[products_df["unit_price"] > 0]


# --- Merge & Build Sales Dataset ---
# Join orders with customers and products
merged_df = orders_df.merge(customers_df, on="customer_id", how="inner")
merged_df = merged_df.merge(products_df, on="product_id", how="inner")

# Calculate total_amount
merged_df["total_amount"] = merged_df["quantity"] * merged_df["unit_price"]

# Construct final Sales dataframe structure
sales_df = pd.DataFrame({
    "order_id": merged_df["order_id"],
    "customer": merged_df["full_name"],
    "product": merged_df[prod_col],
    "quantity": merged_df["quantity"],
    "unit_price": merged_df["unit_price"],
    "total_amount": merged_df["total_amount"]
})


# ==========================================
# 3. LOAD TO SQL SERVER
# ==========================================

# Configure database credentials
SERVER = "ALNAFRAWI"
DATABASE = "SalesDB"
DRIVER = "ODBC Driver 17 for SQL Server"

# Connection string for SQLAlchemy
connection_string = f"mssql+pyodbc://@{SERVER}/{DATABASE}?driver={DRIVER}&trusted_connection=yes"
engine = create_engine(connection_string)

# Load data into SQL Server
sales_df.to_sql("Sales", con=engine, if_exists="replace", index=False)
print("ETL pipeline executed successfully. 'Sales' table loaded into SQL Server.")