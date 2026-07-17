# Business Requirements Document (BRD)
## Healthcare Claims Reference Data Quality & Analytics Platform

| | |
|---|---|
| **Document Owner** | Data Analytics / Reference Data Team |
| **Status** | Approved — v1.0 |
| **Data Classification** | Synthetic only — no PHI, no PII |

---

## 1. Purpose

Define the business requirements for a platform that validates healthcare
claims against reference data (diagnosis codes, procedure codes, providers,
insurance plans), identifies data quality issues, and produces business
reporting for claims operations, finance, and network management
stakeholders.

## 2. Business Problem Statement

A healthcare organization processes thousands of claims per month. Each claim
references several reference datasets — diagnosis (ICD-10) codes, procedure
(CPT) codes, provider records, and insurance plan records. When claims data
is dirty (missing codes, invalid codes, unrecognized providers, duplicate
submissions, impossible dates or amounts), it directly corrupts downstream
reporting, reimbursement calculations, and compliance reporting.

There is currently no automated, auditable process for:
- Validating incoming claims against reference data before they are trusted
- Quantifying and categorizing data quality issues
- Producing consistent, repeatable business KPIs from only the validated
  subset of claims

## 3. Business Objectives

| # | Objective |
|---|---|
| O1 | Validate every incoming claim against 10 defined data-quality rules |
| O2 | Produce a Data Quality Report quantifying issues by type, with examples |
| O3 | Maintain a normalized, referentially-intact claims database in MySQL |
| O4 | Deliver a repeatable business KPI/reporting suite (Python + SQL) |
| O5 | Ensure zero PHI/PII is used or generated anywhere in the platform |

## 4. Stakeholders

| Stakeholder | Interest |
|---|---|
| Claims Operations | Needs a queue of flagged claims to investigate/correct |
| Data/Reference Data Team | Owns ICD/CPT/provider/plan reference tables and their accuracy |
| Finance / Actuarial | Needs trustworthy claim amount totals and trend data |
| Network Management | Needs provider-level volume, approval rate, and geographic reporting |
| Compliance | Needs an auditable record of what was validated and why a claim was excluded |

## 5. Scope

### 5.1 In Scope

- Synthetic claims, patient, provider, insurance plan, ICD, and CPT datasets
  (10,000+ claim scale)
- Python/Pandas data cleaning and 10-rule data quality validation
- Data Quality Report generation (counts, percentages, example claim IDs)
- Normalized MySQL schema with PKs, FKs, constraints, indexes, and views
- 25 SQL business queries covering joins, CTEs, window functions,
  aggregation, ranking, and running totals
- Business KPI suite: claim volume, approval/rejection/pending rates,
  claims by month/provider/plan/state, top ICD/CPT codes

### 5.2 Out of Scope

- Real patient, provider, or claims data of any kind
- Machine learning / predictive fraud scoring
- BI tool integration (Tableau, Power BI, Excel dashboards)
- Real-time/streaming ingestion — this is a batch pipeline
- Claims adjudication logic (this platform validates and reports; it does
  not decide reimbursement amounts)

## 6. Functional Requirements

| ID | Requirement |
|---|---|
| FR1 | System shall generate synthetic reference and claims data with a fixed random seed for reproducibility |
| FR2 | System shall validate each claim's ICD code against the ICD reference table |
| FR3 | System shall validate each claim's CPT code against the CPT reference table |
| FR4 | System shall validate each claim's provider_id against the Providers table |
| FR5 | System shall detect claims with a missing insurance plan |
| FR6 | System shall detect claims with a claim_date in the future |
| FR7 | System shall detect claims with a negative claim_amount |
| FR8 | System shall detect claims with a claim_status outside the allowed set (Approved, Rejected, Pending) |
| FR9 | System shall detect duplicate claim submissions (same business content, different claim_id) |
| FR10 | System shall export a Data Quality Report summarizing every rule violation with counts and examples |
| FR11 | System shall export only fully-valid claims to the load-ready dataset used for MySQL and KPI reporting |
| FR12 | System shall enforce referential integrity in MySQL via foreign key constraints |
| FR13 | System shall provide at least 20 business SQL queries covering joins, CTEs, window functions, and aggregation |

## 7. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR1 | No PHI or PII shall be present anywhere in the dataset or codebase |
| NFR2 | All data generation shall be reproducible via a fixed random seed |
| NFR3 | Python code shall follow PEP 8 and include docstrings/comments explaining business logic |
| NFR4 | SQL schema shall use appropriately typed columns (VARCHAR for codes/IDs, never numeric types that could truncate leading zeros) |
| NFR5 | The platform shall run entirely on Python, Pandas, MySQL, and SQL — no BI tools, no ML/DL frameworks |
| NFR6 | Cleaning (technical fixes) and validation (business rules) shall be implemented as clearly separate steps |

## 8. Success Criteria

- 100% of the 10 defined data quality rules are implemented and independently
  verifiable
- The MySQL schema loads the validated dataset with **zero foreign key
  violations**
- At least 20 business SQL queries execute successfully against the loaded
  database
- All business KPIs listed in scope are computable from the validated dataset
- Full documentation (README, BRD, Data Dictionary) exists and matches the
  delivered code exactly

## 9. Assumptions

- "Business day" claim volume patterns are approximated with a random
  distribution across each month rather than modeling real seasonal claim
  intake patterns
- ICD-10 and CPT reference codes used are a representative public sample,
  not the complete official code sets
- A claim is considered "duplicate" if it shares identical patient, provider,
  plan, diagnosis, procedure, date, and amount — real-world duplicate
  detection may use fuzzier matching

## 10. Constraints

- No real or identifiable healthcare data may be used at any point
- No BI, ML, or deep learning tooling may be used, per project requirements
- All work must be reproducible from Python scripts, notebooks, and SQL
  files checked into the repository

## 11. Risks

| Risk | Mitigation |
|---|---|
| Synthetic data patterns may not reflect real claims distributions | Reference codes and plan types are drawn from real, publicly documented ICD-10/CPT/plan-type structures |
| Leading-zero code corruption during CSV/MySQL load | All ID/code columns are explicitly typed as VARCHAR/str throughout the pipeline |
| Silent data loss during cleaning | Cleaning and validation are kept as separate steps; flagged claims are exported, never deleted |
