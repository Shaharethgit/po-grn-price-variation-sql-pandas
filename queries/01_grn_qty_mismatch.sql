
-- Problem: GRN received more or less than PO qty
-- Business impact: Flags over-receipts (overpayment) and short receipts (stock-outs)
-- Logic: ordered_qty  = (po_qty + free qty) x pack units
--        received_qty = grn_qty x pack units + foc qty
--        Both in base units; all GRNs of a PO are added together.
 SELECT * from um_master
with c1 as (
 SELECT a.item_code,
        b.po_no,
        sum((a.grn_qty * um_units) + a.foc_qty) as received_qty
        FROM (grn_tran as a
        INNER JOIN grn_head as b
        on a.tran_no  = b.grn_no)
        inner JOIN um_master as u
        on a.item_code = u.item_code
        and a.pack_id = u.pack_id
        GROUP BY
        a.item_code,
        b.po_no
), c2 as (SELECT entry_no,
    item_code,
    sum((po_qty + COALESCE(fqty,0)) * um_qty ) as  ordered_qty
    from po_tran
    GROUP BY
    entry_no,
    item_code
)
    SELECT c1.po_no,
        c1.item_code,        
        c2.ordered_qty,
        c1.received_qty,
        c1.received_qty - c2.ordered_qty as diff_qty,
        case
            when c2.ordered_qty = c1.received_qty then 'Exact'
            when c2.ordered_qty < c1.received_qty then 'Over'
            else 'Short'
        end as status
     from c1 INNER JOIN c2
     on c1.po_no = c2.entry_no
     and c1.item_code = c2.item_code
      ORDER BY ABS(c1.received_qty - c2.ordered_qty) DESC, c1.po_no ASC, c1.item_code ASC
    

     
/* Sample result (first 11 rows):
po_no        | item_code | ordered_qty | received_qty | diff_qty | status
-------------+-----------+-------------+--------------+----------+-------
PO0012603906 | 100012791 | 2880        | 1440         | -1440    | Short
PO0012604581 | 100006513 | 1760        | 440          | -1320    | Short
PO0012603417 | 100003490 | 1000        | 150          | -850     | Short
PO0012604943 | 100200008 | 1200        | 400          | -800     | Short
PO0012603891 | 100006513 | 1320        | 660          | -660     | Short
PO0012604905 | 100006513 | 1320        | 660          | -660     | Short
PO0012605214 | 100006513 | 1320        | 660          | -660     | Short
PO0012603545 | 100010911 | 1152        | 576          | -576     | Short
PO0012604647 | 100009586 | 576         | 1152         | 576      | Over
PO0012605217 | 100176250 | 576         | 48           | -528     | Short
PO0012603289 | 100006513 | 1056        | 528          | -528     | Short
*/
  