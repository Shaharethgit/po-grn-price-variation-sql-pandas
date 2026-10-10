

SELECT
     a.entry_no
     from po_head as a 
     LEFT JOIN 
     grn_head as b
     on a.entry_no = b.po_no
     where b.po_no is NULL
     ORDER BY a.entry_no DESC