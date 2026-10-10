
-- Problem: POs with no GRN (pending)
-- Business impact: Shows orders placed but never received, so buyers can chase suppliers
-- Logic: LEFT JOIN from PO header to GRN head on PO number;
--        keep POs where no GRN exists (IS NULL).

SELECT
     a.entry_no
     from po_head as a 
     LEFT JOIN 
     grn_head as b
     on a.entry_no = b.po_no
     where b.po_no is NULL
     ORDER BY a.entry_no DESC