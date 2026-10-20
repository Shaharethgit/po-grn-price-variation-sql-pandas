# Problem: Supplier-wise delay and fill rate
# Business impact: Shows which suppliers deliver late or short, so buyers can act on them
# Logic: per PO, last GRN date vs expected delivery date; fill rate = received / ordered (base units)
# Note: as-of date 2026-08-31; POs with no GRN count as undelivered (overdue) or pending (not yet due)


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

today = pd.Timestamp("2026-08-31")
po = po_tran[['entry_no','po_qty', 'fqty','um_qty']].copy()
po["po_qty"] = po["po_qty"].fillna(0)
po["fqty"] = po["fqty"].fillna(0)
po["entry_no"] = po["entry_no"].str.lower()
po["order_qty"] = (po["po_qty"] + po["fqty"]) * po["um_qty"]
po = po.groupby("entry_no")["order_qty"].sum()
p_head = po_head[['entry_no','supp_code','del_date']].copy()
p_head["entry_no"] = p_head["entry_no"].str.lower()
p_head =  p_head.set_index("entry_no")
po = po.to_frame().join(p_head)
grn = grn_tran[['item_code', 'tran_no', 'grn_qty', 'foc_qty','pack_id']].copy()
grn['grn_qty'] = grn['grn_qty'].fillna(0)
grn['foc_qty'] = grn['foc_qty'].fillna(0)

grn = grn.merge(um_master, left_on=["item_code", "pack_id"], right_on=["item_code", "pack_id"], how="inner")
grn["recieved_qty"] = (grn["grn_qty"] * grn["um_units"]) + grn["foc_qty"]
g_head = grn_head[['grn_no', 'grn_date','po_no']].copy()
g_head["grn_no"] = g_head["grn_no"].str.lower()
grn["tran_no"] = grn["tran_no"].str.lower()
g_head["po_no"] = g_head["po_no"].str.lower()
grn = grn.merge(g_head, left_on="tran_no", right_on="grn_no", how="inner")
grn = grn.groupby("po_no").agg(recieved_qty = ("recieved_qty", "sum"),
                                latest_grn_date = ("grn_date", "max"))
result = po.join(grn).reset_index()
df = result[['supp_code', 'entry_no', 'order_qty', 'del_date', 'recieved_qty',
       'latest_grn_date']].copy()
df = df[df["supp_code"].notna()].copy()
df["late_days"] = (df["latest_grn_date"] - df["del_date"]).dt.days
total_po = df.groupby("supp_code")["entry_no"].count()
late_po = df[df["late_days"] > 0]
late_po = late_po.groupby("supp_code")["entry_no"].count()
undelivered_po = df[(df["late_days"].isna()) & (df["del_date"] < today)]
undelivered_po = undelivered_po.groupby("supp_code")["entry_no"].count()
pending_po = df[(df["late_days"].isna()) & (df["del_date"] >= today)]
pending_po = pending_po.groupby("supp_code")["entry_no"].count()
on_time = df[df["late_days"] <= 0]
on_time = on_time.groupby("supp_code")["entry_no"].count()
Avg_Delay = df[df["late_days"] > 0]
Avg_Delay = Avg_Delay.groupby("supp_code")["late_days"].mean().round(2)
ordered_qty = df.groupby("supp_code")["order_qty"].sum()
received_qty = df.groupby("supp_code")["recieved_qty"].sum()
final_result = pd.DataFrame({
    "total_po" : total_po,
    "late_po" : late_po,
    "undelivered_po" : undelivered_po,
    "pending_po" : pending_po,
    "on_time" : on_time,
    "Avg_Delay" : Avg_Delay,
    "ordered_qty" : ordered_qty,
    "received_qty" : received_qty
})
final_result["fill_rate"] = ((final_result["received_qty"] / final_result["ordered_qty"].replace(0, np.nan)) * 100).round(2)
final_result = final_result.reset_index()
final_result[["total_po", "late_po", "undelivered_po", "pending_po", "on_time"]] = final_result[
    ["total_po", "late_po", "undelivered_po", "pending_po", "on_time"]].fillna(0).astype(int)
print(final_result.head(10))
