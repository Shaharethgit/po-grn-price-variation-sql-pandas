# PO, GRN and Price Variation Analysis using SQL and Python

**PO = Purchase Order, GRN = Goods Receipt Note**

SQL and pandas analysis of purchase orders, goods receipts and price variations to find receiving errors, cost price changes, negative margins and supplier delays.

## Dataset
- Data: anonymized data based on a hypermarket purchase and inventory system.
- The repository contains queries, scripts and result screenshots only, no data files.
- Database: SQL Server
- Tools: SQL and Python (pandas)

## Key assumptions
- All quantities are converted to **base units** using the pack conversion (`um_units`), so cartons and pieces compare correctly.
- Free quantity (FOC) is included on both the PO and GRN sides.

**Logic:**
- Ordered qty = (PO qty + free qty) x pack units
- Received qty = GRN qty x pack units + FOC qty
- All GRNs of a PO are added together, so partial deliveries are compared correctly

## 01. GRN received more or less than PO qty

**Business impact:** Flags over-receipts (overpayment risk) and short receipts (stock-outs, supplier fill problems).


## Schema diagram

```mermaid
erDiagram
    grn_head ||--|{ grn_tran : "grn_no = tran_no"
    grn_head }o--o{ po_tran : "po_no = entry_no"
    grn_tran }o--o{ po_tran : "item_code (with po_no = entry_no)"
    um_master ||--o{ grn_tran : "item_code + pack_id"

    grn_head {
        varchar grn_no PK
        varchar po_no
    }
    grn_tran {
        varchar tran_no FK
        varchar item_code
        varchar pack_id
        decimal grn_qty
        decimal foc_qty
    }
    po_tran {
        varchar entry_no
        varchar item_code
        decimal po_qty
        decimal fqty
        decimal um_qty
    }
    um_master {
        varchar item_code
        varchar pack_id
        decimal um_units
    }
```
Only the tables and columns used by "GRN received more or less than PO qty" are shown.
---


### SQL

**Query:** [01_grn_qty_mismatch.sql](queries/01_grn_qty_mismatch.sql)

**Result:**

![GRN qty mismatch SQL result](results/01_grn_qty_mismatch.png)

### pandas

**Script:** [01_grn_qty_mismatch.py](pandas/01_grn_qty_mismatch.py)

**Result:**

![GRN qty mismatch pandas result](results/01_grn_qty_mismatch_pandas.png)

Top 15 rows shown, sorted by largest difference. Total: 16,632 PO-item rows compared. The pandas result matches the SQL result (same row count and same Exact, Short and Over counts).


---

## 02. POs with no GRN (pending)

**Business impact:** Shows orders placed but never received, so buyers can chase suppliers.

**Tables used:**

```mermaid
erDiagram
    po_head ||--o{ grn_head : "entry_no = po_no"

    po_head {
        varchar entry_no
    }
    grn_head {
        varchar grn_no
        varchar po_no
    }
```

Only the tables and columns used by "POs with no GRN (pending)" are shown.

### SQL

**Query:** [02_pending_po.sql](queries/02_po_with_no_grn.sql)

**Result:**

![Pending PO SQL result](results/02_pending_po.png)

### pandas

**Script:** [02_pending_po.py](pandas/02_pending_po.py)

**Result:**

![Pending PO pandas result](results/02_pending_po_pandas.png)

Top 10 rows shown. Total pending POs: 86. SQL and pandas counts match.

## 03. Same GRN entered twice

**Business impact:** Duplicate entries inflate stock and purchase value and can cause double payment.

**Logic:**
- Each item is totalled per GRN in base units: received qty = GRN qty x pack units + FOC qty
- Ordered qty = (PO qty + free qty) x pack units
- A PO item is flagged when it is received in **more than one GRN** and the **total received is more than the PO quantity**

**Tables used:**

```mermaid
erDiagram
    grn_head ||--|{ grn_tran : "grn_no = tran_no"
    um_master ||--o{ grn_tran : "item_code + pack_id"
    grn_head }o--o{ po_tran : "po_no = entry_no"
    grn_tran }o--o{ po_tran : "item_code"

    grn_head {
        varchar grn_no
        varchar po_no
        varchar supp_code
    }
    grn_tran {
        varchar tran_no
        varchar item_code
        varchar pack_id
        decimal grn_qty
        decimal foc_qty
    }
    um_master {
        varchar item_code
        varchar pack_id
        decimal um_units
    }
    po_tran {
        varchar entry_no
        varchar item_code
        decimal po_qty
        decimal fqty
        decimal um_qty
    }
```

Only the tables and columns used by "Same GRN entered twice" are shown.

### SQL

**Query:** [03_duplicate_grn.sql](queries/03_duplicate_grn.sql)

**Result:**

![Duplicate GRN SQL result](results/03_duplicate_grn.png)

### pandas

**Script:** [03_duplicate_grn.py](pandas/03_duplicate_grn.py)

**Result:**

![Duplicate GRN pandas result](results/03_duplicate_grn_pandas.png)

**Finding:** 1 PO with 2 items was received twice, so the total received was exactly double the ordered quantity.