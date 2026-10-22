-- Problem: Monthly purchase trend
-- Business impact: Shows how purchase spend moves month by month, to spot spikes and plan budgets
-- Logic: GRN net amount grouped by month; running total with SUM() OVER; LAG() for change vs previous month

with myear as(
select	
	convert(char(7), grn_date, 126) as Month,
	MONTH(grn_date) as m,	
	YEAR(grn_date) as y,
	sum(net_amt) as Monthly_Purchase,
	COUNT(grn_no) as grn_count
	
from grn_head
group by FORMAT(grn_date,'yyyy-MM'), MONTH(grn_date) , YEAR(grn_date) ,convert(char(7), grn_date, 126)
)
select
	Month,
	grn_count,
	cast(Monthly_Purchase as decimal(14,2)) as Monthly_Purchase,
	SUM(Monthly_Purchase) over(order by y, m) as Running_Total,
	cast(((Monthly_Purchase - lag(Monthly_Purchase) over(order by y, m)) * 100.0
    / nullif(lag(Monthly_Purchase) over(order by y, m), 0)) as decimal(10,2)) as pct_change
from myear 
order by y,m



