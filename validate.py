# validate.py — Run this to verify the dataset
# Usage (PowerShell-safe): python validate.py
# Do NOT paste multi-line code directly into PowerShell — use this file instead

import pandas as pd
import numpy as np

df = pd.read_csv('data/generated/kenya_motor_claims_50000_v4_FINAL.csv')
df['accident_date']     = pd.to_datetime(df['accident_date'])
df['policy_start_date'] = pd.to_datetime(df['policy_start_date'])
acc_year = df['accident_date'].dt.year.astype(int)

veh_ok    = (df['vehicle_age'] == acc_year - df['vehicle_year']).all()
no_early  = (df['accident_date'] >= df['policy_start_date']).all()
pol_ok    = (abs(df['policy_age_days'] - (df['accident_date'] - df['policy_start_date']).dt.days) < 5).all()
ratio1_ok = (abs(df['claim_to_estimate_ratio']    - df['claimed_amount_ksh'] / df['garage_estimate_ksh']) < 0.001).mean() > 0.999
ratio2_ok = (abs(df['claim_to_sum_insured_ratio'] - df['claimed_amount_ksh'] / df['sum_insured_ksh'])     < 0.001).mean() > 0.999
fraud_gap = df.loc[df['is_fraud']==1,'fraud_probability_score'].mean() - df.loc[df['is_fraud']==0,'fraud_probability_score'].mean()

print("=" * 50)
print("  INSURTECH AI — Dataset Validation")
print("=" * 50)
print(f"  Vehicle age OK         : {veh_ok}")
print(f"  No early accidents     : {no_early}")
print(f"  Policy age consistent  : {pol_ok}")
print(f"  claim_to_estimate_ratio: {ratio1_ok}")
print(f"  claim_to_sum_insured   : {ratio2_ok}")
print(f"  Fraud score gap        : {fraud_gap:.3f} (need > 0.35)")
print(f"  Fraud rate             : {df['is_fraud'].mean():.1%}")
print(f"  Rows                   : {len(df):,}")
print(f"  Columns                : {df.shape[1]}")
print(f"  Missing values         : {df.isnull().sum().sum()}")
print("=" * 50)
all_ok = all([veh_ok, no_early, pol_ok, ratio1_ok, ratio2_ok, fraud_gap > 0.35])
print(f"  RESULT: {'ALL CHECKS PASSED' if all_ok else 'SOME CHECKS FAILED'}")
print("=" * 50)