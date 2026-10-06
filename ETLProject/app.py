from flask import Flask, render_template
import pandas as pd
from sqlalchemy import create_engine

app = Flask(__name__)

# Database Configuration
SERVER = "localhost"
DATABASE = "SalesDB"
DRIVER = "ODBC Driver 17 for SQL Server"
connection_string = f"mssql+pyodbc://@{SERVER}/{DATABASE}?driver={DRIVER}&trusted_connection=yes"

engine = create_engine(connection_string)

@app.route("/")
def dashboard():
    # Retrieve Sales table from SQL Server
    sales_df = pd.read_sql("SELECT * FROM Sales", con=engine)
    
    # Calculate key aggregate metrics
    total_sales = sales_df["total_amount"].sum() if not sales_df.empty else 0
    total_orders = sales_df["order_id"].nunique() if not sales_df.empty else 0
    total_units = sales_df["quantity"].sum() if not sales_df.empty else 0
    
    sales_records = sales_df.to_dict(orient="records")
    
    return render_template(
        "index.html",
        sales=sales_records,
        total_sales=f"${total_sales:,.2f}",
        total_orders=f"{total_orders:,}",
        total_units=f"{total_units:,}"
    )

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)