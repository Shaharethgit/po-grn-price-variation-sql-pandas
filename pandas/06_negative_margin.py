# Problem: Selling price below cost (negative margin)
# Business impact: Shows packs sold at a loss, so prices can be corrected before more margin is lost
# Logic: pack cost = last net cost per base unit x pack units;
# a pack is listed when its retail price is below its cost


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
product_master = pd.read_sql("select * from product_master", engine)
price_level = pd.read_sql("select * from price_level", engine)
p_master = product_master
p_master = p_master.merge(um_master, left_on="item_code", right_on="item_code", how="inner")
p_master = p_master.merge(price_level, left_on=["item_code", "pack_id"], right_on=["item_code","pack_id"], how="inner")
p_master["pack_cost"] = (p_master["last_net_cost"] * p_master["um_units"])
df = p_master[['item_code','item_des','pack_id','um_units','pack_cost','retail','last_net_cost']].copy()
df["margin"] = df["retail"] - df["pack_cost"]
df["margin_pct"] = ((df["retail"] - df["pack_cost"]) * 100.0 ) / df["retail"].replace(0,np.nan)
df = df[(df["retail"] > 0) & (df["last_net_cost"] > 0) & ((df["last_net_cost"] * df["um_units"]) - df["retail"] >= 0.01)].copy()
df = df[['item_code', 'item_des', 'pack_id', 'um_units', 'pack_cost', 'retail','margin', 'margin_pct']]
df["pack_cost"] = df["pack_cost"].round(2)
df["margin"] = df["margin"].round(2)
df["margin_pct"] = df["margin_pct"].round(2)
df = df.sort_values(["margin_pct", "item_code", "pack_id"])

print(df)  