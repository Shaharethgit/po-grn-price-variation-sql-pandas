-- Problem: Selling price below cost (negative margin)
-- Business impact: Shows packs sold at a loss, so prices can be corrected before more margin is lost
-- Logic: pack cost = last net cost per base unit x pack units;
-- a pack is listed when its retail price is below its cost


SELECT 
	p.item_code,
	p.item_des,
	u.pack_id,
	u.um_units,
	cast(u.um_units * p.last_net_cost	as decimal(10,2)) as pack_cost,
	pl.retail,
	cast(pl.retail - (u.um_units * p.last_net_cost) as decimal(10,2)) as margin,
	cast((pl.retail - (u.um_units * p.last_net_cost)) * 100.0 /
	nullif(pl.retail,0) as decimal(10,2)) as margin_pct
FROM product_master as p inner join um_master as u
	on p.item_code = u.item_code inner join price_level as pl
	on p.item_code = pl.item_code
	and u.pack_id = pl.pack_id
where pl.retail > 0
	and p.last_net_cost > 0
	and u.um_units * p.last_net_cost - pl.retail >= 0.01
order by
	margin_pct, p.item_code, u.pack_id;

