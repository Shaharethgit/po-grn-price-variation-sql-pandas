-- Problem: Top 10 suppliers by purchase value
-- Business impact: Shows where most spend sits, to focus negotiations and supplier reviews
-- Logic: sum of GRN net amount per supplier; DENSE_RANK() by purchase value; top 10 kept
-- Note: likely duplicate GRNs from task 03 are not excluded


with purchase as (
select 
	a.supp_code,
	b.supp_name,
	SUM(a.net_amt) as Purchase_Value
from grn_head as a inner join supplier as b
	on a.supp_code = b.supp_code
group by a.supp_code, b.supp_name
),
ranked as(
select *,
	DENSE_RANK() over(order by Purchase_Value desc) as supplier_rank,
	cast((Purchase_Value * 1.0 / sum(Purchase_Value) over()) * 100.0 as decimal(10,2)) as share_pct
from purchase
)
select 
    supplier_rank,
	supp_code,supp_name,
	cast(Purchase_Value as decimal(14,2)) as purchase_Value,
	share_pct	
from 
    ranked 
where 
	supplier_rank <=10
order by 
	supplier_rank, supp_code
