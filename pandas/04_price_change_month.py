# Problem: Items whose cost price changed this month
# Business impact: Shows cost changes early, so buyers can check margins and renegotiate
# Logic: unit cost = GRN net amount / base units, per GRN and item;
# compares the last cost before the month with the latest cost in the month



import pandas as pd
from sqlalchemy import create_engine

engine = create_engine(
    "mssql+pyodbc://@localhost/555"
    "?driver=ODBC+Driver+18+for+SQL+Server"
    "&trusted_connection=yes"
    "&TrustServerCertificate=yes"
    )
um_master = pd.read_sql("select * from um_master", engine)
grn_head = pd.read_sql("select * from grn_head", engine)
grn_tran = pd.read_sql("select * from grn_tran", engine)

grn = grn_tran.copy()
grn["tran_no"] = grn["tran_no"].str.lower()
grn_head["grn_no"] = grn_head["grn_no"].str.lower()
grn = grn.merge(grn_head, left_on="tran_no", right_on="grn_no", how="inner",suffixes=("","_head"))
grn = grn.merge(um_master, left_on=["item_code", "pack_id"], right_on=["item_code","pack_id"], how="inner", suffixes=("","_um"))
grn = grn[grn["net_amt"] > 0][['item_code', 'tran_no', 'grn_qty','net_amt','grn_date','um_units']]
grn["qty"] = grn["grn_qty"] * grn["um_units"]
grn = grn[['item_code', 'tran_no','net_amt', 'grn_date','qty']]
grn = grn.groupby(["item_code","tran_no","grn_date"]).agg(grn_qty = ("qty","sum"),
                                                          net_amt = ("net_amt", "sum")).reset_index()
last_month_grn = grn.copy()
today = pd.to_datetime('2026-09-07')
month_start = today.replace(day=1)
month_end = today + pd.offsets.MonthEnd(0)
last_month_grn = last_month_grn[last_month_grn["grn_date"] < month_start].copy()
last_month_grn["old_cost"] = (last_month_grn["net_amt"] / last_month_grn["grn_qty"]).round(2)

this_month_grn = grn.copy()
this_month_grn = grn[(grn["grn_date"] >= month_start) &
                     (grn["grn_date"] < month_end + pd.Timedelta(days=1))].copy()
this_month_grn["new_cost"] =  (this_month_grn["net_amt"] / this_month_grn["grn_qty"]).round(2)
last_month_grn = last_month_grn.sort_values(["item_code","grn_date","tran_no"], ascending=[True, False, False])
last_month_grn = last_month_grn.groupby("item_code").head(1)
this_month_grn = this_month_grn.sort_values(["item_code","grn_date","tran_no"], ascending=[True, False, False])
this_month_grn = this_month_grn.groupby("item_code").head(1)

result = this_month_grn.merge(last_month_grn, left_on="item_code", right_on="item_code", how="inner", suffixes=("","_lm")).copy()
result = result[['item_code','grn_date','old_cost','new_cost']]
result["cost_diff"] = (result["new_cost"] - result["old_cost"]).round(2)
result["cost_change_pct"] = (((result["new_cost"] - result["old_cost"]) / result["old_cost"]) * 100).round(2)
result = result.rename(columns={"grn_date" : "change_date"})
result = result[result["new_cost"] != result["old_cost"]]
result = result.sort_values("item_code", ascending=True)
print(result)
