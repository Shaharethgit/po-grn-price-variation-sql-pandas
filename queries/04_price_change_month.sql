-- Problem: Items whose cost price changed this month
-- Business impact: Shows cost changes early, so buyers can check margins and renegotiate
-- Logic: unit cost = GRN net amount / base units, per GRN and item;
-- compares the last cost before the month with the latest cost in the month

declare @today as date
set @today = '2026-09-07'
declare @last_month as date
set @last_month = DATEADD(MONTH, -1, @today)

;with grn_all as(
select 
	a.item_code, a.tran_no,	b.grn_date,
	sum(a.grn_qty * u.um_units) as grn_qty,
	sum(a.net_amt) as net_amt
from
	(grn_tran as a left join grn_head as b
	on a.tran_no = b.grn_no)
	inner join um_master as u
	on a.item_code = u.item_code
	and a.pack_id = u.pack_id
where a.net_amt > 0
group by a.item_code,
	a.tran_no, b.grn_date
	),

last_month_grn_all as (
select
	item_code,tran_no,grn_date,
	cast(net_amt / grn_qty as decimal(10,2)) as old_cost,
	row_number() over(partition by item_code order by grn_date desc, tran_no desc) as rn
from
	grn_all
where
	grn_date <= EOMONTH(@last_month)
),

last_month_grn as(
select *
from last_month_grn_all
where rn = 1
),

this_month_grn_all as (
select
	item_code,tran_no,grn_date,
	cast(net_amt / grn_qty as decimal(10,2)) as new_cost,
	row_number() over(partition by item_code order by grn_date desc, tran_no desc) as rn2
from
	grn_all
where
	grn_date >  EOMONTH(@last_month)
	and grn_date <= EOMONTH(@today)
	),

this_month_grn as(
select *
from this_month_grn_all 
where rn2 = 1
)

select a.item_code, a.grn_date as change_date, b.old_cost, a.new_cost,
	cast(a.new_cost - b.old_cost as decimal(10,2)) as cost_diff,
	cast(((a.new_cost - b.old_cost) / b.old_cost) * 100 as decimal(10,2)) as cost_change_pct
from this_month_grn as a  inner join last_month_grn as b
on a.item_code = b.item_code
where a.new_cost <> b.old_cost
order by item_code