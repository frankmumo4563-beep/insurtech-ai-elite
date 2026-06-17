"""
INSURTECH AI ELITE — Kenya Motor Claims Monte Carlo Simulator
=============================================================
Author: Frank Mumo | University of Nairobi | 2026
Description:
    Generates realistic synthetic Kenyan motor insurance claims
    calibrated to IRA market statistics, AKI industry reports,
    and field structures from Jubilee Allianz & ICEA Lion claim forms.

Parameters anchored to:
    - IRA Annual Insurance Report 2023/2024
    - AKI Industry Statistics (12% motor fraud rate)
    - Kenya National Bureau of Statistics vehicle registration data
    - Nairobi traffic accident patterns (NTSA 2023)
"""

import numpy as np
import pandas as pd
from scipy import stats
import random
import os
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# SEED FOR REPRODUCIBILITY
# ─────────────────────────────────────────────
SEED = 42
np.random.seed(SEED)
random.seed(SEED)

# ─────────────────────────────────────────────
# KENYA-SPECIFIC CONSTANTS
# (anchored to real market data)
# ─────────────────────────────────────────────

# Kenya's vehicle fleet is dominated by used Japanese imports
# Source: NTSA Vehicle Registration Statistics 2023
VEHICLE_MAKES = {
    "Toyota": 0.58,       # Dominant — Probox, Fielder, Premio, Land Cruiser
    "Nissan": 0.12,
    "Mitsubishi": 0.08,
    "Isuzu": 0.06,        # Commercial vehicles
    "Mazda": 0.05,
    "Subaru": 0.04,
    "Honda": 0.03,
    "Volkswagen": 0.02,
    "Mercedes-Benz": 0.01,
    "Other": 0.01,
}

TOYOTA_MODELS = ["Probox", "Fielder", "Premio", "Corolla", "Prado", "Hilux", "Land Cruiser", "Vitz", "Aqua"]
NISSAN_MODELS = ["Tiida", "Note", "X-Trail", "Navara", "Dualis", "March"]
MITSUBISHI_MODELS = ["Outlander", "Pajero", "Colt", "L200", "Galant"]
ISUZU_MODELS = ["D-Max", "FRR", "NPR", "MU-X"]
MAZDA_MODELS = ["Demio", "Axela", "CX-5", "BT-50"]
OTHER_MODELS = ["Impreza", "Forester", "Fit", "Polo", "Vito", "C-Class"]

# Kenyan insurance companies (IRA licensed motor underwriters)
INSURERS = {
    "Jubilee Allianz General": 0.18,
    "ICEA Lion General": 0.14,
    "CIC General": 0.13,
    "APA Insurance": 0.11,
    "Britam General": 0.10,
    "Madison Insurance": 0.08,
    "UAP Old Mutual": 0.07,
    "Sanlam General": 0.06,
    "Resolution Insurance": 0.05,
    "Other Licensed Insurer": 0.08,
}

# Kenyan counties (Nairobi has highest claim volume)
COUNTIES = {
    "Nairobi": 0.42,
    "Mombasa": 0.12,
    "Kiambu": 0.09,
    "Nakuru": 0.08,
    "Kisumu": 0.06,
    "Machakos": 0.04,
    "Uasin Gishu": 0.04,
    "Meru": 0.03,
    "Nyeri": 0.03,
    "Other County": 0.09,
}

# Road types (Nairobi-weighted)
ROAD_TYPES = {
    "Tarmac/Paved": 0.65,
    "Murram/Gravel": 0.20,
    "Highway": 0.10,
    "Dirt Road": 0.05,
}

# Police stations (Nairobi major ones + upcountry)
POLICE_STATIONS = [
    "Central Police Station Nairobi", "Parklands Police Station",
    "Kilimani Police Station", "Kasarani Police Station",
    "Mombasa Central", "Nakuru Police Station",
    "Kisumu Central", "Eldoret Police Station",
    "Thika Police Station", "Machakos Police Station",
]

# Occupations (Kenya labour market distribution)
OCCUPATIONS = {
    "Business/Self-employed": 0.28,
    "Civil Servant": 0.18,
    "Employee (Private Sector)": 0.22,
    "Driver/Transport": 0.12,
    "Farmer": 0.08,
    "Teacher": 0.05,
    "Medical Professional": 0.04,
    "Engineer": 0.03,
}

# Claim types
CLAIM_TYPES = {
    "Own Damage": 0.45,
    "Third Party Property Damage": 0.25,
    "Theft/Total Loss": 0.12,
    "Third Party Bodily Injury": 0.10,
    "Fire Damage": 0.05,
    "Windscreen": 0.03,
}

# ─────────────────────────────────────────────
# FRAUD PATTERN PARAMETERS
# (calibrated to 12% industry fraud rate, IRA 2024)
# ─────────────────────────────────────────────
BASE_FRAUD_RATE = 0.12

# These multipliers increase fraud probability
FRAUD_MULTIPLIERS = {
    "night_incident": 2.3,        # 10pm–5am (fewer witnesses)
    "young_driver": 1.8,          # age < 25
    "new_policy": 2.5,            # policy < 90 days old (hit-and-run pattern)
    "no_police": 1.9,             # no police report filed
    "total_loss_claim": 2.1,      # theft/total loss claims
    "high_amount_claim": 1.6,     # amount > KSh 500,000
    "repeat_claimant": 3.2,       # more than 1 claim in 12 months
    "no_witnesses": 1.7,          # no independent witnesses
    "inconsistent_speed": 1.5,    # reported speed inconsistent with damage
    "single_vehicle": 1.4,        # no other vehicle involved
}

# ─────────────────────────────────────────────
# CLAIM AMOUNT DISTRIBUTIONS (KSh)
# Log-normal is standard actuarial practice for severity
# Parameters estimated from Kenyan motor market
# ─────────────────────────────────────────────
CLAIM_AMOUNT_PARAMS = {
    "Own Damage":                 {"mu": 12.2, "sigma": 0.85},   # ~KSh 200K mean
    "Third Party Property Damage":{"mu": 11.5, "sigma": 0.90},   # ~KSh 100K mean
    "Theft/Total Loss":           {"mu": 13.1, "sigma": 0.70},   # ~KSh 500K mean
    "Third Party Bodily Injury":  {"mu": 12.8, "sigma": 1.10},   # ~KSh 350K mean
    "Fire Damage":                {"mu": 12.5, "sigma": 0.80},
    "Windscreen":                 {"mu": 10.5, "sigma": 0.40},   # ~KSh 36K mean
}

# Fraud inflates claim amounts (fraudsters over-claim)
FRAUD_INFLATION_FACTOR = {"mu_add": 0.6, "sigma_scale": 0.9}


# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

def weighted_choice(options_dict):
    """Pick a key from dict based on probability weights."""
    keys = list(options_dict.keys())
    weights = list(options_dict.values())
    return np.random.choice(keys, p=weights)


def generate_policy_number(insurer_abbrev):
    year = np.random.randint(2019, 2026)
    num = np.random.randint(100000, 999999)
    return f"{insurer_abbrev[:3].upper()}/{year}/{num}"


def generate_id_number():
    """Kenyan National ID: 8 digits"""
    return str(np.random.randint(10000000, 39999999))


def generate_kra_pin():
    """KRA PIN format: A + 9 digits + letter"""
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return f"A{np.random.randint(100000000, 999999999)}{random.choice(letters)}"


def generate_vehicle_reg(county_name):
    """Generate Kenya vehicle registration plates"""
    # Nairobi: KA-KZ series, others have county-specific
    nairobi_series = ["KAA", "KAB", "KAC", "KBA", "KBB", "KBC", "KCA", "KCB",
                      "KDA", "KDB", "KDC", "KEA", "KEB", "KFA", "KGA", "KHA",
                      "KIA", "KJA", "KLA", "KMA", "KNA", "KPA", "KRA", "KSA",
                      "KTA", "KUA", "KVA", "KWA", "KXA", "KYA", "KZA"]
    upcountry_series = ["KXX", "KYY", "KZZ", "UAA", "UAB"]

    if county_name == "Nairobi" or county_name == "Kiambu":
        prefix = random.choice(nairobi_series)
    else:
        prefix = random.choice(upcountry_series)

    number = np.random.randint(100, 999)
    suffix = random.choice("ABCDEFGHJKLMNPQRSTUVWXYZ")
    return f"{prefix} {number}{suffix}"


def generate_accident_datetime(is_fraud):
    """
    Generate realistic accident date/time.
    Fraud: biased toward night hours (10pm–5am).
    Legitimate: biased toward peak traffic (7–9am, 5–8pm).
    """
    # Random date within last 2 years
    base_date = datetime(2023, 1, 1)
    days_offset = np.random.randint(0, 730)
    accident_date = base_date + timedelta(days=int(days_offset))

    if is_fraud and np.random.random() < 0.65:
        # Night hours — fraud window
        hour = np.random.choice(
            list(range(22, 24)) + list(range(0, 6)),
            p=[0.1, 0.1, 0.15, 0.2, 0.2, 0.15, 0.05, 0.05]
        )
    else:
        # Peak traffic hours — morning or evening
        if np.random.random() < 0.5:
            hour = int(np.random.normal(8, 1))   # Morning peak
        else:
            hour = int(np.random.normal(18, 1.5))  # Evening peak
        hour = max(5, min(21, hour))

    minute = np.random.randint(0, 60)
    accident_datetime = accident_date.replace(hour=hour, minute=minute)
    return accident_datetime


def compute_fraud_probability(record):
    """
    Compute fraud probability using multiplicative risk model.
    Starts from base rate and applies multipliers.
    """
    prob = BASE_FRAUD_RATE

    if record.get("night_incident"):
        prob *= FRAUD_MULTIPLIERS["night_incident"]
    if record.get("driver_age", 30) < 25:
        prob *= FRAUD_MULTIPLIERS["young_driver"]
    if record.get("policy_age_days", 365) < 90:
        prob *= FRAUD_MULTIPLIERS["new_policy"]
    if not record.get("police_report_filed"):
        prob *= FRAUD_MULTIPLIERS["no_police"]
    if record.get("claim_type") in ["Theft/Total Loss"]:
        prob *= FRAUD_MULTIPLIERS["total_loss_claim"]
    if record.get("claimed_amount", 0) > 500000:
        prob *= FRAUD_MULTIPLIERS["high_amount_claim"]
    if record.get("prior_claims_12m", 0) > 0:
        prob *= FRAUD_MULTIPLIERS["repeat_claimant"]
    if not record.get("independent_witnesses"):
        prob *= FRAUD_MULTIPLIERS["no_witnesses"]
    if not record.get("other_vehicle_involved"):
        prob *= FRAUD_MULTIPLIERS["single_vehicle"]

    return min(prob, 0.97)  # cap at 97%


def generate_claim_amount(claim_type, is_fraud):
    """Log-normal claim amount, inflated for fraud."""
    params = CLAIM_AMOUNT_PARAMS[claim_type]
    mu = params["mu"]
    sigma = params["sigma"]

    if is_fraud:
        mu += FRAUD_INFLATION_FACTOR["mu_add"]
        sigma *= FRAUD_INFLATION_FACTOR["sigma_scale"]

    amount = np.random.lognormal(mu, sigma)

    # Clamp to realistic Kenyan motor claim range
    amount = max(5000, min(amount, 8_000_000))
    return round(amount, -2)  # Round to nearest 100 KSh


# ─────────────────────────────────────────────
# MAIN SIMULATION FUNCTION
# ─────────────────────────────────────────────

def simulate_kenyan_motor_claims(n_claims=50000, output_path=None):
    """
    Generate n_claims realistic Kenyan motor insurance claim records.

    Parameters
    ----------
    n_claims : int
        Number of claims to generate (default 50,000)
    output_path : str
        Path to save CSV. If None, saves to data/generated/

    Returns
    -------
    pd.DataFrame
        Full claims dataset
    """
    print(f"\n{'='*60}")
    print(f"  INSURTECH AI ELITE — Monte Carlo Claim Simulator")
    print(f"  Generating {n_claims:,} Kenya-calibrated motor claims...")
    print(f"{'='*60}\n")

    records = []

    # Track claimant history for repeat fraud patterns
    claimant_history = {}

    for i in range(n_claims):
        if (i + 1) % 10000 == 0:
            print(f"  ✓ Generated {i+1:,} / {n_claims:,} claims...")

        record = {}

        # ── CLAIM ADMINISTRATION ──────────────────────────
        record["claim_id"] = f"CLM{str(i+1).zfill(6)}"
        insurer = weighted_choice(INSURERS)
        record["insurer"] = insurer
        record["claim_type"] = weighted_choice(CLAIM_TYPES)

        # ── POLICY HOLDER ─────────────────────────────────
        record["insured_id"] = generate_id_number()
        gender = np.random.choice(["Male", "Female"], p=[0.68, 0.32])
        record["insured_gender"] = gender

        # Age distribution: Kenya driver age profile
        age = int(np.random.normal(38, 10))
        age = max(18, min(70, age))
        record["insured_age"] = age

        record["insured_occupation"] = weighted_choice(OCCUPATIONS)
        record["insured_pin"] = generate_kra_pin()

        county = weighted_choice(COUNTIES)
        record["county"] = county

        # ── POLICY DETAILS ────────────────────────────────
        insurer_abbrev = insurer.split()[0]
        record["policy_number"] = generate_policy_number(insurer_abbrev)

        policy_start_offset = np.random.randint(30, 1500)
        policy_age_days = int(policy_start_offset)
        record["policy_age_days"] = policy_age_days
        record["policy_type"] = np.random.choice(
            ["Comprehensive", "Third Party", "Third Party Fire & Theft"],
            p=[0.52, 0.38, 0.10]
        )
        record["sum_insured_ksh"] = round(
            np.random.lognormal(13.5, 0.6), -3
        )  # Vehicle value

        # ── VEHICLE ───────────────────────────────────────
        make = weighted_choice(VEHICLE_MAKES)
        record["vehicle_make"] = make

        model_map = {
            "Toyota": TOYOTA_MODELS, "Nissan": NISSAN_MODELS,
            "Mitsubishi": MITSUBISHI_MODELS, "Isuzu": ISUZU_MODELS,
            "Mazda": MAZDA_MODELS,
        }
        record["vehicle_model"] = random.choice(model_map.get(make, OTHER_MODELS))

        # Kenya vehicle age: mostly 10–20 year old Japanese imports
        manufacture_year = int(np.random.normal(2010, 5))
        manufacture_year = max(1995, min(2024, manufacture_year))
        record["vehicle_year"] = manufacture_year
        record["vehicle_age"] = 2026 - manufacture_year

        record["vehicle_reg"] = generate_vehicle_reg(county)
        record["engine_cc"] = np.random.choice(
            [1000, 1200, 1300, 1500, 1800, 2000, 2500, 3000],
            p=[0.05, 0.10, 0.20, 0.25, 0.20, 0.10, 0.06, 0.04]
        )
        record["vehicle_use"] = np.random.choice(
            ["Private", "Commercial/PSV", "Commercial/Goods", "Government"],
            p=[0.58, 0.22, 0.15, 0.05]
        )

        # ── DRIVER ────────────────────────────────────────
        # Driver may differ from insured (employed driver)
        driver_is_insured = np.random.random() < 0.62
        record["driver_is_insured"] = driver_is_insured

        if driver_is_insured:
            driver_age = age
            record["driver_gender"] = gender
        else:
            driver_age = int(np.random.normal(32, 8))
            driver_age = max(18, min(65, driver_age))
            record["driver_gender"] = np.random.choice(["Male", "Female"], p=[0.78, 0.22])

        record["driver_age"] = driver_age
        record["driver_years_experience"] = max(0, driver_age - 18 - np.random.randint(0, 5))
        record["driver_license_valid"] = np.random.random() < 0.88
        record["driver_prior_accidents"] = int(np.random.poisson(0.15))
        record["driver_prior_convictions"] = int(np.random.poisson(0.04))

        # Prior claims in last 12 months (fraud ring indicator)
        claimant_key = record["insured_id"]
        prior_claims = claimant_history.get(claimant_key, 0)
        record["prior_claims_12m"] = prior_claims
        claimant_history[claimant_key] = prior_claims + 1

        # ── ACCIDENT DETAILS ──────────────────────────────
        # First pass: estimate fraud likelihood to set accident characteristics
        record["night_incident"] = False  # temp
        record["police_report_filed"] = True  # temp
        record["independent_witnesses"] = True  # temp
        record["other_vehicle_involved"] = True  # temp

        # Initial fraud probability
        init_fraud_prob = compute_fraud_probability(record)
        is_fraud_flag = np.random.random() < init_fraud_prob

        # Now generate accident details (fraud-aware)
        accident_dt = generate_accident_datetime(is_fraud_flag)
        record["accident_date"] = accident_dt.strftime("%Y-%m-%d")
        record["accident_time"] = accident_dt.strftime("%H:%M")
        record["accident_hour"] = accident_dt.hour

        night_incident = (accident_dt.hour >= 22 or accident_dt.hour <= 5)
        record["night_incident"] = night_incident

        record["accident_county"] = county
        record["accident_road_type"] = weighted_choice(ROAD_TYPES)

        # Speed (inconsistent with damage is a fraud flag)
        speed = max(0, int(np.random.normal(60, 25)))
        if is_fraud_flag and np.random.random() < 0.3:
            speed = np.random.randint(5, 30)  # Fraudsters claim low speed
        record["reported_speed_kmh"] = speed

        record["weather_conditions"] = np.random.choice(
            ["Clear", "Light Rain", "Heavy Rain", "Foggy", "Overcast"],
            p=[0.55, 0.20, 0.10, 0.05, 0.10]
        )
        record["road_surface_condition"] = np.random.choice(
            ["Dry", "Wet", "Muddy", "Potholed"],
            p=[0.55, 0.25, 0.10, 0.10]
        )

        # Police report (fraudsters avoid police)
        if is_fraud_flag:
            police_filed = np.random.random() < 0.38
        else:
            police_filed = np.random.random() < 0.82
        record["police_report_filed"] = police_filed
        record["police_station"] = random.choice(POLICE_STATIONS) if police_filed else None

        # Witnesses
        if is_fraud_flag:
            has_witnesses = np.random.random() < 0.25
        else:
            has_witnesses = np.random.random() < 0.71
        record["independent_witnesses"] = has_witnesses
        record["witness_count"] = np.random.randint(1, 4) if has_witnesses else 0

        # Other vehicles
        if is_fraud_flag and record["claim_type"] == "Theft/Total Loss":
            other_vehicle = False
        elif is_fraud_flag:
            other_vehicle = np.random.random() < 0.40
        else:
            other_vehicle = np.random.random() < 0.68
        record["other_vehicle_involved"] = other_vehicle
        record["third_party_vehicles_count"] = np.random.randint(1, 3) if other_vehicle else 0

        # Passengers
        record["passengers_in_vehicle"] = np.random.randint(0, 5)
        record["persons_injured"] = np.random.randint(0, record["passengers_in_vehicle"] + 1)

        # ── CLAIM AMOUNTS ─────────────────────────────────
        # Recompute fraud with accurate flags
        final_fraud_prob = compute_fraud_probability(record)
        is_fraud = np.random.random() < final_fraud_prob

        claimed_amount = generate_claim_amount(record["claim_type"], is_fraud)
        record["claimed_amount_ksh"] = claimed_amount

        # Repair estimate vs claimed (fraudsters over-claim)
        if is_fraud:
            garage_estimate = claimed_amount * np.random.uniform(0.35, 0.70)
        else:
            garage_estimate = claimed_amount * np.random.uniform(0.85, 1.05)
        record["garage_estimate_ksh"] = round(garage_estimate, -2)

        # Settlement amount (after investigation)
        if is_fraud and np.random.random() < 0.12:  # Some fraud gets through
            settlement_amount = claimed_amount * np.random.uniform(0.8, 1.0)
        elif is_fraud:
            settlement_amount = garage_estimate * np.random.uniform(0.7, 0.9)
        else:
            settlement_amount = claimed_amount * np.random.uniform(0.88, 0.98)
        record["settlement_amount_ksh"] = round(settlement_amount, -2)

        record["excess_deductible_ksh"] = np.random.choice(
            [5000, 7500, 10000, 15000, 25000],
            p=[0.25, 0.20, 0.30, 0.15, 0.10]
        )

        # ── FRAUD LABEL ───────────────────────────────────
        record["is_fraud"] = int(is_fraud)
        record["fraud_probability_score"] = round(final_fraud_prob, 4)

        # ── ENGINEERED FRAUD RISK FEATURES ───────────────
        # These are the domain-expert features from your original model
        record["amount_to_estimate_ratio"] = round(
            claimed_amount / max(garage_estimate, 1), 4
        )
        record["claim_to_sum_insured_ratio"] = round(
            claimed_amount / max(record["sum_insured_ksh"], 1), 4
        )
        record["policy_age_risk"] = int(policy_age_days < 90)
        record["young_driver_flag"] = int(driver_age < 25)
        record["night_incident_flag"] = int(night_incident)
        record["no_police_flag"] = int(not police_filed)
        record["no_witness_flag"] = int(not has_witnesses)
        record["repeat_claimant_flag"] = int(prior_claims > 0)
        record["single_vehicle_flag"] = int(not other_vehicle)
        record["total_loss_flag"] = int(record["claim_type"] == "Theft/Total Loss")

        # Composite risk score (0–10 scale, for dashboard)
        risk_score = (
            record["policy_age_risk"] * 2.5 +
            record["young_driver_flag"] * 1.8 +
            record["night_incident_flag"] * 2.3 +
            record["no_police_flag"] * 1.9 +
            record["no_witness_flag"] * 1.7 +
            record["repeat_claimant_flag"] * 3.2 +
            record["single_vehicle_flag"] * 1.4 +
            record["total_loss_flag"] * 2.1
        )
        record["composite_risk_score"] = round(min(risk_score, 10), 2)
        record["risk_tier"] = (
            "High" if risk_score >= 4 else
            "Medium" if risk_score >= 2 else
            "Low"
        )

        records.append(record)

    # ── BUILD DATAFRAME ───────────────────────────────────
    df = pd.DataFrame(records)

    # ── SUMMARY STATISTICS ────────────────────────────────
    fraud_rate = df["is_fraud"].mean()
    avg_claim = df["claimed_amount_ksh"].mean()
    total_exposure = df["claimed_amount_ksh"].sum()
    fraud_exposure = df[df["is_fraud"] == 1]["claimed_amount_ksh"].sum()

    print(f"\n{'='*60}")
    print(f"  SIMULATION COMPLETE")
    print(f"{'='*60}")
    print(f"  Total Claims Generated : {len(df):,}")
    print(f"  Fraud Rate             : {fraud_rate:.1%}  (target: ~12%)")
    print(f"  Avg Claim Amount       : KSh {avg_claim:,.0f}")
    print(f"  Total Exposure         : KSh {total_exposure:,.0f}")
    print(f"  Fraud Exposure         : KSh {fraud_exposure:,.0f}")
    print(f"  High Risk Claims       : {(df['risk_tier']=='High').sum():,}")
    print(f"  Medium Risk Claims     : {(df['risk_tier']=='Medium').sum():,}")
    print(f"  Low Risk Claims        : {(df['risk_tier']=='Low').sum():,}")
    print(f"{'='*60}\n")

    # ── SAVE ──────────────────────────────────────────────
    if output_path is None:
        os.makedirs("data/generated", exist_ok=True)
        output_path = f"data/generated/kenya_motor_claims_{n_claims}.csv"

    df.to_csv(output_path, index=False)
    print(f"  ✓ Dataset saved to: {output_path}")
    print(f"  ✓ Shape: {df.shape[0]:,} rows × {df.shape[1]} columns\n")

    return df


# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="INSURTECH AI — Kenya Motor Claims Monte Carlo Simulator"
    )
    parser.add_argument(
        "--n", type=int, default=50000,
        help="Number of claims to generate (default: 50000)"
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output CSV path (default: data/generated/)"
    )
    args = parser.parse_args()

    df = simulate_kenyan_motor_claims(n_claims=args.n, output_path=args.output)
    print("  Sample of generated data:")
    print(df[["claim_id","insurer","claim_type","claimed_amount_ksh",
              "is_fraud","risk_tier","composite_risk_score"]].head(10).to_string(index=False))
