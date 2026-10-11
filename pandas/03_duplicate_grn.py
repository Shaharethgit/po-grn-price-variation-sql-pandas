
import pandas as pd
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

grn = grn_tran.copy()
po = po_tran.copy()

grn = grn.merge(
        um_master, 
        left_on=["item_code","pack_id"], 
        right_on=["item_code", "pack_id"],
        how="inner", 
        suffixes=("", "_um"))
grn["received_qty"] = (grn["grn_qty"] * grn["um_units"]) + grn["foc_qty"]
grn = grn.groupby(["item_code","tran_no"])["received_qty"].sum().reset_index()

grn["tran_no"] = grn["tran_no"].astype(str).str.strip().str.lower()
grn_head["grn_no"] = grn_head["grn_no"].astype(str).str.strip().str.lower()
grn_head["po_no"] = grn_head["po_no"].astype(str).str.strip().str.lower()
po["entry_no"] = po["entry_no"].astype(str).str.strip().str.lower()


grn = grn.merge(
        grn_head, 
        left_on="tran_no",
        right_on="grn_no",
        how="inner"
)
grn = grn[["item_code", "tran_no", "received_qty", "po_no", "supp_code"]]
po = po[["entry_no", "item_code", "po_qty", "fqty", "um_qty"]].copy()
po["fqty"] = po["fqty"].fillna(0)
po["ordered_qty"] = (po["po_qty"] + po["fqty"]) * po["um_qty"]

po = po.groupby(["entry_no","item_code"])["ordered_qty"].sum().reset_index()

grn = grn.merge(
        po,
        left_on=["po_no","item_code"],
        right_on=["entry_no","item_code"],
        how="inner",
        suffixes=("","_po")
)

grn = grn[['po_no','supp_code','item_code', 'tran_no', 'ordered_qty','received_qty']]
grn = grn.groupby(["po_no","supp_code","item_code"]).agg(times_entered = ("tran_no", "count"),
                                                         ordered_qty = ("ordered_qty", "min"),
                                                         total_received_qty = ("received_qty", "sum")).reset_index()

result = grn[(grn["total_received_qty"] > grn["ordered_qty"]) & (grn["times_entered"] >1)]    
print(result)      

