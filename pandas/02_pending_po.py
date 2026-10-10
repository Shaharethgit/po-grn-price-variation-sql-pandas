
import pandas as pd
import numpy as np
from sqlalchemy import create_engine

engine = create_engine(
    "mssql+pyodbc://@localhost/555"
    "?driver=ODBC+Driver+18+for+SQL+Server"
    "&trusted_connection=yes"
    "&TrustServerCertificate=yes"
    )
po_head = pd.read_sql("select * from po_head", engine)
grn_head = pd.read_sql("select * from grn_head", engine)

grn_head["po_no"] = grn_head["po_no"].str.strip().str.lower()
po_head["entry_no"] = po_head["entry_no"].str.strip().str.lower()
result = po_head.merge(grn_head, left_on="entry_no", right_on="po_no", how="left", suffixes=("","s"))
result = result[result["po_no"].isna()][["entry_no"]].reset_index(drop=True)
result = result.sort_values("entry_no", ascending=False)
result = result.rename(columns={"entry_no" :"po_no"})
print(result.head(10))