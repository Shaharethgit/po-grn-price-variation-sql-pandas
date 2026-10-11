-- Problem: Same GRN entered twice
-- Business impact: Duplicate entries inflate stock and purchase value and can cause double payment
-- Logic: ordered_qty  = (po_qty + free qty) x pack units
--        received_qty = grn_qty x pack units + foc qty (totalled per GRN and item)
--        Flagged when the same item on a PO is received in more than one GRN
--        and the total received is more than the PO quantity.

WITH grn as (
    select a.*,b.po_no,b.supp_code
        from
        (SELECT a.item_code,
        a.tran_no,
        SUM((a.grn_qty * b.um_units) + a.foc_qty) as received_qty
    
        from grn_tran as a
        INNER JOIN um_master as b
        on a.item_code = b.item_code
        and a.pack_id = b.pack_id
        GROUP BY 
        a.item_code,
        a.tran_no) as a INNER JOIN
        grn_head as b 
        on a.tran_no = b.grn_no

),
po as (

   SELECT entry_no,
     item_code,
     SUM((po_qty + COALESCE(fqty,0)) * um_qty) as ordered_qty
     from po_tran 
     GROUP BY
     entry_no,
     item_code 
),
grn_po as (SELECT grn.*,
     po.ordered_qty
     from grn INNER JOIN po
     on grn.po_no = po.entry_no
     and grn.item_code = po.item_code 
)


SELECT po_no,
    
     supp_code,
     item_code,

     COUNT(tran_no) as times_entered ,
     --MIN(tran_no) as first_grn ,
    -- max(tran_no) as last_grn,
     min(ordered_qty) as ordered_qty,
     sum(received_qty) as tota_received_qty

     --COUNT(tran_no) as times_entered 
       from grn_po
     -- group by 
   --   po_no,
    --  supp_code,
   --   item_code
    --  where received_qty > ordered_qty
      group by
      po_no,
      supp_code,
      
      item_code
      having sum(received_qty) > min(ordered_qty)
      and COUNT(tran_no) > 1


