-- =============================================================================
-- business_queries.sql
-- Healthcare Claims Reference Data Quality & Analytics Platform
-- 25 business SQL queries: joins, CTEs, window functions, aggregations,
-- ranking, running totals, and operational reporting.
-- Run against the `healthcare_claims` database after schema.sql + load_data.sql.
-- =============================================================================

USE healthcare_claims;


-- =============================================================================
-- SECTION 1: CORE VOLUME & STATUS KPIs
-- =============================================================================

-- Q1. Total claims, and claims broken out by status, with rates.
-- Business purpose: the single most-requested number in claims ops --
-- "how many claims came in, and what happened to them."
SELECT
    COUNT(*)                                                    AS total_claims,
    SUM(claim_status = 'Approved')                              AS approved_claims,
    SUM(claim_status = 'Rejected')                               AS rejected_claims,
    SUM(claim_status = 'Pending')                                AS pending_claims,
    ROUND(SUM(claim_status = 'Approved') / COUNT(*) * 100, 2)   AS approval_rate_pct,
    ROUND(SUM(claim_status = 'Rejected') / COUNT(*) * 100, 2)   AS rejection_rate_pct,
    ROUND(SUM(claim_status = 'Pending')  / COUNT(*) * 100, 2)   AS pending_rate_pct
FROM claims;


-- Q2. Average and total claim amount overall.
-- Business purpose: baseline financial exposure figures for finance/leadership.
SELECT
    COUNT(*)                     AS total_claims,
    ROUND(SUM(claim_amount), 2)  AS total_claim_amount,
    ROUND(AVG(claim_amount), 2)  AS avg_claim_amount,
    ROUND(MIN(claim_amount), 2)  AS min_claim_amount,
    ROUND(MAX(claim_amount), 2)  AS max_claim_amount
FROM claims;


-- Q3. Claim amount statistics broken out by claim_status.
-- Business purpose: are rejected claims systematically higher-value than
-- approved ones? A common early signal of fraud/abuse patterns.
SELECT
    claim_status,
    COUNT(*)                     AS claim_count,
    ROUND(SUM(claim_amount), 2)  AS total_amount,
    ROUND(AVG(claim_amount), 2)  AS avg_amount
FROM claims
GROUP BY claim_status
ORDER BY total_amount DESC;


-- =============================================================================
-- SECTION 2: TIME-BASED REPORTING
-- =============================================================================

-- Q4. Claims by month.
-- Business purpose: core operational trend line -- claim volume over time.
SELECT
    DATE_FORMAT(claim_date, '%Y-%m') AS claim_month,
    COUNT(*)                          AS total_claims,
    ROUND(SUM(claim_amount), 2)       AS total_amount
FROM claims
GROUP BY DATE_FORMAT(claim_date, '%Y-%m')
ORDER BY claim_month;


-- Q5. Month-over-month running total of claim volume and claim amount.
-- Business purpose: cumulative claims processed year-to-date, a standard
-- finance/ops reporting line, built with a window function running total.
SELECT
    claim_month,
    total_claims,
    total_amount,
    SUM(total_claims) OVER (ORDER BY claim_month) AS running_total_claims,
    ROUND(SUM(total_amount) OVER (ORDER BY claim_month), 2) AS running_total_amount
FROM (
    SELECT
        DATE_FORMAT(claim_date, '%Y-%m') AS claim_month,
        COUNT(*)                          AS total_claims,
        SUM(claim_amount)                 AS total_amount
    FROM claims
    GROUP BY DATE_FORMAT(claim_date, '%Y-%m')
) AS monthly
ORDER BY claim_month;


-- Q6. Month-over-month percentage change in claim volume.
-- Business purpose: flags unusual spikes/drops in intake volume, using
-- the LAG() window function to compare each month to the previous one.
SELECT
    claim_month,
    total_claims,
    LAG(total_claims) OVER (ORDER BY claim_month) AS prev_month_claims,
    ROUND(
        (total_claims - LAG(total_claims) OVER (ORDER BY claim_month))
        / LAG(total_claims) OVER (ORDER BY claim_month) * 100, 2
    ) AS pct_change_vs_prev_month
FROM (
    SELECT DATE_FORMAT(claim_date, '%Y-%m') AS claim_month, COUNT(*) AS total_claims
    FROM claims
    GROUP BY DATE_FORMAT(claim_date, '%Y-%m')
) AS monthly
ORDER BY claim_month;


-- Q7. Approval rate trend by month.
-- Business purpose: is claim quality/approval improving or degrading over time?
SELECT
    DATE_FORMAT(claim_date, '%Y-%m')                              AS claim_month,
    COUNT(*)                                                       AS total_claims,
    SUM(claim_status = 'Approved')                                 AS approved_claims,
    ROUND(SUM(claim_status = 'Approved') / COUNT(*) * 100, 2)      AS approval_rate_pct
FROM claims
GROUP BY DATE_FORMAT(claim_date, '%Y-%m')
ORDER BY claim_month;


-- =============================================================================
-- SECTION 3: PROVIDER ANALYSIS
-- =============================================================================

-- Q8. Claims and total billed amount by provider (top 15 by volume).
-- Business purpose: identify highest-volume providers for network management.
SELECT
    pr.provider_id,
    pr.provider_name,
    pr.specialty,
    COUNT(c.claim_id)            AS total_claims,
    ROUND(SUM(c.claim_amount),2) AS total_billed
FROM claims c
JOIN providers pr ON c.provider_id = pr.provider_id
GROUP BY pr.provider_id, pr.provider_name, pr.specialty
ORDER BY total_claims DESC
LIMIT 15;


-- Q9. Rank providers by total billed amount within their specialty.
-- Business purpose: "who is the top biller in each specialty" -- a classic
-- window-function ranking query (RANK() partitioned by specialty).
SELECT *
FROM (
    SELECT
        pr.specialty,
        pr.provider_id,
        pr.provider_name,
        ROUND(SUM(c.claim_amount), 2) AS total_billed,
        RANK() OVER (PARTITION BY pr.specialty ORDER BY SUM(c.claim_amount) DESC) AS specialty_rank
    FROM claims c
    JOIN providers pr ON c.provider_id = pr.provider_id
    GROUP BY pr.specialty, pr.provider_id, pr.provider_name
) ranked
WHERE specialty_rank <= 3
ORDER BY specialty, specialty_rank;


-- Q10. Claims by specialty, with approval rate.
-- Business purpose: are certain specialties seeing lower approval rates?
-- Useful for targeting coding/documentation training.
SELECT
    pr.specialty,
    COUNT(*)                                                  AS total_claims,
    SUM(c.claim_status = 'Approved')                          AS approved_claims,
    ROUND(SUM(c.claim_status = 'Approved') / COUNT(*) * 100, 2) AS approval_rate_pct
FROM claims c
JOIN providers pr ON c.provider_id = pr.provider_id
GROUP BY pr.specialty
ORDER BY approval_rate_pct ASC;


-- Q11. Providers with an approval rate below the overall average.
-- Business purpose: uses a CTE to compute the overall benchmark once, then
-- flags underperforming providers relative to it -- a common QA screen.
WITH overall_rate AS (
    SELECT SUM(claim_status = 'Approved') / COUNT(*) AS avg_approval_rate
    FROM claims
),
provider_rates AS (
    SELECT
        pr.provider_id,
        pr.provider_name,
        COUNT(*) AS total_claims,
        SUM(c.claim_status = 'Approved') / COUNT(*) AS provider_approval_rate
    FROM claims c
    JOIN providers pr ON c.provider_id = pr.provider_id
    GROUP BY pr.provider_id, pr.provider_name
    HAVING COUNT(*) >= 10   -- ignore very low-volume providers (noisy rates)
)
SELECT
    pv.provider_id,
    pv.provider_name,
    pv.total_claims,
    ROUND(pv.provider_approval_rate * 100, 2) AS provider_approval_rate_pct,
    ROUND(ov.avg_approval_rate * 100, 2)      AS overall_approval_rate_pct
FROM provider_rates pv
CROSS JOIN overall_rate ov
WHERE pv.provider_approval_rate < ov.avg_approval_rate
ORDER BY pv.provider_approval_rate ASC;


-- Q12. Providers by state, with claim volume and rejection rate.
-- Business purpose: geographic breakdown for regional network performance.
SELECT
    pr.state,
    COUNT(DISTINCT pr.provider_id)                              AS provider_count,
    COUNT(c.claim_id)                                            AS total_claims,
    ROUND(SUM(c.claim_status = 'Rejected') / COUNT(*) * 100, 2)  AS rejection_rate_pct
FROM claims c
JOIN providers pr ON c.provider_id = pr.provider_id
GROUP BY pr.state
ORDER BY total_claims DESC;


-- =============================================================================
-- SECTION 4: INSURANCE PLAN ANALYSIS
-- =============================================================================

-- Q13. Claims and total amount by insurance plan.
-- Business purpose: which plans drive the most claim volume/cost.
SELECT
    ip.plan_id,
    ip.plan_name,
    ip.plan_type,
    COUNT(c.claim_id)             AS total_claims,
    ROUND(SUM(c.claim_amount), 2) AS total_amount,
    ROUND(AVG(c.claim_amount), 2) AS avg_amount
FROM claims c
JOIN insurance_plans ip ON c.plan_id = ip.plan_id
GROUP BY ip.plan_id, ip.plan_name, ip.plan_type
ORDER BY total_claims DESC;


-- Q14. Approval rate by plan type (HMO, PPO, Medicare, etc.).
-- Business purpose: do certain plan types systematically approve/reject more?
SELECT
    ip.plan_type,
    COUNT(*)                                                     AS total_claims,
    ROUND(SUM(c.claim_status = 'Approved') / COUNT(*) * 100, 2)  AS approval_rate_pct,
    ROUND(SUM(c.claim_status = 'Rejected') / COUNT(*) * 100, 2)  AS rejection_rate_pct
FROM claims c
JOIN insurance_plans ip ON c.plan_id = ip.plan_id
GROUP BY ip.plan_type
ORDER BY approval_rate_pct DESC;


-- Q15. Rank insurance plans by total claim amount (with dense ranking).
-- Business purpose: leadership-level ranking of plans by financial exposure.
SELECT
    plan_name,
    plan_type,
    total_amount,
    DENSE_RANK() OVER (ORDER BY total_amount DESC) AS amount_rank
FROM (
    SELECT ip.plan_name, ip.plan_type, ROUND(SUM(c.claim_amount), 2) AS total_amount
    FROM claims c
    JOIN insurance_plans ip ON c.plan_id = ip.plan_id
    GROUP BY ip.plan_name, ip.plan_type
) plan_totals
ORDER BY amount_rank;


-- =============================================================================
-- SECTION 5: DIAGNOSIS (ICD) & PROCEDURE (CPT) ANALYSIS
-- =============================================================================

-- Q16. Top 10 diagnosis (ICD) codes by claim volume.
-- Business purpose: identifies the most common conditions being treated --
-- useful for care management and network resource planning.
SELECT
    ic.icd_code,
    ic.icd_description,
    COUNT(*)                      AS claim_count,
    ROUND(SUM(c.claim_amount), 2) AS total_amount
FROM claims c
JOIN icd_codes ic ON c.icd_code = ic.icd_code
GROUP BY ic.icd_code, ic.icd_description
ORDER BY claim_count DESC
LIMIT 10;


-- Q17. Top 10 procedure (CPT) codes by claim volume.
-- Business purpose: identifies the most frequently billed procedures.
SELECT
    cc.cpt_code,
    cc.cpt_description,
    COUNT(*)                      AS claim_count,
    ROUND(SUM(c.claim_amount), 2) AS total_amount
FROM claims c
JOIN cpt_codes cc ON c.cpt_code = cc.cpt_code
GROUP BY cc.cpt_code, cc.cpt_description
ORDER BY claim_count DESC
LIMIT 10;


-- Q18. Top 5 CPT codes by claim volume, WITHIN each of the top 5 ICD codes.
-- Business purpose: "for the most common diagnoses, what procedures are
-- typically billed alongside them" -- a classic partitioned ranking query
-- combining CTEs with ROW_NUMBER().
WITH top_icd AS (
    SELECT icd_code
    FROM claims
    GROUP BY icd_code
    ORDER BY COUNT(*) DESC
    LIMIT 5
),
icd_cpt_pairs AS (
    SELECT
        c.icd_code,
        c.cpt_code,
        COUNT(*) AS pair_count,
        ROW_NUMBER() OVER (PARTITION BY c.icd_code ORDER BY COUNT(*) DESC) AS rn
    FROM claims c
    JOIN top_icd t ON c.icd_code = t.icd_code
    GROUP BY c.icd_code, c.cpt_code
)
SELECT
    p.icd_code,
    ic.icd_description,
    p.cpt_code,
    cc.cpt_description,
    p.pair_count
FROM icd_cpt_pairs p
JOIN icd_codes ic ON p.icd_code = ic.icd_code
JOIN cpt_codes cc ON p.cpt_code = cc.cpt_code
WHERE p.rn <= 3
ORDER BY p.icd_code, p.rn;


-- Q19. Diagnosis codes with the highest average claim amount (min 15 claims).
-- Business purpose: identifies high-cost conditions -- relevant for case
-- management and cost-containment programs.
SELECT
    ic.icd_code,
    ic.icd_description,
    COUNT(*)                      AS claim_count,
    ROUND(AVG(c.claim_amount), 2) AS avg_amount
FROM claims c
JOIN icd_codes ic ON c.icd_code = ic.icd_code
GROUP BY ic.icd_code, ic.icd_description
HAVING COUNT(*) >= 15
ORDER BY avg_amount DESC
LIMIT 10;


-- =============================================================================
-- SECTION 6: PATIENT / GEOGRAPHIC ANALYSIS
-- =============================================================================

-- Q20. Claims by patient state.
-- Business purpose: geographic distribution of claim volume and cost.
SELECT
    p.state,
    COUNT(c.claim_id)             AS total_claims,
    ROUND(SUM(c.claim_amount), 2) AS total_amount,
    ROUND(AVG(c.claim_amount), 2) AS avg_amount
FROM claims c
JOIN patients p ON c.patient_id = p.patient_id
GROUP BY p.state
ORDER BY total_claims DESC;


-- Q21. Claims by patient age band and gender.
-- Business purpose: demographic utilization pattern -- who is filing the
-- most claims, and does cost vary by age band?
SELECT
    p.age_band,
    p.gender,
    COUNT(c.claim_id)             AS total_claims,
    ROUND(AVG(c.claim_amount), 2) AS avg_amount
FROM claims c
JOIN patients p ON c.patient_id = p.patient_id
GROUP BY p.age_band, p.gender
ORDER BY p.age_band, p.gender;


-- Q22. Top 10 patients by total claim amount (high-utilization patients).
-- Business purpose: identifies patients with the highest total billed
-- amount -- often used to flag candidates for case management outreach.
SELECT
    p.patient_id,
    p.age_band,
    p.state,
    COUNT(c.claim_id)             AS total_claims,
    ROUND(SUM(c.claim_amount), 2) AS total_amount
FROM claims c
JOIN patients p ON c.patient_id = p.patient_id
GROUP BY p.patient_id, p.age_band, p.state
ORDER BY total_amount DESC
LIMIT 10;


-- =============================================================================
-- SECTION 7: CROSS-CUTTING / ADVANCED ANALYTICAL QUERIES
-- =============================================================================

-- Q23. Each claim's amount vs. the average amount for its own CPT code
-- (i.e. how far each claim deviates from the "typical" cost of that
-- procedure). Business purpose: a lightweight outlier-detection query
-- using a window function AVG() OVER (PARTITION BY ...) -- claims far
-- above the procedure's typical cost are worth a manual review.
SELECT
    claim_id,
    cpt_code,
    claim_amount,
    ROUND(AVG(claim_amount) OVER (PARTITION BY cpt_code), 2) AS avg_amount_for_cpt,
    ROUND(claim_amount - AVG(claim_amount) OVER (PARTITION BY cpt_code), 2) AS deviation_from_avg
FROM claims
ORDER BY deviation_from_avg DESC
LIMIT 20;


-- Q24. Provider "scorecard": claim volume, approval rate, and a NTILE(4)
-- quartile bucket ranking providers into performance quartiles by volume.
-- Business purpose: quickly segment the provider network into volume
-- quartiles for account management prioritization.
SELECT
    pr.provider_id,
    pr.provider_name,
    pr.specialty,
    COUNT(*)                                                     AS total_claims,
    ROUND(SUM(c.claim_status = 'Approved') / COUNT(*) * 100, 2)  AS approval_rate_pct,
    NTILE(4) OVER (ORDER BY COUNT(*) DESC)                       AS volume_quartile
FROM claims c
JOIN providers pr ON c.provider_id = pr.provider_id
GROUP BY pr.provider_id, pr.provider_name, pr.specialty
ORDER BY total_claims DESC;


-- Q25. Full claims detail export using the claims_enriched view, filtered
-- to a specific reporting slice (e.g. rejected claims in the most recent
-- quarter of data) -- demonstrates using a pre-built view in an ad hoc
-- operational report a claims examiner might run.
SELECT
    claim_id,
    claim_date,
    claim_amount,
    claim_status,
    provider_name,
    provider_specialty,
    plan_name,
    icd_code,
    icd_description,
    cpt_code,
    cpt_description
FROM claims_enriched
WHERE claim_status = 'Rejected'
ORDER BY claim_date DESC
LIMIT 25;
