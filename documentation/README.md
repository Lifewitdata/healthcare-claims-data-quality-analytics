<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=26&duration=2800&pause=1200&color=2E9EF7&center=true&vCenter=true&width=800&lines=Healthcare+Claims+Reference+Data;Quality+%26+Analytics+Platform;Python+%2B+Pandas+%2B+MySQL+%2B+SQL;10%2C060+Synthetic+Claims+%7C+Zero+PHI%2FPII" alt="Typing SVG" />

<br/>

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.x-150458?style=for-the-badge&logo=pandas&logoColor=white)
![Jupyter](https://img.shields.io/badge/Jupyter-Notebook-F37626?style=for-the-badge&logo=jupyter&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=120&section=header" width="100%"/>

</div>

## What is this?

A **production-style, end-to-end healthcare claims analytics platform** built to
mirror the daily work of a Healthcare Data Analyst on a claims/reference-data
team — validating diagnosis (ICD) and procedure (CPT) codes, catching data
quality problems before they hit a report, and turning 10,000+ raw claims
into trustworthy business KPIs.

**100% synthetic data. Zero PHI. Zero PII.** Every patient record is anonymous
(surrogate ID + age band + gender + state only) — nothing that could identify
a real person, on purpose.

> Built as a portfolio project for healthcare data analyst / claims data
> engineering roles (e.g. Gainwell-style reference data + claims analytics
> work) using **only** Python, Pandas, MySQL, SQL, and Jupyter — no BI tools,
> no ML.

<img src="https://capsule-render.vercel.app/api?type=rect&color=gradient&customColorList=6,11,20&height=3&width=100%"/>

## Table of Contents

- [Architecture](#architecture)
- [The Pipeline in Numbers](#the-pipeline-in-numbers)
- [Business Problem](#business-problem)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Data Quality Engine](#data-quality-engine)
- [Database Design](#database-design)
- [SQL Analytics — 25 Business Queries](#sql-analytics--25-business-queries)
- [Sample Insights](#sample-insights)
- [How to Run It](#how-to-run-it)
- [Documentation](#documentation)
- [Future Improvements](#future-improvements)
- [Author](#author)

<img src="https://capsule-render.vercel.app/api?type=rect&color=gradient&customColorList=6,11,20&height=3&width=100%"/>

## Architecture

```mermaid
flowchart LR
    A[("Synthetic Data\nGenerator\ngenerate_data.py")] --> B[/"Raw CSVs\ndata/raw/"/]
    B --> C{{"Notebook 1\nCleaning + 10 DQ Rules"}}
    C -->|"valid claims"| D[/"data/cleaned/\nclaims_valid.csv"/]
    C -->|"flagged claims"| E[/"outputs/\ndata_quality_report.csv"/]
    D --> F[("MySQL\nhealthcare_claims")]
    F --> G["25 Business SQL Queries\njoins · CTEs · window fns"]
    D --> H["Notebook 2\nPandas KPI Reporting"]
    G --> I(["Business Insights"])
    H --> I

    style A fill:#2E9EF7,color:#fff
    style F fill:#4479A1,color:#fff
    style I fill:#2ea44f,color:#fff
```

The pipeline is **deliberately split into two independent tracks**:

| Track | Tooling | Responsibility |
|---|---|---|
| 🐍 **Python track** | Pandas, Jupyter | Generate → clean → validate → flag → export |
| 🗄️ **SQL track** | MySQL | Schema → load → 25 business queries |

Python never queries MySQL and MySQL never runs Python — each track stands
on its own and is independently reviewable.

<img src="https://capsule-render.vercel.app/api?type=rect&color=gradient&customColorList=6,11,20&height=3&width=100%"/>

## The Pipeline in Numbers

<div align="center">

| Metric | Value |
|---|---|
| 📄 Raw claims generated | **10,060** |
| ✅ Claims passing all 10 DQ rules | **9,460** (94%) |
| 🚩 Claims flagged for review | **600** (6%, 60 per rule) |
| 🏥 Providers | **300** |
| 🙍 Patients (anonymous) | **2,500** |
| 💳 Insurance plans | **15** |
| 🩺 ICD-10 diagnosis codes | **150** |
| 🔬 CPT procedure codes | **113** |
| 💰 Total validated claim amount | **$3,672,696.57** |
| 📈 Overall approval rate | **61.97%** |
| 🗓️ Claim date range | **Jan 2023 – Dec 2025** |
| 🧮 Business SQL queries | **25** |

</div>

<img src="https://capsule-render.vercel.app/api?type=rect&color=gradient&customColorList=6,11,20&height=3&width=100%"/>

## Business Problem

A healthcare payer receives thousands of claims every month. Before any claim
can be trusted for reporting, reimbursement analysis, or compliance, it has to
survive a gauntlet of reference-data checks: is the diagnosis code real? Is
the procedure code real? Is the billing provider actually in network? Was
this claim already submitted once before?

This project builds that gauntlet — and then builds the reporting layer on
top of the claims that pass it.

Full requirements are documented in [`documentation/BRD.md`](BRD.md).

<img src="https://capsule-render.vercel.app/api?type=rect&color=gradient&customColorList=6,11,20&height=3&width=100%"/>

## Tech Stack

<div align="center">

![Python](https://img.shields.io/badge/-Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/-Pandas-150458?style=flat-square&logo=pandas&logoColor=white)
![NumPy](https://img.shields.io/badge/-NumPy-013243?style=flat-square&logo=numpy&logoColor=white)
![MySQL](https://img.shields.io/badge/-MySQL-4479A1?style=flat-square&logo=mysql&logoColor=white)
![Jupyter](https://img.shields.io/badge/-Jupyter-F37626?style=flat-square&logo=jupyter&logoColor=white)
![Git](https://img.shields.io/badge/-Git-F05032?style=flat-square&logo=git&logoColor=white)

</div>

<img src="https://capsule-render.vercel.app/api?type=rect&color=gradient&customColorList=6,11,20&height=3&width=100%"/>

## Project Structure

```
Healthcare-Claims-Analytics/
│
├── data/
│   ├── raw/                     # 6 generated CSVs (10,060 claims + dimensions)
│   └── cleaned/                 # load-ready: claims_valid.csv, claims_flagged.csv, dims
│
├── database/
│   ├── schema.sql                # tables, PKs, FKs, constraints, indexes, 2 views
│   └── load_data.sql             # LOAD DATA, FK-safe order
│
├── sql/
│   └── business_queries.sql      # 25 queries: joins, CTEs, window fns, ranking
│
├── python/
│   └── generate_data.py          # synthetic data generator (seeded, reproducible)
│
├── notebooks/
│   ├── 01_data_cleaning_and_validation.ipynb
│   └── 02_kpi_business_reporting.ipynb
│
├── outputs/
│   ├── data_quality_report.csv
│   └── kpi_summary.csv
│
├── documentation/
│   ├── README.md
│   ├── BRD.md
│   └── Data_Dictionary.md
│
├── screenshots/
├── requirements.txt
└── README.md
```

<img src="https://capsule-render.vercel.app/api?type=rect&color=gradient&customColorList=6,11,20&height=3&width=100%"/>

## Data Quality Engine

Ten independent business rules run against every claim. A claim can fail more
than one rule at once — nothing is silently dropped, everything is flagged
and reported.

<div align="center">

| # | Rule | Claims Flagged |
|---|---|:---:|
| 1 | Missing ICD code | 60 |
| 2 | Missing CPT code | 60 |
| 3 | Invalid ICD code (not in reference table) | 60 |
| 4 | Invalid CPT code (not in reference table) | 60 |
| 5 | Invalid provider ID | 60 |
| 6 | Missing insurance plan | 60 |
| 7 | Future-dated claim | 60 |
| 8 | Negative claim amount | 60 |
| 9 | Invalid claim status | 60 |
| 10 | Duplicate claim submission | 60 |

</div>

> Design principle: **cleaning ≠ validation.** Cleaning fixes technical
> formatting (whitespace, dtypes, exact duplicate rows). Validation applies
> business rules and *reports* violations — a real claims ops team needs to
> see the problem, not have it disappear.

<img src="https://capsule-render.vercel.app/api?type=rect&color=gradient&customColorList=6,11,20&height=3&width=100%"/>

## Database Design

```mermaid
erDiagram
    PATIENTS ||--o{ CLAIMS : files
    PROVIDERS ||--o{ CLAIMS : bills
    INSURANCE_PLANS ||--o{ CLAIMS : covers
    ICD_CODES ||--o{ CLAIMS : diagnoses
    CPT_CODES ||--o{ CLAIMS : procedures

    PATIENTS {
        varchar patient_id PK
        varchar age_band
        char gender
        char state
    }
    PROVIDERS {
        varchar provider_id PK
        varchar npi UK
        varchar provider_name
        varchar specialty
        char state
    }
    INSURANCE_PLANS {
        varchar plan_id PK
        varchar plan_name
        varchar plan_type
    }
    ICD_CODES {
        varchar icd_code PK
        varchar icd_description
    }
    CPT_CODES {
        varchar cpt_code PK
        varchar cpt_description
    }
    CLAIMS {
        varchar claim_id PK
        varchar patient_id FK
        varchar provider_id FK
        varchar plan_id FK
        varchar icd_code FK
        varchar cpt_code FK
        date claim_date
        decimal claim_amount
        varchar claim_status
    }
```

Full column-level definitions live in
[`documentation/Data_Dictionary.md`](Data_Dictionary.md).

<img src="https://capsule-render.vercel.app/api?type=rect&color=gradient&customColorList=6,11,20&height=3&width=100%"/>

## SQL Analytics — 25 Business Queries

`sql/business_queries.sql` is organized into 7 sections, run against the
loaded MySQL database:

1. **Core volume & status KPIs** — totals, approval/rejection/pending rates
2. **Time-based reporting** — monthly trend, running totals (`SUM() OVER`), MoM % change (`LAG()`)
3. **Provider analysis** — top billers, `RANK()` within specialty, CTE-based underperformer detection
4. **Insurance plan analysis** — volume/cost by plan, `DENSE_RANK()` by exposure
5. **ICD/CPT analysis** — top diagnoses & procedures, `ROW_NUMBER()` for top procedures per diagnosis
6. **Patient/geographic analysis** — claims by state, age/gender utilization, top-cost patients
7. **Advanced analytics** — outlier detection (`AVG() OVER PARTITION BY`), `NTILE(4)` provider quartiles

Every query has been executed end-to-end against the live 9,460-row loaded
database — see `sql/business_queries_sample_output.txt` for real output.

<img src="https://capsule-render.vercel.app/api?type=rect&color=gradient&customColorList=6,11,20&height=3&width=100%"/>

## Sample Insights

- Overall approval rate is **61.97%**, with rejection (18.41%) and pending
  (19.62%) roughly split — a healthy, realistic claims funnel.
- The highest-billed specialties cluster around **Cardiology, Dermatology,
  and Orthopedics**, consistent with real-world claim cost patterns.
- Outlier detection (claim amount vs. average for its own CPT code) surfaces
  claims billed **3–4x higher** than the typical cost of the same procedure
  — exactly the kind of signal a claims examiner would want surfaced
  automatically.
- Monthly claim volume is stable in the **230–310 claims/month** range across
  all three years of synthetic data, with no unexplained spikes — confirming
  the DQ layer is filtering noise rather than real business signal.

<img src="https://capsule-render.vercel.app/api?type=rect&color=gradient&customColorList=6,11,20&height=3&width=100%"/>

## How to Run It

```bash
# 1. Clone
git clone https://github.com/<your-username>/Healthcare-Claims-Analytics.git
cd Healthcare-Claims-Analytics

# 2. Install dependencies
pip install -r requirements.txt

# 3. Generate synthetic data
cd python && python generate_data.py

# 4. Run the cleaning & validation notebook
jupyter notebook notebooks/01_data_cleaning_and_validation.ipynb

# 5. Build the MySQL database
mysql -u root -p < database/schema.sql
mysql -u root -p --local-infile=1 < database/load_data.sql

# 6. Run the business analytics
mysql -u root -p healthcare_claims < sql/business_queries.sql
```

<img src="https://capsule-render.vercel.app/api?type=rect&color=gradient&customColorList=6,11,20&height=3&width=100%"/>

## Documentation

| Document | Contents |
|---|---|
| [`BRD.md`](BRD.md) | Business Requirements Document — objectives, scope, stakeholders, success criteria |
| [`Data_Dictionary.md`](Data_Dictionary.md) | Every table, every column, every constraint, with examples |
| This README | Architecture, pipeline, and how to run it |

## Future Improvements

- [ ] Add a fraud/anomaly scoring layer on top of the outlier-detection query
- [ ] Parameterize the SQL queries into a lightweight Python reporting CLI
- [ ] Add automated pytest coverage for each DQ rule function
- [ ] Containerize the MySQL schema + load step with Docker Compose
- [ ] Add incremental/delta loading instead of full reload

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=100&section=footer" width="100%"/>

<div align="center">

**Built as a healthcare data analytics portfolio project — 100% synthetic data, zero PHI/PII.**

</div>
