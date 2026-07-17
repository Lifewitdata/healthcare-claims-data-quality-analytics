-- =============================================================================
-- load_data.sql
-- Loads the cleaned, validated CSVs (produced by the Python DQ pipeline)
-- into the MySQL schema, in foreign-key-safe order: reference tables first,
-- claims fact table last.
-- =============================================================================

USE healthcare_claims;

SET FOREIGN_KEY_CHECKS = 0;

LOAD DATA LOCAL INFILE 'Healthcare-Claims-Analytics/data/cleaned/insurance_plans.csv'
INTO TABLE insurance_plans
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(plan_id, plan_name, plan_type);

LOAD DATA LOCAL INFILE 'Healthcare-Claims-Analytics/data/cleaned/providers.csv'
INTO TABLE providers
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(provider_id, npi, provider_name, specialty, state);

LOAD DATA LOCAL INFILE 'Healthcare-Claims-Analytics/data/cleaned/patients.csv'
INTO TABLE patients
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(patient_id, age_band, gender, state);

LOAD DATA LOCAL INFILE 'Healthcare-Claims-Analytics/data/cleaned/icd_codes.csv'
INTO TABLE icd_codes
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(icd_code, icd_description);

LOAD DATA LOCAL INFILE 'Healthcare-Claims-Analytics/data/cleaned/cpt_codes.csv'
INTO TABLE cpt_codes
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(cpt_code, cpt_description);

LOAD DATA LOCAL INFILE 'Healthcare-Claims-Analytics/data/cleaned/claims_valid.csv'
INTO TABLE claims
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(claim_id, patient_id, provider_id, plan_id, icd_code, cpt_code, claim_date, claim_amount, claim_status);

SET FOREIGN_KEY_CHECKS = 1;

SELECT 'insurance_plans' AS table_name, COUNT(*) AS row_count FROM insurance_plans
UNION ALL SELECT 'providers', COUNT(*) FROM providers
UNION ALL SELECT 'patients', COUNT(*) FROM patients
UNION ALL SELECT 'icd_codes', COUNT(*) FROM icd_codes
UNION ALL SELECT 'cpt_codes', COUNT(*) FROM cpt_codes
UNION ALL SELECT 'claims', COUNT(*) FROM claims;
