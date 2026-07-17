"""
generate_data.py

Business Purpose
-----------------
Healthcare analytics teams rarely get to build/test pipelines against real
claims data (PHI/PII restrictions, data-sharing agreements, etc.). This
script generates a fully SYNTHETIC claims ecosystem that mimics the shape,
scale, and messiness of real-world healthcare claims data so that the rest
of the platform (cleaning, validation, KPIs, SQL analysis) can be built and
demonstrated end-to-end without ever touching real patient information.

No PHI or PII is created or used. Patient records contain only an
anonymous surrogate ID, age band, gender, and state -- no names, dates of
birth, addresses, or SSNs.

What this script creates
-------------------------
1. patients.csv        - 2,500 anonymous patient records
2. providers.csv        - 300 healthcare providers
3. insurance_plans.csv  - 15 insurance plans
4. icd_codes.csv        - ~150 real, publicly documented ICD-10-CM codes
5. cpt_codes.csv        - ~120 real, publicly documented CPT code ranges
6. claims.csv           - 10,000 claims, ~6% intentionally "dirty" so the
                           downstream data-quality step has real issues to
                           detect (this mimics real claims intake data,
                           which is never perfectly clean).

Design choice: reproducibility
-------------------------------
A fixed random seed (SEED = 42) is used everywhere so that regenerating the
dataset produces identical output. This matters in a portfolio/interview
context -- a reviewer should be able to re-run the script and get the exact
same numbers you show in your README/report.
"""

import random
from datetime import date, timedelta

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

# ---------------------------------------------------------------------------
# Output paths
# ---------------------------------------------------------------------------
RAW_DIR = "../data/raw"

# ---------------------------------------------------------------------------
# Reference constants
# ---------------------------------------------------------------------------
US_STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
]

GENDERS = ["M", "F", "U"]  # U = Unknown/Unspecified
AGE_BANDS = ["0-17", "18-34", "35-49", "50-64", "65-79", "80+"]

SPECIALTIES = [
    "Family Medicine", "Internal Medicine", "Cardiology", "Orthopedics",
    "Pediatrics", "Dermatology", "Radiology", "General Surgery",
    "Neurology", "Psychiatry", "Endocrinology", "Gastroenterology",
    "Oncology", "Ophthalmology", "Urology", "Pulmonology",
    "Emergency Medicine", "Anesthesiology", "Physical Therapy", "Nephrology",
]

PLAN_TYPES = ["HMO", "PPO", "EPO", "POS", "Medicare", "Medicaid", "HDHP"]

CLAIM_STATUSES = ["Approved", "Rejected", "Pending"]
CLAIM_STATUS_WEIGHTS = [0.62, 0.18, 0.20]  # realistic-ish distribution

# Real, publicly documented ICD-10-CM codes (a representative sample
# spanning common chronic and acute conditions). Source: CMS ICD-10-CM
# code list (public domain).
ICD_CODES_SEED = [
    ("A09", "Infectious gastroenteritis and colitis, unspecified"),
    ("B34.9", "Viral infection, unspecified"),
    ("C50.911", "Malignant neoplasm of unspecified site of right female breast"),
    ("D64.9", "Anemia, unspecified"),
    ("E03.9", "Hypothyroidism, unspecified"),
    ("E11.9", "Type 2 diabetes mellitus without complications"),
    ("E66.9", "Obesity, unspecified"),
    ("F32.9", "Major depressive disorder, single episode, unspecified"),
    ("F41.1", "Generalized anxiety disorder"),
    ("G43.909", "Migraine, unspecified, not intractable, without status migrainosus"),
    ("G47.33", "Obstructive sleep apnea (adult) (pediatric)"),
    ("I10", "Essential (primary) hypertension"),
    ("I25.10", "Atherosclerotic heart disease of native coronary artery"),
    ("I48.91", "Unspecified atrial fibrillation"),
    ("I50.9", "Heart failure, unspecified"),
    ("J06.9", "Acute upper respiratory infection, unspecified"),
    ("J18.9", "Pneumonia, unspecified organism"),
    ("J44.9", "Chronic obstructive pulmonary disease, unspecified"),
    ("J45.909", "Unspecified asthma, uncomplicated"),
    ("K21.9", "Gastro-esophageal reflux disease without esophagitis"),
    ("K29.70", "Gastritis, unspecified, without bleeding"),
    ("K35.80", "Unspecified acute appendicitis"),
    ("K59.00", "Constipation, unspecified"),
    ("L03.90", "Cellulitis, unspecified"),
    ("M15.9", "Polyosteoarthritis, unspecified"),
    ("M25.50", "Pain in unspecified joint"),
    ("M54.5", "Low back pain"),
    ("M79.1", "Myalgia"),
    ("N18.9", "Chronic kidney disease, unspecified"),
    ("N39.0", "Urinary tract infection, site not specified"),
    ("R05.9", "Cough, unspecified"),
    ("R07.9", "Chest pain, unspecified"),
    ("R10.9", "Unspecified abdominal pain"),
    ("R11.10", "Vomiting, unspecified"),
    ("R42", "Dizziness and giddiness"),
    ("R50.9", "Fever, unspecified"),
    ("R51.9", "Headache, unspecified"),
    ("R53.83", "Other fatigue"),
    ("S06.0X0A", "Concussion without loss of consciousness, initial encounter"),
    ("S93.401A", "Sprain of unspecified ligament of right ankle, initial encounter"),
    ("T78.40XA", "Allergy, unspecified, initial encounter"),
    ("Z00.00", "Encounter for general adult medical examination without abnormal findings"),
    ("Z23", "Encounter for immunization"),
    ("Z79.4", "Long term (current) use of insulin"),
    ("E78.5", "Hyperlipidemia, unspecified"),
    ("F17.210", "Nicotine dependence, cigarettes, uncomplicated"),
    ("H52.4", "Presbyopia"),
    ("H10.9", "Unspecified conjunctivitis"),
    ("H66.90", "Otitis media, unspecified, unspecified ear"),
    ("J01.90", "Acute sinusitis, unspecified"),
    ("J02.9", "Acute pharyngitis, unspecified"),
    ("J03.90", "Acute tonsillitis, unspecified"),
    ("J20.9", "Acute bronchitis, unspecified"),
    ("K52.9", "Noninfective gastroenteritis and colitis, unspecified"),
    ("K80.20", "Calculus of gallbladder without cholecystitis without obstruction"),
    ("L20.9", "Atopic dermatitis, unspecified"),
    ("L30.9", "Dermatitis, unspecified"),
    ("M17.9", "Osteoarthritis of knee, unspecified"),
    ("M19.90", "Osteoarthritis, unspecified site"),
    ("M25.511", "Pain in right shoulder"),
    ("M25.512", "Pain in left shoulder"),
    ("M25.561", "Pain in right knee"),
    ("M25.562", "Pain in left knee"),
    ("M54.2", "Cervicalgia"),
    ("M54.9", "Dorsalgia, unspecified"),
    ("N40.0", "Benign prostatic hyperplasia without lower urinary tract symptoms"),
    ("O80", "Encounter for full-term uncomplicated delivery"),
    ("R00.0", "Tachycardia, unspecified"),
    ("R06.02", "Shortness of breath"),
    ("R19.7", "Diarrhea, unspecified"),
    ("R21", "Rash and other nonspecific skin eruption"),
    ("R41.0", "Disorientation, unspecified"),
    ("R55", "Syncope and collapse"),
    ("R60.9", "Edema, unspecified"),
    ("S00.83XA", "Contusion of other part of head, initial encounter"),
    ("S61.409A", "Unspecified open wound of right hand, initial encounter"),
    ("T14.90XA", "Injury, unspecified, initial encounter"),
    ("Z00.129", "Encounter for routine child health examination without abnormal findings"),
    ("Z01.419", "Encounter for gynecological examination without abnormal findings"),
    ("Z12.11", "Encounter for screening for malignant neoplasm of colon"),
    ("Z12.31", "Encounter for screening mammogram for malignant neoplasm of breast"),
    ("Z13.220", "Encounter for screening for lipoid disorders"),
    ("Z34.90", "Encounter for supervision of normal pregnancy, unspecified trimester"),
    ("Z71.3", "Dietary counseling and surveillance"),
    ("Z76.89", "Persons encountering health services in other specified circumstances"),
    ("Z79.899", "Other long term (current) drug therapy"),
    ("Z86.73", "Personal history of transient ischemic attack, and cerebral infarction without residual deficits"),
    ("Z87.891", "Personal history of nicotine dependence"),
    ("D50.9", "Iron deficiency anemia, unspecified"),
    ("D69.6", "Thrombocytopenia, unspecified"),
    ("E03.8", "Other specified hypothyroidism"),
    ("E55.9", "Vitamin D deficiency, unspecified"),
    ("E86.0", "Dehydration"),
    ("F10.20", "Alcohol dependence, uncomplicated"),
    ("F31.9", "Bipolar disorder, unspecified"),
    ("F43.10", "Post-traumatic stress disorder, unspecified"),
    ("F90.9", "Attention-deficit hyperactivity disorder, unspecified type"),
    ("G40.909", "Epilepsy, unspecified, not intractable, without status epilepticus"),
    ("G89.29", "Other chronic pain"),
    ("H25.9", "Unspecified age-related cataract"),
    ("H40.9", "Unspecified glaucoma"),
    ("H61.20", "Impacted cerumen, unspecified ear"),
    ("I63.9", "Cerebral infarction, unspecified"),
    ("I73.9", "Peripheral vascular disease, unspecified"),
    ("I80.219", "Phlebitis and thrombophlebitis of unspecified deep vessels of left lower extremity"),
    ("I95.9", "Hypotension, unspecified"),
    ("J30.9", "Allergic rhinitis, unspecified"),
    ("J32.9", "Chronic sinusitis, unspecified"),
    ("J34.89", "Other specified disorders of nose and nasal sinuses"),
    ("J93.9", "Pneumothorax, unspecified"),
    ("K21.00", "Gastro-esophageal reflux disease with esophagitis"),
    ("K57.30", "Diverticulosis of large intestine without perforation or abscess without bleeding"),
    ("K58.9", "Irritable bowel syndrome without diarrhea"),
    ("K76.0", "Fatty (change of) liver, not elsewhere classified"),
    ("L02.91", "Cutaneous abscess, unspecified"),
    ("L40.9", "Psoriasis, unspecified"),
    ("L50.9", "Urticaria, unspecified"),
    ("L57.0", "Actinic keratosis"),
    ("M06.9", "Rheumatoid arthritis, unspecified"),
    ("M10.9", "Gout, unspecified"),
    ("M47.812", "Spondylosis without myelopathy or radiculopathy, cervical region"),
    ("M48.06", "Spinal stenosis, lumbar region"),
    ("M53.1", "Cervicobrachial syndrome"),
    ("M62.830", "Muscle spasm of back"),
    ("M65.9", "Synovitis and tenosynovitis, unspecified"),
    ("M75.100", "Unspecified rotator cuff tear or rupture of right shoulder, not specified as traumatic"),
    ("N18.30", "Chronic kidney disease, stage 3 unspecified"),
    ("N20.0", "Calculus of kidney"),
    ("N30.00", "Acute cystitis without hematuria"),
    ("N92.6", "Irregular menstruation, unspecified"),
    ("N95.1", "Menopausal and female climacteric states"),
    ("O09.90", "Supervision of high risk pregnancy, unspecified, unspecified trimester"),
    ("O26.90", "Pregnancy related conditions, unspecified, unspecified trimester"),
    ("P59.9", "Neonatal jaundice, unspecified"),
    ("Q21.10", "Atrial septal defect, unspecified"),
    ("R00.2", "Palpitations"),
    ("R09.02", "Hypoxemia"),
    ("R23.4", "Changes in skin texture"),
    ("R30.0", "Dysuria"),
    ("R31.9", "Hematuria, unspecified"),
    ("R33.9", "Retention of urine, unspecified"),
    ("R34", "Anuria and oliguria"),
    ("R56.9", "Unspecified convulsions"),
    ("R63.4", "Abnormal weight loss"),
    ("S52.501A", "Unspecified fracture of the lower end of right radius, initial encounter"),
    ("S82.891A", "Other fracture of right lower leg, initial encounter"),
    ("T50.905A", "Poisoning by unspecified drugs, accidental, initial encounter"),
    ("Z79.01", "Long term (current) use of anticoagulants"),
    ("Z79.84", "Long term (current) use of oral hypoglycemic drugs"),
    ("Z88.0", "Allergy status to penicillin"),
]

# Real, publicly documented CPT code ranges with representative sample
# codes and descriptions (Source: AMA CPT code structure -- ranges are
# public knowledge; specific codes below are commonly-used, publicly
# referenced examples used for illustrative/educational purposes).
CPT_CODES_SEED = [
    ("99201", "Office/outpatient visit new, straightforward"),
    ("99202", "Office/outpatient visit new, low complexity"),
    ("99203", "Office/outpatient visit new, moderate complexity"),
    ("99204", "Office/outpatient visit new, moderate-high complexity"),
    ("99205", "Office/outpatient visit new, high complexity"),
    ("99211", "Office/outpatient visit established, minimal"),
    ("99212", "Office/outpatient visit established, straightforward"),
    ("99213", "Office/outpatient visit established, low complexity"),
    ("99214", "Office/outpatient visit established, moderate complexity"),
    ("99215", "Office/outpatient visit established, high complexity"),
    ("99221", "Initial hospital care, low severity"),
    ("99222", "Initial hospital care, moderate severity"),
    ("99223", "Initial hospital care, high severity"),
    ("99231", "Subsequent hospital care, stable"),
    ("99232", "Subsequent hospital care, minor complication"),
    ("99233", "Subsequent hospital care, unstable"),
    ("99281", "Emergency department visit, minor"),
    ("99282", "Emergency department visit, low to moderate"),
    ("99283", "Emergency department visit, moderate"),
    ("99284", "Emergency department visit, high severity"),
    ("99285", "Emergency department visit, high severity/threat to life"),
    ("99381", "Preventive visit, new patient, infant"),
    ("99385", "Preventive visit, new patient, 18-39 years"),
    ("99395", "Preventive visit, established patient, 18-39 years"),
    ("99396", "Preventive visit, established patient, 40-64 years"),
    ("99397", "Preventive visit, established patient, 65+ years"),
    ("36415", "Collection of venous blood by venipuncture"),
    ("71045", "Chest X-ray, single view"),
    ("71046", "Chest X-ray, two views"),
    ("71250", "CT thorax without contrast"),
    ("72110", "X-ray lumbar spine, 4+ views"),
    ("72148", "MRI lumbar spine without contrast"),
    ("73030", "X-ray shoulder, complete"),
    ("73721", "MRI lower extremity joint without contrast"),
    ("74176", "CT abdomen and pelvis without contrast"),
    ("74177", "CT abdomen and pelvis with contrast"),
    ("76700", "Abdominal ultrasound, complete"),
    ("76705", "Abdominal ultrasound, limited"),
    ("76770", "Retroperitoneal ultrasound, complete"),
    ("76856", "Pelvic ultrasound, complete"),
    ("77067", "Screening mammography, bilateral"),
    ("80048", "Basic metabolic panel"),
    ("80053", "Comprehensive metabolic panel"),
    ("80061", "Lipid panel"),
    ("81001", "Urinalysis with microscopy"),
    ("81002", "Urinalysis without microscopy"),
    ("82947", "Glucose, blood quantitative"),
    ("83036", "Hemoglobin A1c"),
    ("84443", "Thyroid stimulating hormone (TSH)"),
    ("85025", "Complete blood count with differential"),
    ("85027", "Complete blood count, automated"),
    ("86803", "Hepatitis C antibody test"),
    ("87070", "Bacterial culture"),
    ("87086", "Urine bacterial culture"),
    ("87491", "Chlamydia trachomatis, amplified probe"),
    ("87591", "Neisseria gonorrhoeae, amplified probe"),
    ("87635", "SARS-CoV-2 detection, amplified probe"),
    ("90471", "Immunization administration, one vaccine"),
    ("90472", "Immunization administration, each additional vaccine"),
    ("90658", "Influenza vaccine, injectable"),
    ("90715", "Tdap vaccine"),
    ("90732", "Pneumococcal vaccine"),
    ("90791", "Psychiatric diagnostic evaluation"),
    ("90792", "Psychiatric diagnostic evaluation with medical services"),
    ("90832", "Psychotherapy, 30 minutes"),
    ("90834", "Psychotherapy, 45 minutes"),
    ("90837", "Psychotherapy, 60 minutes"),
    ("92014", "Eye exam, established patient, comprehensive"),
    ("92557", "Comprehensive hearing test"),
    ("93000", "Electrocardiogram, complete"),
    ("93010", "Electrocardiogram, interpretation only"),
    ("93306", "Echocardiography, complete"),
    ("93880", "Duplex scan of carotid arteries"),
    ("94010", "Spirometry"),
    ("94060", "Bronchodilation responsiveness test"),
    ("94640", "Nebulizer treatment"),
    ("94664", "Inhaler demonstration"),
    ("95810", "Polysomnography, sleep study"),
    ("96116", "Neurobehavioral status exam"),
    ("96372", "Therapeutic injection, subcutaneous/intramuscular"),
    ("97110", "Therapeutic exercise"),
    ("97112", "Neuromuscular reeducation"),
    ("97140", "Manual therapy techniques"),
    ("97161", "Physical therapy evaluation, low complexity"),
    ("97162", "Physical therapy evaluation, moderate complexity"),
    ("97535", "Self-care/home management training"),
    ("99050", "Services after posted office hours"),
    ("99070", "Supplies and materials provided by physician"),
    ("99091", "Collection and interpretation of physiologic data"),
    ("99406", "Smoking cessation counseling, 3-10 minutes"),
    ("99406", "Smoking cessation counseling, > 10 minutes"),
    ("99490", "Chronic care management, first 20 minutes"),
    ("99495", "Transitional care management, moderate complexity"),
    ("11042", "Debridement, subcutaneous tissue"),
    ("11720", "Debridement of nail, 1-5"),
    ("12001", "Simple repair of superficial wounds, 2.5cm or less"),
    ("12031", "Layer closure of wounds"),
    ("17000", "Destruction of premalignant lesion, first lesion"),
    ("20610", "Arthrocentesis, aspiration and/or injection, major joint"),
    ("29125", "Application of short arm splint"),
    ("29881", "Knee arthroscopy with meniscectomy"),
    ("43239", "Upper GI endoscopy with biopsy"),
    ("45378", "Colonoscopy, diagnostic"),
    ("45380", "Colonoscopy with biopsy"),
    ("47562", "Laparoscopic cholecystectomy"),
    ("58150", "Total abdominal hysterectomy"),
    ("59400", "Routine obstetric care, vaginal delivery"),
    ("59510", "Routine obstetric care, cesarean delivery"),
    ("62323", "Lumbar epidural injection"),
    ("64483", "Lumbar transforaminal epidural injection"),
    ("66984", "Cataract surgery with IOL insertion"),
    ("69210", "Removal of impacted cerumen"),
    ("27447", "Total knee arthroplasty"),
    ("27130", "Total hip arthroplasty"),
]


# ---------------------------------------------------------------------------
# Table generators
# ---------------------------------------------------------------------------
def generate_patients(n=2500):
    """
    Generate anonymous patient records.

    Business purpose: Patients table supports claim-level demographic
    aggregation (e.g. "claims by age band/state") WITHOUT storing any
    identifying information. Only a surrogate patient_id, age_band,
    gender, and state are stored -- no names, DOB, address, or SSN.
    """
    records = []
    for i in range(1, n + 1):
        records.append({
            "patient_id": f"PAT{i:06d}",
            "age_band": random.choice(AGE_BANDS),
            "gender": random.choice(GENDERS),
            "state": random.choice(US_STATES),
        })
    return pd.DataFrame(records)


def generate_providers(n=300):
    """
    Generate provider (physician/facility) records.

    Business purpose: Providers are the entities submitting claims.
    Realistic NPI-style IDs (10-digit numeric, matching the real NPI
    format) are generated for realism, along with specialty and state,
    to support "claims by provider/specialty" reporting.
    """
    records = []
    used_npis = set()
    for i in range(1, n + 1):
        # Generate a unique 10-digit synthetic NPI-style identifier
        while True:
            npi = f"1{random.randint(100000000, 999999999)}"
            if npi not in used_npis:
                used_npis.add(npi)
                break
        records.append({
            "provider_id": f"PRV{i:05d}",
            "npi": npi,
            "provider_name": f"Provider {i:05d}",  # synthetic, non-identifying
            "specialty": random.choice(SPECIALTIES),
            "state": random.choice(US_STATES),
        })
    return pd.DataFrame(records)


def generate_insurance_plans():
    """
    Generate insurance plan reference data.

    Business purpose: claims are always associated with an insurance
    plan; the plan type drives reimbursement rules downstream and is a
    common dimension for "claims by insurance plan" reporting.
    """
    plan_names = [
        "BluePath HMO", "BluePath PPO", "SilverCross EPO", "SilverCross POS",
        "MediCare Advantage Plus", "MediCare Advantage Standard",
        "StateAid Medicaid", "StateAid Medicaid Managed",
        "Horizon HDHP Bronze", "Horizon HDHP Silver",
        "Summit PPO Gold", "Summit PPO Platinum",
        "ValleyHealth HMO", "ValleyHealth EPO", "Guardian POS",
    ]
    records = []
    for i, name in enumerate(plan_names, start=1):
        plan_type = next((pt for pt in PLAN_TYPES if pt.lower() in name.lower()), None)
        if plan_type is None:
            plan_type = random.choice(PLAN_TYPES)
        records.append({
            "plan_id": f"PLN{i:03d}",
            "plan_name": name,
            "plan_type": plan_type,
        })
    return pd.DataFrame(records)


def generate_icd_codes():
    """
    Load the curated set of real, publicly documented ICD-10-CM codes.

    Business purpose: this acts as the reference/lookup table used to
    validate diagnosis codes on incoming claims -- a core data-quality
    control in real healthcare claims processing.
    """
    return pd.DataFrame(ICD_CODES_SEED, columns=["icd_code", "icd_description"])


def generate_cpt_codes():
    """
    Load the curated set of real, publicly documented CPT codes.

    Business purpose: this acts as the reference/lookup table used to
    validate procedure codes on incoming claims.
    """
    df = pd.DataFrame(CPT_CODES_SEED, columns=["cpt_code", "cpt_description"])
    return df.drop_duplicates(subset="cpt_code").reset_index(drop=True)


def generate_claims(
    n,
    patients_df,
    providers_df,
    plans_df,
    icd_df,
    cpt_df,
    dirty_rate=0.06,
):
    """
    Generate the Claims fact table, with a configurable percentage of
    intentionally "dirty" records injected to simulate real-world claims
    intake data quality issues.

    Business purpose: this is the central fact table of the platform. In
    a real claims pipeline, incoming claims are NEVER perfectly clean --
    they arrive with missing codes, mistyped provider IDs, duplicate
    submissions, and other issues that the Data Quality layer must catch
    before the claim is trusted for reporting. Injecting a known,
    controlled amount of dirty data (~6%) lets us later prove the
    validation logic actually works, and gives realistic-looking DQ
    metrics for the portfolio.

    Dirty data categories injected (roughly evenly split across the
    dirty_rate budget):
      - missing ICD code
      - missing CPT code
      - invalid ICD code (not in reference table)
      - invalid CPT code (not in reference table)
      - invalid provider_id (not in Providers table)
      - duplicate claim (exact re-submission of another claim_id's data)
      - future claim date
      - negative claim amount
      - invalid claim status (not in allowed status list)
      - missing insurance plan
    """
    patient_ids = patients_df["patient_id"].tolist()
    provider_ids = providers_df["provider_id"].tolist()
    plan_ids = plans_df["plan_id"].tolist()
    icd_codes = icd_df["icd_code"].tolist()
    cpt_codes = cpt_df["cpt_code"].tolist()

    start_date = date(2023, 1, 1)
    end_date = date(2025, 12, 31)
    date_range_days = (end_date - start_date).days

    records = []
    for i in range(1, n + 1):
        claim_date = start_date + timedelta(days=random.randint(0, date_range_days))
        claim_amount = round(np.random.gamma(shape=3.0, scale=120.0) + 25, 2)

        records.append({
            "claim_id": f"CLM{i:07d}",
            "patient_id": random.choice(patient_ids),
            "provider_id": random.choice(provider_ids),
            "plan_id": random.choice(plan_ids),
            "icd_code": random.choice(icd_codes),
            "cpt_code": random.choice(cpt_codes),
            "claim_date": claim_date.isoformat(),
            "claim_amount": claim_amount,
            "claim_status": random.choices(CLAIM_STATUSES, weights=CLAIM_STATUS_WEIGHTS)[0],
        })

    claims_df = pd.DataFrame(records)

    # ------------------------------------------------------------------
    # Inject dirty data into a random, non-overlapping-by-category sample
    # of rows. Using disjoint index sets keeps each dirty category
    # independently countable/verifiable in the DQ report.
    # ------------------------------------------------------------------
    n_dirty_each = int(n * dirty_rate / 10)  # 10 dirty categories
    all_idx = list(claims_df.index)
    random.shuffle(all_idx)

    dirty_slices = {}
    pointer = 0
    for category in [
        "missing_icd", "missing_cpt", "invalid_icd", "invalid_cpt",
        "invalid_provider", "duplicate", "future_date", "negative_amount",
        "invalid_status", "missing_plan",
    ]:
        dirty_slices[category] = all_idx[pointer: pointer + n_dirty_each]
        pointer += n_dirty_each

    claims_df.loc[dirty_slices["missing_icd"], "icd_code"] = np.nan
    claims_df.loc[dirty_slices["missing_cpt"], "cpt_code"] = np.nan
    claims_df.loc[dirty_slices["invalid_icd"], "icd_code"] = "X99.999"
    claims_df.loc[dirty_slices["invalid_cpt"], "cpt_code"] = "00000"
    claims_df.loc[dirty_slices["invalid_provider"], "provider_id"] = "PRVXXXXX"
    # Anchor "future" dates to the REAL system date (not a fixed date),
    # so these rows remain genuinely future-dated no matter when this
    # script is run or when the validation step is later executed.
    today = date.today()
    claims_df.loc[dirty_slices["future_date"], "claim_date"] = [
        (today + timedelta(days=random.randint(30, 700))).isoformat()
        for _ in dirty_slices["future_date"]
    ]
    claims_df.loc[dirty_slices["negative_amount"], "claim_amount"] = [
        -round(abs(v), 2) for v in claims_df.loc[dirty_slices["negative_amount"], "claim_amount"]
    ]
    claims_df.loc[dirty_slices["invalid_status"], "claim_status"] = "Unknown"
    claims_df.loc[dirty_slices["missing_plan"], "plan_id"] = np.nan

    # Duplicate claims: take rows and re-append them with a NEW claim_id
    # but IDENTICAL business content (same patient/provider/plan/codes/
    # date/amount) -- this simulates a claim being submitted twice, a
    # very common real-world claims data-quality issue.
    dup_rows = claims_df.loc[dirty_slices["duplicate"]].copy()
    dup_rows["claim_id"] = [f"CLM{n + j:07d}" for j in range(1, len(dup_rows) + 1)]
    claims_df = pd.concat([claims_df, dup_rows], ignore_index=True)

    # Shuffle final row order so dirty records aren't clustered/obvious
    claims_df = claims_df.sample(frac=1, random_state=SEED).reset_index(drop=True)

    return claims_df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("Generating synthetic healthcare claims dataset...")

    patients_df = generate_patients(n=2500)
    providers_df = generate_providers(n=300)
    plans_df = generate_insurance_plans()
    icd_df = generate_icd_codes()
    cpt_df = generate_cpt_codes()
    claims_df = generate_claims(
        n=10000,
        patients_df=patients_df,
        providers_df=providers_df,
        plans_df=plans_df,
        icd_df=icd_df,
        cpt_df=cpt_df,
        dirty_rate=0.06,
    )

    patients_df.to_csv(f"{RAW_DIR}/patients.csv", index=False)
    providers_df.to_csv(f"{RAW_DIR}/providers.csv", index=False)
    plans_df.to_csv(f"{RAW_DIR}/insurance_plans.csv", index=False)
    icd_df.to_csv(f"{RAW_DIR}/icd_codes.csv", index=False)
    cpt_df.to_csv(f"{RAW_DIR}/cpt_codes.csv", index=False)
    claims_df.to_csv(f"{RAW_DIR}/claims.csv", index=False)

    print(f"  patients.csv         -> {len(patients_df):,} rows")
    print(f"  providers.csv        -> {len(providers_df):,} rows")
    print(f"  insurance_plans.csv  -> {len(plans_df):,} rows")
    print(f"  icd_codes.csv        -> {len(icd_df):,} rows")
    print(f"  cpt_codes.csv        -> {len(cpt_df):,} rows")
    print(f"  claims.csv           -> {len(claims_df):,} rows "
          f"(includes injected duplicate claims + dirty data)")
    print("\nAll files written to:", RAW_DIR)


if __name__ == "__main__":
    main()
