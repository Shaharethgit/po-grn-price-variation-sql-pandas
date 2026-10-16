-- Problem: Price change history per item
-- Business impact: Shows how each item's cost moved over time, to spot repeated increases
-- Logic: unit cost = GRN net amount / base units, per GRN and item;
-- LAG() gives the previous cost; the first cost and every later change are listed
-- Note: costs rounded to 2 decimals; free (FOC) units are not counted in the unit cost

with grn as(
select 
	a.item_code,a.tran_no, p.item_des, b.grn_date,
	sum(a.grn_qty * u.um_units) as grn_qty,
	sum(a.net_amt) as net_amt
from ((grn_tran as a
	inner join grn_head as b
    on a.tran_no = b.grn_no)
	inner join product_master as p
    on a.item_code = p.item_code)
	inner join um_master as u
	on a.item_code = u.item_code
	and a.pack_id = u.pack_id
	where a.net_amt > 0
group by
	a.item_code,p.item_des,b.grn_date,a.tran_no
	),

current_cost as(
select
	item_code, item_des, grn_date ,tran_no, cast(net_amt / grn_qty as decimal(10,2))  as current_cost
from grn
)

,result as (
select *,
	LAG(current_cost) over(partition by item_code order by grn_date, tran_no) as previous_cost
from current_cost
	)
	select item_code, item_des, grn_date as change_date,
	previous_cost, current_cost,
	current_cost - previous_cost as difference
	from result 
	where previous_cost is null or
	current_cost <> previous_cost
	order by item_code, grn_date, tran_no
	 
	