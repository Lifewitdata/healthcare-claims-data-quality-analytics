-- =============================================================================
-- schema.sql
-- Healthcare Claims Reference Data Quality & Analytics Platform
-- =============================================================================
-- Business Purpose
-- -----------------
-- This script creates a normalized relational schema for storing validated
-- healthcare claims and their supporting reference data (patients, providers,
-- insurance plans, ICD diagnosis codes, CPT procedure codes).
--
-- Design choices, and why they fit a healthcare analytics environment:
--   1. Reference tables (icd_codes, cpt_codes, insurance_plans, providers,
--      patients) are loaded FIRST and are the source of truth that the
--      claims fact table's foreign keys point to. This mirrors real claims
--      systems, where a claim can never reference a code/provider/plan that
--      doesn't already exist in the reference data.
--   2. All identifier/code columns are VARCHAR, never INT -- claim IDs,
--      provider IDs, ICD codes, and CPT codes all carry meaningful leading
--      zeros or alphanumeric formats (e.g. CPT "00000", ICD "A09") that
--      would be silently corrupted by a numeric type.
--   3. Foreign keys + constraints enforce referential integrity at the
--      DATABASE level, not just in application code -- critical for a
--      claims system where multiple pipelines may write to the database.
--   4. Indexes are added on columns used heavily in the business queries
--      (claim_date, claim_status, provider_id, plan_id) to keep the
--      30-query analytics workload fast at 10K+ claim scale.
--   5. Two views are provided as reusable building blocks for reporting.
-- =============================================================================

DROP DATABASE IF EXISTS healthcare_claims;
CREATE DATABASE healthcare_claims CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE healthcare_claims;

-- -----------------------------------------------------------------------------
-- Reference table: insurance_plans
-- -----------------------------------------------------------------------------
CREATE TABLE insurance_plans (
    plan_id      VARCHAR(10)  NOT NULL,
    plan_name    VARCHAR(100) NOT NULL,
    plan_type    VARCHAR(20)  NOT NULL,
    PRIMARY KEY (plan_id)
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- Reference table: providers
-- -----------------------------------------------------------------------------
CREATE TABLE providers (
    provider_id    VARCHAR(10)  NOT NULL,
    npi            VARCHAR(10)  NOT NULL,
    provider_name  VARCHAR(100) NOT NULL,
    specialty      VARCHAR(50)  NOT NULL,
    state          CHAR(2)      NOT NULL,
    PRIMARY KEY (provider_id),
    UNIQUE KEY uq_providers_npi (npi)
) ENGINE=InnoDB;

CREATE INDEX idx_providers_specialty ON providers (specialty);
CREATE INDEX idx_providers_state ON providers (state);

-- -----------------------------------------------------------------------------
-- Reference table: patients (anonymous only -- no PII/PHI)
-- -----------------------------------------------------------------------------
CREATE TABLE patients (
    patient_id  VARCHAR(10) NOT NULL,
    age_band    VARCHAR(10) NOT NULL,
    gender      CHAR(1)     NOT NULL,
    state       CHAR(2)     NOT NULL,
    PRIMARY KEY (patient_id)
) ENGINE=InnoDB;

CREATE INDEX idx_patients_state ON patients (state);

-- -----------------------------------------------------------------------------
-- Reference table: icd_codes (diagnosis codes)
-- -----------------------------------------------------------------------------
CREATE TABLE icd_codes (
    icd_code        VARCHAR(10)  NOT NULL,
    icd_description VARCHAR(255) NOT NULL,
    PRIMARY KEY (icd_code)
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- Reference table: cpt_codes (procedure codes)
-- -----------------------------------------------------------------------------
CREATE TABLE cpt_codes (
    cpt_code        VARCHAR(10)  NOT NULL,
    cpt_description VARCHAR(255) NOT NULL,
    PRIMARY KEY (cpt_code)
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- Fact table: claims
-- -----------------------------------------------------------------------------
-- Only VALIDATED claims (from claims_valid.csv, produced by the Python data
-- quality pipeline) are loaded here. This table is the trusted analytical
-- source -- every row is guaranteed to satisfy the 10 DQ rules already
-- applied upstream, so foreign keys here should never fail.
-- -----------------------------------------------------------------------------
CREATE TABLE claims (
    claim_id       VARCHAR(15)    NOT NULL,
    patient_id     VARCHAR(10)    NOT NULL,
    provider_id    VARCHAR(10)    NOT NULL,
    plan_id        VARCHAR(10)    NOT NULL,
    icd_code       VARCHAR(10)    NOT NULL,
    cpt_code       VARCHAR(10)    NOT NULL,
    claim_date     DATE           NOT NULL,
    claim_amount   DECIMAL(10,2)  NOT NULL,
    claim_status   VARCHAR(20)    NOT NULL,
    PRIMARY KEY (claim_id),
    CONSTRAINT fk_claims_patient
        FOREIGN KEY (patient_id) REFERENCES patients (patient_id),
    CONSTRAINT fk_claims_provider
        FOREIGN KEY (provider_id) REFERENCES providers (provider_id),
    CONSTRAINT fk_claims_plan
        FOREIGN KEY (plan_id) REFERENCES insurance_plans (plan_id),
    CONSTRAINT fk_claims_icd
        FOREIGN KEY (icd_code) REFERENCES icd_codes (icd_code),
    CONSTRAINT fk_claims_cpt
        FOREIGN KEY (cpt_code) REFERENCES cpt_codes (cpt_code),
    CONSTRAINT chk_claims_amount_nonnegative
        CHECK (claim_amount >= 0),
    CONSTRAINT chk_claims_status
        CHECK (claim_status IN ('Approved', 'Rejected', 'Pending'))
) ENGINE=InnoDB;

-- Indexes to support the analytics workload (date-range filters, grouping
-- by provider/plan/status, which appear repeatedly in the business queries)
CREATE INDEX idx_claims_date ON claims (claim_date);
CREATE INDEX idx_claims_status ON claims (claim_status);
CREATE INDEX idx_claims_provider ON claims (provider_id);
CREATE INDEX idx_claims_plan ON claims (plan_id);
CREATE INDEX idx_claims_patient ON claims (patient_id);
CREATE INDEX idx_claims_icd ON claims (icd_code);
CREATE INDEX idx_claims_cpt ON claims (cpt_code);

-- =============================================================================
-- Views
-- =============================================================================

-- View: claims_enriched
-- Business purpose: a single denormalized view joining claims to all of its
-- reference dimensions. Most business/reporting queries need patient state,
-- provider specialty, plan type, and code descriptions together -- this view
-- saves every analyst from re-writing the same 5-way join.
CREATE VIEW claims_enriched AS
SELECT
    c.claim_id,
    c.claim_date,
    c.claim_amount,
    c.claim_status,
    p.patient_id,
    p.age_band,
    p.gender      AS patient_gender,
    p.state       AS patient_state,
    pr.provider_id,
    pr.provider_name,
    pr.specialty  AS provider_specialty,
    pr.state      AS provider_state,
    ip.plan_id,
    ip.plan_name,
    ip.plan_type,
    c.icd_code,
    ic.icd_description,
    c.cpt_code,
    cc.cpt_description
FROM claims c
JOIN patients p        ON c.patient_id  = p.patient_id
JOIN providers pr       ON c.provider_id = pr.provider_id
JOIN insurance_plans ip ON c.plan_id     = ip.plan_id
JOIN icd_codes ic       ON c.icd_code    = ic.icd_code
JOIN cpt_codes cc       ON c.cpt_code    = cc.cpt_code;

-- View: monthly_claims_summary
-- Business purpose: pre-aggregated monthly rollup (claim volume, total and
-- average claim amount, approval rate) -- the numbers a monthly operations
-- or finance report pulls most often.
CREATE VIEW monthly_claims_summary AS
SELECT
    DATE_FORMAT(claim_date, '%Y-%m') AS claim_month,
    COUNT(*)                          AS total_claims,
    SUM(claim_amount)                 AS total_claim_amount,
    ROUND(AVG(claim_amount), 2)       AS avg_claim_amount,
    SUM(claim_status = 'Approved')    AS approved_claims,
    SUM(claim_status = 'Rejected')    AS rejected_claims,
    SUM(claim_status = 'Pending')     AS pending_claims,
    ROUND(SUM(claim_status = 'Approved') / COUNT(*) * 100, 2) AS approval_rate_pct
FROM claims
GROUP BY DATE_FORMAT(claim_date, '%Y-%m');

SELECT 'Schema created successfully.' AS status;
