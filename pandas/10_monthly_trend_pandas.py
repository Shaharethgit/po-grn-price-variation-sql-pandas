# Problem: Monthly purchase trend
# Business impact: Shows how purchase spend moves month by month, to spot spikes and plan budgets
# Logic: GRN net amount grouped by month; running total with SUM() OVER; LAG() for change vs previous month


import pandas as pd
from sqlalchemy import create_engine
engine = create_engine(
    "mssql+pyodbc://@localhost/db_name"
        "?driver=ODBC+Driver+18+for+SQL+Server"
        "&trusted_connection=yes"
        "&TrustServerCertificate=yes"
)

grn_head = pd.read_sql("select * from grn_head", engine)
grn = grn_head.copy()
grn["month"] = grn["grn_date"].dt.strftime("%Y-%m")
grn = grn.groupby("month").agg(grn_count = ("grn_date", "count"),
                               purchase_value = ("net_amt", "sum")).reset_index()

grn = grn.sort_values("month", ascending=True)
grn["running_total"] = grn["purchase_value"].cumsum()
grn["change_pct"] = (grn["purchase_value"].pct_change() * 100).round(2)
grn["purchase_value"] = grn["purchase_value"].round(2)
grn["running_total"] = grn["running_total"].round(2)


print(grn)