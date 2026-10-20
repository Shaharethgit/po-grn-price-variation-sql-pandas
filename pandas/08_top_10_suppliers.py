# Problem: Top 10 suppliers by purchase value
# Business impact: Shows where most spend sits, to focus negotiations and supplier reviews
# Logic: sum of GRN net amount per supplier; DENSE_RANK() by purchase value; top 10 kept
# Note: likely duplicate GRNs from task 03 are not excluded



import pandas as pd
from sqlalchemy import create_engine
engine = create_engine(
    "mssql+pyodbc://@localhost/555"
        "?driver=ODBC+Driver+18+for+SQL+Server"
        "&trusted_connection=yes"
        "&TrustServerCertificate=yes"
)

grn_head = pd.read_sql("select * from grn_head", engine)
supplier = pd.read_sql("select * from supplier", engine)

grn_head = pd.read_sql("select * from grn_head", engine)
supplier = pd.read_sql("select * from supplier", engine)

grn = grn_head[["supp_code", "net_amt"]].copy()
grn["supp_code"] = grn["supp_code"].str.upper()
supplier["supp_code"] = supplier["supp_code"].str.upper()
grn = grn.merge(supplier, left_on="supp_code", right_on="supp_code", how="inner")
purchase = grn.groupby(["supp_code","supp_name"])["net_amt"].sum().reset_index()
purchase["share_pct"] = ((purchase["net_amt"] / purchase["net_amt"].sum()) * 100).round(2)
purchase = purchase.sort_values("net_amt", ascending=False)
purchase["supplier_rank"] = purchase["net_amt"].rank(method="dense", ascending=False).astype("int")
purchase = purchase[purchase["supplier_rank"] <=10]
purchase = purchase[['supplier_rank','supp_code', 'supp_name', 'net_amt', 'share_pct']]
purchase = purchase.rename(columns={"net_amt" : "purchase_Value"})
print(purchase)