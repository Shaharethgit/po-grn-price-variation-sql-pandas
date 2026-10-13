
with grn_all as(
select 
	a.item_code, a.tran_no,	b.grn_date,
	cast(sum(a.grn_qty * u.um_units) as decimal(8,2)) as grn_qty,
	cast(sum(a.net_amt) as decimal(8,2)) as net_amt
from
	(grn_tran as a left join grn_head as b
	on a.tran_no = b.grn_no)
	inner join um_master as u
	on a.item_code = u.item_code
	and a.pack_id = u.pack_id
where a.net_amt > 0
group by a.item_code,
	a.tran_no, b.grn_date

)
SELECT *,
	cast(net_amt / grn_qty as DECIMAL(10,2)) as unit_cost 
	from grn_all
