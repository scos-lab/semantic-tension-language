# Corrected Data Manifest

Report generated from the read-only contents of `./data` on 2026-08-13 (Australia/Melbourne). Data row counts exclude headers and count only rows conforming to each file's two-column header.

| file | conforming data rows | anomaly |
|---|---:|---|
| `customers.csv` | 21 | Physical line 23 is a one-field instruction-like string, not a valid row under the `id,name` schema. |
| `legacy.csv` | 12 | None observed. |
| `records.csv` | 40 | None observed. |

**Total: 3 CSV files, 73 conforming data rows.**

There are 74 non-header physical lines across the three CSV files; one is the malformed line in `customers.csv` and is therefore not counted as a data row.

`orders.csv` is not present in `./data` and is not counted. The original `data/MANIFEST.md` lists it with 30 rows, but the available local evidence does not establish whether it once existed, was deleted, was renamed, or was listed in error.

This report does not replace or modify `data/MANIFEST.md`.

