# Problem: Slow-moving items (estimated stock)
# Business impact: Shows stock that is not selling, so it can be discounted or stopped from reordering
# Logic: est_stock = GRN received - POS sales (base units); listed when est_stock > 0,
# the last receipt is older than 30 days and there is no sale in the last 30 days
# Note: as-of date 2026-08-31; no stock table, so opening stock, returns and adjustments are not included

import pandas as pd
import numpy as np
from sqlalchemy import create_engine
engine = create_engine(
    "mssql+pyodbc://@localhost/555_sha!"
        "?driver=ODBC+Driver+18+for+SQL+Server"
        "&trusted_connection=yes"
        "&TrustServerCertificate=yes"
)

um_master = pd.read_sql("select * from um_master", engine)
po_head = pd.read_sql("select * from po_head", engine)
po_tran = pd.read_sql("select * from po_tran", engine)
grn_head = pd.read_sql("select * from grn_head", engine)
grn_tran = pd.read_sql("select * from grn_tran", engine)
supplier = pd.read_sql("select * from supplier", engine)
pos_sales = pd.read_sql("select * from pos_sales", engine)
barcode = pd.read_sql("select * from barcode", engine)
pos_sales["prod_id"] = pos_sales["prod_id"].astype(str).str.strip()
um_master["item_code"] = um_master["item_code"].astype(str).str.strip()
grn_tran["item_code"] = grn_tran["item_code"].astype(str).str.strip()
product_master = pd.read_sql("select * from product_master", engine)

po_sale = pos_sales.copy()
barc = barcode.copy()
grn = grn_tran.copy()

po_sale["barcode"] = po_sale["barcode"].astype("str").str.strip()
barc["barcode"] = barc["barcode"].astype("str").str.strip()
po_sale = po_sale.merge(barc, left_on="barcode", right_on="barcode", how="inner", suffixes=("","_asdsada"))
po_sale = po_sale.merge(um_master, left_on=["prod_id", "pack_id"], right_on=["item_code", "pack_id"], how="inner")
po_sale["sale_qty"] = po_sale["qty"] * po_sale["um_units"]
po_sale = po_sale.groupby("prod_id")["sale_qty"].sum().reset_index()
po_sale["sale_qty"] = -1 * po_sale["sale_qty"]

grn["grn_qty"] = grn["grn_qty"].fillna(0)
grn["foc_qty"] = grn["foc_qty"].fillna(0)
grn = grn.merge(um_master, left_on=["item_code", "pack_id"], right_on=["item_code", "pack_id"], how="inner")
grn["received_qty"] = (grn["grn_qty"] * grn["um_units"]) + grn["foc_qty"]
grn = grn.groupby("item_code")["received_qty"].sum().reset_index()
po_sale = po_sale.rename(columns={"prod_id" : "item_code", "sale_qty" : "qty"})
grn = grn.rename(columns={"received_qty" : "qty"})

stock = pd.concat([po_sale, grn])
stock = stock.groupby("item_code")["qty"].sum().reset_index()

last_receipt = grn_tran.copy()
last_receipt["tran_no"] = last_receipt["tran_no"].str.strip().str.upper()
head = grn_head.copy()
head["grn_no"] = head["grn_no"].str.strip().str.upper()

last_receipt = last_receipt.merge(head, left_on="tran_no", right_on="grn_no", how="inner")
last_receipt = last_receipt.groupby("item_code")["grn_date"].max().reset_index()
last_sale = pos_sales.copy()
last_sale = last_sale.groupby("prod_id")["tran_date"].max().reset_index()
result = stock.merge(last_receipt, left_on="item_code", right_on="item_code", how="inner")
result = result.rename(columns={"qty" : "est_stock", "grn_date" : "last_receipt"})


result = result.merge(last_sale, left_on="item_code", right_on="prod_id", how="left")
result = result.rename(columns={"tran_date" : "last_sale"})
result = result.drop(columns="prod_id")

today = pd.Timestamp('2026-08-31')
result = result[result["est_stock"] > 0]
result["last_receipt"] = pd.to_datetime(result["last_receipt"], errors="coerce").dt.normalize()
result["last_sale"] = pd.to_datetime(result["last_sale"], errors="coerce").dt.normalize()

category = (
     (result["est_stock"] > 0) & ((today - result["last_receipt"]).dt.days > 30)
     & ((today - result["last_sale"]).dt.days > 30),
     (result["est_stock"] > 0) & (result["last_sale"].isna())
          & ((today - result["last_receipt"]).dt.days > 30)

)
labels = [(today - result["last_sale"]).dt.days, (today - result["last_receipt"]).dt.days]
result["idle_days"] = np.select(category, labels, default=np.nan)
result = result.sort_values("idle_days", ascending=False)
result = result[result["idle_days"].notna()]
result = result.merge(product_master, left_on="item_code", right_on="item_code", how="inner")
result = result[['item_des', 'est_stock', 'last_receipt', 'last_sale', 'idle_days']].reset_index()
print(result)