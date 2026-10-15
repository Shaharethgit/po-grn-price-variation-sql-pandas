# Problem: Price change history per item
# Logic: same as queries/05_price_history.sql

import pandas as pd
from sqlalchemy import create_engine
engine = create_engine(
    "mssql+pyodbc://@localhost/db_name"
        "?driver=ODBC+Driver+18+for+SQL+Server"
        "&trusted_connection=yes"
        "&TrustServerCertificate=yes"
)

um_master = pd.read_sql("select * from um_master", engine)
po_head = pd.read_sql("select * from po_head", engine)
po_tran = pd.read_sql("select * from po_tran", engine)
grn_head = pd.read_sql("select * from grn_head", engine)
grn_tran = pd.read_sql("select * from grn_tran", engine)
product_master = pd.read_sql("select * from product_master", engine)
grn_tran["tran_no"] = grn_tran["tran_no"].astype(str).str.strip().str.lower()
grn_head["grn_no"]  = grn_head["grn_no"].astype(str).str.strip().str.lower()
p_master = product_master.copy()

grn = grn_tran.copy()
grn = grn_tran.merge(grn_head, left_on="tran_no", right_on="grn_no", how="inner", suffixes=("","_head"))
grn = grn.merge(um_master, left_on=["item_code", "pack_id"], right_on=["item_code", "pack_id"], how="inner")
grn = grn[['item_code', 'tran_no', 'grn_qty','net_amt','grn_date','um_units']]
grn["qty"] = grn["grn_qty"] * grn["um_units"]
grn = grn[grn["net_amt"] > 0]

df = grn[['item_code', 'tran_no', 'net_amt', 'grn_date','qty']].copy()
df = df.groupby(["item_code","grn_date","tran_no"]).agg(grn_qty = ("qty", "sum"),
                                                        net_amt = ("net_amt", "sum")).reset_index()
df["current_cost"] = (df["net_amt"] / df["grn_qty"]).round(2)
df = df.sort_values(["item_code","grn_date","tran_no"], ascending=[True, True, True])
df["previous_cost"] = df.groupby("item_code")["current_cost"].shift(1)

df = df[(df["previous_cost"].isna()) | (df["current_cost"] != df["previous_cost"])].copy()
df["previous_cost"] = df["previous_cost"].round(2)
df["difference"] = (df["current_cost"] - df["previous_cost"]).round(2)
df = df.merge(p_master, left_on="item_code", right_on="item_code", how="inner")
df = df[['item_code','item_des', 'grn_date','previous_cost','current_cost','difference']]
df = df.rename(columns={"grn_date" :"change_date"})
print(df)

