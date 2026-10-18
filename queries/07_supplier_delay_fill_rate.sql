declare @today as date
set @today = '2026-08-31'

;with po_wise_qty as(
select
	entry_no,
	sum((coalesce(po_qty,0) + coalesce(fqty,0)) * um_qty) as po_qty
from po_tran
group by
	entry_no
	),
po_wise_qty_with_supp_del_date as(
select 
	b.supp_code,
	a.*,	
	b.del_date	
from po_wise_qty as a inner join po_head as b
	on a.entry_no = b.entry_no 
	),
grn_wise_qty as(
select
	a.item_code,
	tran_no,
	(coalesce(a.grn_qty, 0) * b.um_units) + coalesce(foc_qty,0) as grn_qty
from grn_tran as a inner join um_master as b
	on a.item_code = b.item_code
	and a.pack_id = b.pack_id		
	),
grn_wise_qty_with_po as(
select 
	b.po_no,
	max(grn_date) as latest_grn_date,
	sum(grn_qty) as grn_qty
from grn_wise_qty a inner join grn_head as b
	on a.tran_no = b.grn_no
group by
	b.po_no
	),
grn_po_with_late_days as(
	select *,
	DATEDIFF(DAY, a.del_date, b.latest_grn_date) as late_days
from 
	po_wise_qty_with_supp_del_date as a
	left join grn_wise_qty_with_po as b
	on a.entry_no = b.po_no
	where a.supp_code is not null
	),
summary as(
select 
	supp_code,
	count(entry_no) as Total_POs,
	count(case
		when late_days > 0
		then entry_no
	end) Late_POs,

	count(case
		when late_days is null and del_date < @today
		then entry_no
	end) Undelivered_POs ,

	count(case
		when late_days is null and del_date >= @today
		then entry_no
	end) Pending_POs,

	count(case
		when late_days <= 0
		then entry_no
	end) On_Time_POs,

	cast(avg(case
		when late_days > 0
		then late_days * 1.0
	end) as decimal(10,2)) as Avg_Delay,

	sum(po_qty) as Ordered_Qty,
	sum(grn_qty) as Received_Qty,

	cast(((sum(grn_qty) * 1.00) /
	sum(po_qty)) * 100.0 as decimal(10,2)) as Fill_Rate
	
from grn_po_with_late_days
group by
	supp_code
	)
select
	b.supp_name, 
	a.*
from summary as a inner join supplier as b
	on a.supp_code = b.supp_code
order by b.supp_code


