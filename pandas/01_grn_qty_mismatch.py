# Problem: GRN received more or less than PO qty
# Business impact: Flags over-receipts (overpayment) and short receipts (stock-outs)
# Logic: ordered_qty  = (po_qty + free qty) x pack units
# received_qty = grn_qty x pack units + foc qty
# Both in base units; all GRNs of a PO are added together.

import pandas as pd
import numpy as np
from sqlalchemy import create_engine

engine = create_engine(
    "mssql+pyodbc://@localhost/555"
    "?driver=ODBC+Driver+18+for+SQL+Server"
    "&trusted_connection=yes"
    "&TrustServerCertificate=yes"
    )

um_master = pd.read_sql("select * from um_master", engine)
po_head = pd.read_sql("select * from po_head", engine)
po_tran = pd.read_sql("select * from po_tran", engine)
grn_head = pd.read_sql("select * from grn_head", engine)
grn_tran = pd.read_sql("select * from grn_tran", engine)

grn = grn_tran.merge(grn_head, left_on="tran_no", right_on="grn_no", how="inner")
grn = grn[['item_code', 'tran_no', 'grn_qty', 'foc_qty','pack_id','po_no']]
grn = grn.merge(um_master,left_on=["item_code","pack_id"], right_on=["item_code","pack_id"], how="inner")
grn["received_qty"] = (grn["grn_qty"] * grn["um_units"]) + grn["foc_qty"]
grn = grn[['item_code','po_no','received_qty']]
grn = grn.groupby(["item_code", "po_no"])["received_qty"].sum().reset_index()
po = po_tran[['entry_no','item_code', 'po_qty', 'fqty','um_qty']]
po["fqty"] = po["fqty"].fillna(0)
po["ordered_qty"] = (po["po_qty"] + po["fqty"]) * po["um_qty"]
po = po.groupby(["entry_no","item_code"])["ordered_qty"].sum().reset_index()
grn["po_no"] = grn["po_no"].str.upper()
po["entry_no"] = po["entry_no"].str.upper()
result = grn.merge(po, left_on=["po_no","item_code"], right_on=["entry_no","item_code"], how="inner")
result = result[['po_no','item_code' ,'ordered_qty', 'received_qty']]
result["diff_qty"] = result["received_qty"] - result["ordered_qty"] 
conditions = (
    result["ordered_qty"] < result["received_qty"],
    result["ordered_qty"] > result["received_qty"],
)
labels = ["Over", "Short"]
result["status"] = np.select(conditions,labels,default="Exact")
result["abs_diff"] = result["diff_qty"].abs()
result = result.sort_values(["abs_diff", "po_no","item_code"], ascending=[False, True,True])
result = result.drop(columns="abs_diff")

print(result.head(15))

