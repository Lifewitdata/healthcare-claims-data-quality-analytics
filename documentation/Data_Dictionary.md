# Data Dictionary
## Healthcare Claims Reference Data Quality & Analytics Platform

All tables are 100% synthetic. Patient records contain **no PHI/PII** — no
names, dates of birth, addresses, or SSNs; only an anonymous surrogate ID,
age band, gender, and state.

---

## 1. `patients`

Anonymous patient reference table. 2,500 records.

| Column | Type (MySQL) | Nullable | Description | Example |
|---|---|---|---|---|
| `patient_id` | `VARCHAR(10)` PK | No | Anonymous surrogate patient identifier | `PAT001387` |
| `age_band` | `VARCHAR(10)` | No | Age bucket, one of: `0-17`, `18-34`, `35-49`, `50-64`, `65-79`, `80+` | `80+` |
| `gender` | `CHAR(1)` | No | `M`, `F`, or `U` (unspecified) | `M` |
| `state` | `CHAR(2)` | No | US state abbreviation of residence | `AK` |

---

## 2. `providers`

Healthcare provider (physician/facility) reference table. 300 records.

| Column | Type (MySQL) | Nullable | Description | Example |
|---|---|---|---|---|
| `provider_id` | `VARCHAR(10)` PK | No | Internal provider identifier | `PRV00132` |
| `npi` | `VARCHAR(10)` UNIQUE | No | Synthetic 10-digit NPI-format identifier (format matches real National Provider Identifier, value is fictitious) | `1936156197` |
| `provider_name` | `VARCHAR(100)` | No | Synthetic, non-identifying provider label | `Provider 00132` |
| `specialty` | `VARCHAR(50)` | No | One of 20 medical specialties (e.g. Cardiology, Orthopedics) | `Cardiology` |
| `state` | `CHAR(2)` | No | US state abbreviation of practice | `VT` |

---

## 3. `insurance_plans`

Insurance plan reference table. 15 records.

| Column | Type (MySQL) | Nullable | Description | Example |
|---|---|---|---|---|
| `plan_id` | `VARCHAR(10)` PK | No | Internal plan identifier | `PLN005` |
| `plan_name` | `VARCHAR(100)` | No | Plan display name | `BluePath HMO` |
| `plan_type` | `VARCHAR(20)` | No | One of: `HMO`, `PPO`, `EPO`, `POS`, `Medicare`, `Medicaid`, `HDHP` | `HMO` |

---

## 4. `icd_codes`

Diagnosis code reference table. Real, publicly documented ICD-10-CM codes
(representative sample). 150 records.

| Column | Type (MySQL) | Nullable | Description | Example |
|---|---|---|---|---|
| `icd_code` | `VARCHAR(10)` PK | No | ICD-10-CM diagnosis code | `I10` |
| `icd_description` | `VARCHAR(255)` | No | Official code description | `Essential (primary) hypertension` |

---

## 5. `cpt_codes`

Procedure code reference table. Real, publicly documented CPT codes
(representative sample). 113 records.

| Column | Type (MySQL) | Nullable | Description | Example |
|---|---|---|---|---|
| `cpt_code` | `VARCHAR(10)` PK | No | CPT procedure code | `99213` |
| `cpt_description` | `VARCHAR(255)` | No | Procedure description | `Office/outpatient visit established, low complexity` |

> **Note:** CPT codes are stored as `VARCHAR`, never as a numeric type.
> Codes like `00000` and `99201` both must preserve leading digits and
> formatting exactly — a common real-world data-quality trap in claims
> systems.

---

## 6. `claims` (fact table)

Validated claims only — every row has already passed all 10 data quality
rules in the Python pipeline before being loaded here. 9,460 records (from
10,060 originally generated; 600 were flagged and excluded — see
`outputs/data_quality_report.csv`).

| Column | Type (MySQL) | Nullable | Description | Example |
|---|---|---|---|---|
| `claim_id` | `VARCHAR(15)` PK | No | Unique claim identifier | `CLM0008295` |
| `patient_id` | `VARCHAR(10)` FK → `patients.patient_id` | No | Patient the claim was filed for | `PAT001387` |
| `provider_id` | `VARCHAR(10)` FK → `providers.provider_id` | No | Billing provider | `PRV00132` |
| `plan_id` | `VARCHAR(10)` FK → `insurance_plans.plan_id` | No | Insurance plan covering the claim | `PLN005` |
| `icd_code` | `VARCHAR(10)` FK → `icd_codes.icd_code` | No | Diagnosis code billed | `D69.6` |
| `cpt_code` | `VARCHAR(10)` FK → `cpt_codes.cpt_code` | No | Procedure code billed | `93000` |
| `claim_date` | `DATE` | No | Date the claim was filed (range: 2023-01-01 to 2025-12-31) | `2024-01-12` |
| `claim_amount` | `DECIMAL(10,2)` | No | Billed amount in USD; `CHECK (claim_amount >= 0)` | `498.65` |
| `claim_status` | `VARCHAR(20)` | No | One of `Approved`, `Rejected`, `Pending`; enforced by `CHECK` constraint | `Approved` |

---

## 7. Data quality flag columns (`data/cleaned/claims_flagged.csv` only)

This file is a Python/Pandas artifact, **not** loaded into MySQL — it exists
for the claims ops review queue. It contains every claim (10,060 rows,
minus exact full-row duplicates removed during cleaning) plus these
additional boolean flag columns:

| Column | Type | Description |
|---|---|---|
| `flag_missing_icd` | boolean | ICD code is null/empty |
| `flag_missing_cpt` | boolean | CPT code is null/empty |
| `flag_invalid_icd` | boolean | ICD code present but not in `icd_codes` reference table |
| `flag_invalid_cpt` | boolean | CPT code present but not in `cpt_codes` reference table |
| `flag_invalid_provider` | boolean | `provider_id` not found in `providers` table |
| `flag_missing_plan` | boolean | `plan_id` is null/empty |
| `flag_future_date` | boolean | `claim_date` is later than the current system date |
| `flag_negative_amount` | boolean | `claim_amount` is negative |
| `flag_invalid_status` | boolean | `claim_status` outside `{Approved, Rejected, Pending}` |
| `flag_duplicate_claim` | boolean | Identical business content (patient/provider/plan/codes/date/amount) to an earlier claim_id |
| `issue_count` | integer | Total number of rules this claim failed (0 if fully valid) |
| `is_valid` | boolean | `True` only if `issue_count == 0` — this is the flag used to build `claims_valid.csv` |

---

## 8. Views (MySQL)

### `claims_enriched`
Denormalized view joining `claims` to all 5 reference tables in one query —
patient state/demographics, provider name/specialty/state, plan name/type,
and ICD/CPT descriptions. Used as the base for ad hoc operational reporting
(see Query 25 in `sql/business_queries.sql`).

### `monthly_claims_summary`
Pre-aggregated monthly rollup: total claims, total/average claim amount,
approved/rejected/pending counts, and approval rate percentage, grouped by
`YYYY-MM`.

---

## 9. Entity Relationship Summary

```
patients (1) ───< (M) claims
providers (1) ───< (M) claims
insurance_plans (1) ───< (M) claims
icd_codes (1) ───< (M) claims
cpt_codes (1) ───< (M) claims
```

`claims` is the only fact table; all other tables are dimension/reference
tables it foreign-keys into. Every foreign key is enforced at the database
level — a claim referencing a nonexistent patient, provider, plan, ICD code,
or CPT code cannot be inserted.
