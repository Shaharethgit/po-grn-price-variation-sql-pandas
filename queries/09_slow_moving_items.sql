-- Problem: Slow-moving items (estimated stock)
-- Business impact: Shows stock that is not selling, so it can be discounted or stopped from reordering
-- Logic: est_stock = GRN received - POS sales (base units); listed when est_stock > 0,
--        the last receipt is older than 30 days and there is no sale in the last 30 days
-- Note: as-of date 2026-08-31; no stock table, so opening stock, returns and adjustments are not included


declare @today as date
set @today = '2026-08-31'

;with po_sales as(
select 
	c.item_code,
	a.barcode,
	a.qty,
	b.pack_id,
	c.um_units,
	a.qty * c.um_units as sale_qty,
	a.tran_date
from pos_sales as a inner join barcode b
	on a.barcode = b.barcode inner join um_master as c
	on a.prod_id = c.item_code and b.pack_id = c.pack_id
	),
sales_grn as(
select 
	item_code,
	-1 * sum(sale_qty) as sales_qty
from po_sales
group by item_code
union all
select 
	a.item_code,
	sum((coalesce(a.grn_qty,0) * b.um_units) + coalesce(a.foc_qty,0)) as grn_qty
from grn_tran as a inner join um_master as b
	on a.item_code = b.item_code and a.pack_id = b.pack_id 
group by a.item_code
),
stock as(
select 
	item_code,
	sum(sales_qty) as stock
from 
	sales_grn
group by 
	item_code
	),
last_sales as(
select 
	prod_id,
	max(tran_date) as last_sale
from pos_sales
group by
	prod_id
	),
last_receipts as(
select
	a.item_code, 
	max(b.grn_date) as last_receipt 	
from grn_tran as a inner join grn_head as b
	on a.tran_no = b.grn_no
group by
	a.item_code
),
result as(
select 
	a.item_code,
	a.stock as est_stock,
	cast(b.last_receipt as date) as last_receipt,
	cast(c.last_sale as date) last_sale
from (stock as a inner join last_receipts as b
	on a.item_code = b.item_code) 
	left join last_sales as c
	on a.item_code = c.prod_id
	),
idle_day as(
select 
	*,
	case
		when 
			est_stock > 0 and 
			datediff(day, last_receipt, @today) > 30
			and DATEDIFF(DAY,last_sale, @today) > 30
		then DATEDIFF(DAY, last_sale, @today)
		when 
			est_stock > 0 and
			last_sale is null and
			datediff(day, last_receipt, @today) > 30
		then
		    DATEDIFF(DAY, last_receipt, @today)					
	end as idle_days
from result
)
select 
	b.item_des,
	a.est_stock,
	a.last_receipt,
	a.last_sale,
	a.idle_days
from idle_day a
	inner join product_master as b
	on a.item_code = b.item_code
where 
	idle_days is not null
