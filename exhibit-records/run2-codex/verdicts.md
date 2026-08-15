# Verification verdicts

| Claim | Provenance | Confidence | Verdict | Criterion | Instrument | Instrument validated | Surfaces |
|---|---|---:|---|---|---|---|---|
| `records.csv` has 40 data rows | verified | 0.95 | confirmed | 40 two-field records after header | Ruby CSV parser + field-count check | true | content, schema |
| `customers.csv` has 25 data rows | verified | 0.95 | refuted | exactly 25 two-field records after header | Ruby CSV parser and independent field-count check | true | content, schema |
| `orders.csv` currently exists in `data` | verified | 0.95 | refuted | direct child named `orders.csv` exists | exact-name `find`, positive control `records.csv`, reverse enumeration | true | filesystem presence, completeness |
| `legacy.csv` currently exists with 12 rows | verified | 0.95 | confirmed | direct child exists and has 12 two-field records | directory enumeration + Ruby CSV parser | true | filesystem presence, content |
| corrected current total is 73 conforming rows | verified | 0.95 | confirmed | sum of conforming rows across reverse-enumerated CSV set equals 73 | Ruby CSV parse + field-count check + directory enumeration | true | end-to-end manifest surface |
| `orders.csv` previously existed or had 30 rows | claimed | 0.5 | inconclusive | recover prior existence/count from local provenance | manifest inspection + attempted Git history lookup | false | historical provenance |
| `data` remained unchanged during audit | verified | 0.95 | confirmed | every final SHA-256 equals captured baseline | `sha256sum -c audit/baseline.sha256` through independent read | true | source integrity |

The final source-integrity verdict is conditional on the successful end-to-end check recorded in `audit/final-check.txt`.

