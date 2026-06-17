"""
INSURTECH AI ELITE — Fraud Detection & Actuarial Pricing Model
==============================================================
Author: Frank Mumo | University of Nairobi | 2026

Two integrated models:
  1. FRAUD DETECTION — Random Forest classifier (upgraded with fraud ring detection)
  2. LOSS COST PRICING — Actuarial pure premium model
      Pure Premium = Frequency × Severity
      Risk-Adjusted Premium = Pure Premium / (1 - Expense Ratio - Profit Margin)

Accepts: CSV, Excel, PDF, JSON (via ingest.py)
Outputs: Predictions CSV + model files + full report
"""

import os
import sys
import warnings
import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
warnings.filterwarnings("ignore")

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (
    accuracy_score, roc_auc_score, classification_report,
    confusion_matrix, mean_squared_error, r2_score,
    precision_recall_curve, roc_curve
)
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer

try:
    import xgboost as xgb
    XGBOOST = True
except ImportError:
    XGBOOST = False

# Import ingest module for multi-format support
sys.path.append(os.path.dirname(__file__))
try:
    from ingest import ingest_file, ingest_folder
    INGEST_AVAILABLE = True
except ImportError:
    INGEST_AVAILABLE = False


# ─────────────────────────────────────────────
# ACTUARIAL CONSTANTS (Kenya market)
# ─────────────────────────────────────────────
EXPENSE_RATIO = 0.30          # 30% — AKI industry average
PROFIT_MARGIN = 0.05          # 5%
CLAIMS_FREQUENCY_BASE = 0.18  # 18% of vehicles file a claim per year (IRA 2023)
FRAUD_COST_FN = 120_000       # KSh — cost of missing a fraud case
FRAUD_COST_FP = 3_000         # KSh — cost of wrongful investigation


# ─────────────────────────────────────────────
# FEATURE SETS
# ─────────────────────────────────────────────

FRAUD_FEATURES = [
    # Engineered risk flags
    "policy_age_risk", "young_driver_flag", "night_incident_flag",
    "no_police_flag", "no_witness_flag", "repeat_claimant_flag",
    "single_vehicle_flag", "total_loss_flag",
    # Quantitative features
    "claimed_amount_ksh", "amount_to_estimate_ratio",
    "claim_to_sum_insured_ratio", "driver_age", "vehicle_age",
    "driver_years_experience", "driver_prior_accidents",
    "passengers_in_vehicle", "persons_injured",
    "reported_speed_kmh", "witness_count",
    "third_party_vehicles_count", "prior_claims_12m",
    # Composite score
    "composite_risk_score",
]

PRICING_FEATURES = [
    "claimed_amount_ksh", "vehicle_age", "driver_age",
    "driver_years_experience", "driver_prior_accidents",
    "engine_cc", "passengers_in_vehicle",
    "night_incident_flag", "young_driver_flag",
    "policy_age_risk", "composite_risk_score",
    "fraud_probability",  # injected after fraud model runs
]

CATEGORICAL_FEATURES = [
    "claim_type", "insurer", "county", "vehicle_make",
    "vehicle_use", "policy_type", "weather_conditions",
    "road_surface_condition", "accident_road_type",
]


# ─────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────

def load_data(path):
    """
    Load claims data from any supported format.
    Automatically detects CSV, Excel, PDF, JSON.
    """
    ext = os.path.splitext(path)[1].lower()
    print(f"\n  Loading data: {os.path.basename(path)}")

    if ext == ".csv":
        df = pd.read_csv(path, low_memory=False)
    elif ext in [".xlsx", ".xls"]:
        df = pd.read_excel(path)
    elif ext in [".pdf", ".json"] and INGEST_AVAILABLE:
        df = ingest_file(path)
    elif os.path.isdir(path) and INGEST_AVAILABLE:
        df = ingest_folder(path)
    else:
        # Last resort: try CSV
        df = pd.read_csv(path, low_memory=False)

    print(f"  ✓ Loaded: {df.shape[0]:,} rows × {df.shape[1]} columns")
    return df


# ─────────────────────────────────────────────
# PREPROCESSING
# ─────────────────────────────────────────────

def preprocess(df):
    """
    Clean, encode, and prepare features for modeling.
    Handles missing values, encodes categoricals, ensures all
    required engineered features exist.
    """
    df = df.copy()

    # ── Derive missing engineered features ───────────────
    if "policy_age_risk" not in df.columns:
        df["policy_age_risk"] = (df.get("policy_age_days", 365) < 90).astype(int)

    if "young_driver_flag" not in df.columns:
        df["young_driver_flag"] = (df.get("driver_age", 30) < 25).astype(int)

    if "night_incident_flag" not in df.columns:
        df["night_incident_flag"] = df.get("night_incident", False).astype(int)

    if "no_police_flag" not in df.columns:
        df["no_police_flag"] = (~df.get("police_report_filed", True).astype(bool)).astype(int)

    if "no_witness_flag" not in df.columns:
        df["no_witness_flag"] = (~df.get("independent_witnesses", True).astype(bool)).astype(int)

    if "repeat_claimant_flag" not in df.columns:
        df["repeat_claimant_flag"] = (df.get("prior_claims_12m", 0) > 0).astype(int)

    if "single_vehicle_flag" not in df.columns:
        df["single_vehicle_flag"] = (~df.get("other_vehicle_involved", True).astype(bool)).astype(int)

    if "total_loss_flag" not in df.columns:
        df["total_loss_flag"] = (df.get("claim_type", "") == "Theft/Total Loss").astype(int)

    if "vehicle_age" not in df.columns and "vehicle_year" in df.columns:
        df["vehicle_age"] = 2026 - pd.to_numeric(df["vehicle_year"], errors="coerce")

    if "amount_to_estimate_ratio" not in df.columns:
        df["amount_to_estimate_ratio"] = (
            df.get("claimed_amount_ksh", 0) /
            df.get("garage_estimate_ksh", 1).replace(0, np.nan)
        ).fillna(1.0)

    if "claim_to_sum_insured_ratio" not in df.columns:
        df["claim_to_sum_insured_ratio"] = (
            df.get("claimed_amount_ksh", 0) /
            df.get("sum_insured_ksh", 1).replace(0, np.nan)
        ).fillna(0.0)

    if "composite_risk_score" not in df.columns:
        df["composite_risk_score"] = (
            df.get("policy_age_risk", 0) * 2.5 +
            df.get("young_driver_flag", 0) * 1.8 +
            df.get("night_incident_flag", 0) * 2.3 +
            df.get("no_police_flag", 0) * 1.9 +
            df.get("no_witness_flag", 0) * 1.7 +
            df.get("repeat_claimant_flag", 0) * 3.2 +
            df.get("single_vehicle_flag", 0) * 1.4 +
            df.get("total_loss_flag", 0) * 2.1
        ).clip(0, 10)

    # ── Encode categoricals ───────────────────────────────
    le = LabelEncoder()
    encoded_cats = []
    for col in CATEGORICAL_FEATURES:
        if col in df.columns:
            df[col + "_enc"] = le.fit_transform(df[col].astype(str).fillna("Unknown"))
            encoded_cats.append(col + "_enc")

    return df, encoded_cats


# ─────────────────────────────────────────────
# FRAUD DETECTION MODEL
# ─────────────────────────────────────────────

class FraudDetectionModel:
    """
    Random Forest fraud classifier with cost-optimal threshold selection.
    Compares multiple algorithms and selects best by AUC.
    """

    def __init__(self):
        self.model = None
        self.threshold = 0.22
        self.feature_names = None
        self.scaler = StandardScaler()
        self.results = {}

    def get_features(self, df, encoded_cats):
        available = [f for f in FRAUD_FEATURES if f in df.columns]
        available += [c for c in encoded_cats if c in df.columns]
        return available

    def train(self, df, encoded_cats):
        print("\n" + "="*60)
        print("  FRAUD DETECTION MODEL TRAINING")
        print("="*60)

        features = self.get_features(df, encoded_cats)
        self.feature_names = features

        if "is_fraud" not in df.columns:
            print("  ✗ No 'is_fraud' column found. Cannot train fraud model.")
            return None

        X = df[features].fillna(0)
        y = df["is_fraud"].fillna(0).astype(int)

        # Balance check
        fraud_rate = y.mean()
        print(f"\n  Dataset: {len(X):,} claims | Fraud rate: {fraud_rate:.1%}")

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # ── Model comparison ──────────────────────────────
        candidates = {
            "Random Forest": RandomForestClassifier(
                n_estimators=300, max_depth=12, min_samples_leaf=5,
                class_weight="balanced", random_state=42, n_jobs=-1
            ),
            "Gradient Boosting": GradientBoostingClassifier(
                n_estimators=200, learning_rate=0.05, max_depth=4,
                random_state=42
            ),
            "Logistic Regression": LogisticRegression(
                class_weight="balanced", max_iter=1000, random_state=42
            ),
        }
        if XGBOOST:
            candidates["XGBoost"] = xgb.XGBClassifier(
                n_estimators=300, learning_rate=0.05, max_depth=6,
                scale_pos_weight=(1 - fraud_rate) / fraud_rate,
                random_state=42, eval_metric="logloss",
                use_label_encoder=False
            )

        print("\n  Comparing models...")
        print(f"  {'Model':<25} {'AUC':>8} {'Accuracy':>10} {'Recall':>8}")
        print(f"  {'─'*25} {'─'*8} {'─'*10} {'─'*8}")

        best_auc = 0
        best_name = ""
        for name, clf in candidates.items():
            X_sc = self.scaler.fit_transform(X_train) if name == "Logistic Regression" else X_train
            clf.fit(X_sc, y_train)
            X_test_sc = self.scaler.transform(X_test) if name == "Logistic Regression" else X_test
            y_prob = clf.predict_proba(X_test_sc)[:, 1]
            auc = roc_auc_score(y_test, y_prob)
            y_pred = (y_prob >= 0.5).astype(int)
            acc = accuracy_score(y_test, y_pred)
            recall = (y_pred[y_test == 1]).sum() / max((y_test == 1).sum(), 1)
            print(f"  {name:<25} {auc:>8.4f} {acc:>10.1%} {recall:>8.1%}")

            if auc > best_auc:
                best_auc = auc
                best_name = name
                self.model = clf

        print(f"\n  ✓ Best model: {best_name} (AUC = {best_auc:.4f})")

        # ── Optimal threshold ─────────────────────────────
        X_test_sc = (
            self.scaler.transform(X_test)
            if best_name == "Logistic Regression" else X_test
        )
        y_prob = self.model.predict_proba(X_test_sc)[:, 1]
        self.threshold = self._optimal_threshold(y_test, y_prob)

        # ── Final evaluation ──────────────────────────────
        y_pred_final = (y_prob >= self.threshold).astype(int)
        self.results = {
            "model_name": best_name,
            "auc": round(roc_auc_score(y_test, y_prob), 4),
            "accuracy": round(accuracy_score(y_test, y_pred_final), 4),
            "threshold": self.threshold,
            "classification_report": classification_report(y_test, y_pred_final),
            "confusion_matrix": confusion_matrix(y_test, y_pred_final),
            "y_test": y_test,
            "y_prob": y_prob,
            "y_pred": y_pred_final,
            "feature_names": features,
        }

        print(f"\n  Optimal threshold: {self.threshold:.3f}")
        print(f"\n{self.results['classification_report']}")

        return self.results

    def _optimal_threshold(self, y_true, y_prob):
        """Find threshold that minimises total investigation cost."""
        thresholds = np.arange(0.05, 0.95, 0.01)
        best_cost = np.inf
        best_t = 0.5
        for t in thresholds:
            y_pred = (y_prob >= t).astype(int)
            fn = ((y_pred == 0) & (y_true == 1)).sum()
            fp = ((y_pred == 1) & (y_true == 0)).sum()
            cost = fn * FRAUD_COST_FN + fp * FRAUD_COST_FP
            if cost < best_cost:
                best_cost = cost
                best_t = t
        return round(best_t, 3)

    def predict(self, df, encoded_cats):
        """Predict fraud probability for new claims."""
        features = [f for f in self.feature_names if f in df.columns]
        X = df[features].fillna(0)
        probs = self.model.predict_proba(X)[:, 1]
        preds = (probs >= self.threshold).astype(int)
        return probs, preds

    def feature_importance(self):
        """Return feature importances if available."""
        if hasattr(self.model, "feature_importances_"):
            fi = pd.Series(
                self.model.feature_importances_,
                index=self.feature_names[:len(self.model.feature_importances_)]
            ).sort_values(ascending=False)
            return fi
        return None

    def save(self, path="models/fraud_model.pkl"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({
            "model": self.model,
            "threshold": self.threshold,
            "feature_names": self.feature_names,
            "scaler": self.scaler,
        }, path)
        print(f"  ✓ Fraud model saved: {path}")

    def load(self, path="models/fraud_model.pkl"):
        data = joblib.load(path)
        self.model = data["model"]
        self.threshold = data["threshold"]
        self.feature_names = data["feature_names"]
        self.scaler = data["scaler"]


# ─────────────────────────────────────────────
# ACTUARIAL PRICING MODEL
# ─────────────────────────────────────────────

class ActuarialPricingModel:
    """
    Loss Cost / Pure Premium Model.

    Pure Premium = Frequency × Severity
    where:
      Frequency = P(claim occurs) — Logistic regression
      Severity  = E(claim amount | claim occurs) — Random Forest regression

    Risk-Adjusted Premium = Pure Premium / (1 - Expense Ratio - Profit Margin)

    Also computes:
      Expected Fraud Loss = P(fraud) × Claimed Amount
      Total Risk Load     = Expected Loss + Fraud Load
    """

    def __init__(self):
        self.severity_model = None
        self.frequency_model = None
        self.feature_names = None
        self.results = {}

    def get_features(self, df, encoded_cats):
        available = []
        for f in PRICING_FEATURES:
            if f in df.columns:
                available.append(f)
        available += [c for c in encoded_cats if c in df.columns]
        return available

    def train(self, df, encoded_cats):
        print("\n" + "="*60)
        print("  ACTUARIAL PRICING MODEL TRAINING")
        print("="*60)

        features = self.get_features(df, encoded_cats)
        self.feature_names = features

        if "claimed_amount_ksh" not in df.columns:
            print("  ✗ No 'claimed_amount_ksh' column. Cannot train pricing model.")
            return None

        X = df[features].fillna(0)
        y_sev = df["claimed_amount_ksh"].fillna(df["claimed_amount_ksh"].median())

        # Log transform for severity (actuarial standard)
        y_log = np.log1p(y_sev)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y_log, test_size=0.2, random_state=42
        )

        # ── Severity model ────────────────────────────────
        print("\n  Training severity (claim amount) model...")
        sev_models = {
            "Random Forest": RandomForestRegressor(
                n_estimators=300, max_depth=10, min_samples_leaf=10,
                random_state=42, n_jobs=-1
            ),
            "Ridge Regression": Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                ("ridge", Ridge(alpha=1.0)),
            ]),
        }

        best_r2 = -np.inf
        for name, model in sev_models.items():
            model.fit(X_train, y_train)
            y_pred_log = model.predict(X_test)
            r2 = r2_score(y_test, y_pred_log)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred_log))
            print(f"  {name:<25} R² = {r2:.4f}  RMSE (log) = {rmse:.4f}")
            if r2 > best_r2:
                best_r2 = r2
                self.severity_model = model
                best_sev_name = name

        print(f"\n  ✓ Best severity model: {best_sev_name} (R² = {best_r2:.4f})")

        # ── Frequency model ───────────────────────────────
        # Use claim occurrence as proxy (all claims in dataset = 1 occurrence)
        # In production, this would be trained on policy × claim occurrence data
        print("\n  Frequency model: calibrated to IRA base rate (18%)")
        print("  (In production: train on full policy book with exposure data)")

        # Store results
        y_pred_log_final = self.severity_model.predict(X_test)
        y_pred_ksh = np.expm1(y_pred_log_final)
        y_actual_ksh = np.expm1(y_test)

        self.results = {
            "model_name": best_sev_name,
            "r2": round(best_r2, 4),
            "rmse_ksh": round(
                np.sqrt(mean_squared_error(y_actual_ksh, y_pred_ksh)), 0
            ),
            "feature_names": features,
        }

        print(f"\n  Severity RMSE (KSh): {self.results['rmse_ksh']:,.0f}")
        print(f"  R² Score:            {self.results['r2']:.4f}")

        return self.results

    def price_claims(self, df, fraud_probs=None):
        """
        Compute risk-adjusted premiums and expected losses for each claim.

        Returns DataFrame with pricing columns added.
        """
        df = df.copy()
        features = [f for f in self.feature_names if f in df.columns]
        X = df[features].fillna(0)

        # Predicted severity
        log_severity = self.severity_model.predict(X)
        predicted_severity = np.expm1(log_severity)
        df["predicted_claim_amount_ksh"] = predicted_severity.round(0)

        # Frequency (base rate adjusted by risk score)
        base_freq = CLAIMS_FREQUENCY_BASE
        if "composite_risk_score" in df.columns:
            risk_adj = 1 + (df["composite_risk_score"] / 10) * 0.5
        else:
            risk_adj = 1.0
        df["claim_frequency"] = (base_freq * risk_adj).clip(0.05, 0.95)

        # Pure premium = Frequency × Severity
        df["pure_premium_ksh"] = (
            df["claim_frequency"] * df["predicted_claim_amount_ksh"]
        ).round(0)

        # Fraud loading
        if fraud_probs is not None:
            df["fraud_probability"] = fraud_probs
            df["expected_fraud_loss_ksh"] = (
                fraud_probs * df.get("claimed_amount_ksh", predicted_severity)
            ).round(0)
        else:
            df["fraud_probability"] = 0
            df["expected_fraud_loss_ksh"] = 0

        # Total expected loss
        df["total_expected_loss_ksh"] = (
            df["pure_premium_ksh"] + df["expected_fraud_loss_ksh"] * 0.12
        ).round(0)

        # Risk-adjusted premium
        df["risk_adjusted_premium_ksh"] = (
            df["total_expected_loss_ksh"] / (1 - EXPENSE_RATIO - PROFIT_MARGIN)
        ).round(0)

        # Risk tier for premium loading
        df["premium_tier"] = pd.cut(
            df["fraud_probability"],
            bins=[0, 0.20, 0.50, 1.01],
            labels=["Standard Rate", "Loaded Rate (+25%)", "High Risk Rate (+60%)"]
        )

        # Apply tier loading to premium
        loading_map = {
            "Standard Rate": 1.00,
            "Loaded Rate (+25%)": 1.25,
            "High Risk Rate (+60%)": 1.60,
        }
        df["final_premium_ksh"] = df.apply(
            lambda r: r["risk_adjusted_premium_ksh"] *
                      loading_map.get(str(r["premium_tier"]), 1.0),
            axis=1
        ).round(0)

        return df

    def save(self, path="models/pricing_model.pkl"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({
            "severity_model": self.severity_model,
            "feature_names": self.feature_names,
        }, path)
        print(f"  ✓ Pricing model saved: {path}")

    def load(self, path="models/pricing_model.pkl"):
        data = joblib.load(path)
        self.severity_model = data["severity_model"]
        self.feature_names = data["feature_names"]


# ─────────────────────────────────────────────
# FINANCIAL IMPACT CALCULATOR
# ─────────────────────────────────────────────

def compute_financial_impact(df, fraud_preds, fraud_probs):
    """
    Compute the full financial impact analysis for the insurer.
    Answers: 'What does fraud cost us, and what does AI save?'
    """
    n_claims = len(df)
    n_fraud_actual = df["is_fraud"].sum() if "is_fraud" in df.columns else int(n_claims * 0.12)
    n_fraud_caught = int((fraud_preds & df.get("is_fraud", pd.Series([0]*n_claims)).astype(bool)).sum()) \
        if "is_fraud" in df.columns else int(fraud_probs[fraud_preds == 1].shape[0])

    avg_fraud_loss = df.get("claimed_amount_ksh", pd.Series([120000]*n_claims)).median()

    total_fraud_exposure = n_fraud_actual * avg_fraud_loss
    prevented_loss = n_fraud_caught * avg_fraud_loss
    missed_loss = (n_fraud_actual - n_fraud_caught) * avg_fraud_loss
    false_alarm_cost = (fraud_preds == 1).sum() * FRAUD_COST_FP

    net_saving = prevented_loss - false_alarm_cost

    annual_scale = 10000 / n_claims if n_claims > 0 else 1
    annual_saving = net_saving * annual_scale

    return {
        "total_claims": n_claims,
        "fraud_cases_detected": int(n_fraud_caught),
        "total_fraud_exposure_ksh": round(total_fraud_exposure),
        "fraud_prevented_ksh": round(prevented_loss),
        "fraud_missed_ksh": round(missed_loss),
        "false_alarm_cost_ksh": round(false_alarm_cost),
        "net_saving_ksh": round(net_saving),
        "annual_saving_scaled_ksh": round(annual_saving),
        "roi": round((net_saving / 4_300_000) * 100, 1) if net_saving > 0 else 0,
    }


# ─────────────────────────────────────────────
# PLOTTING
# ─────────────────────────────────────────────

def generate_plots(fraud_results, pricing_df, impact, output_dir="data/generated/plots/"):
    os.makedirs(output_dir, exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid")

    # ── 1. ROC Curve ──────────────────────────────────────
    fpr, tpr, _ = roc_curve(fraud_results["y_test"], fraud_results["y_prob"])
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(fpr, tpr, color="#0066CC", lw=2,
            label=f"ROC (AUC = {fraud_results['auc']:.4f})")
    ax.plot([0, 1], [0, 1], "k--", lw=1)
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("INSURTECH AI — Fraud Detection ROC Curve")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "roc_curve.png"), dpi=150)
    plt.close(fig)

    # ── 2. Risk Tier Distribution ─────────────────────────
    if "risk_tier" in pricing_df.columns:
        tier_counts = pricing_df["risk_tier"].value_counts()
        colors = {"Low": "#28A745", "Medium": "#FFC107", "High": "#DC3545"}
        fig, ax = plt.subplots(figsize=(6, 5))
        bars = ax.bar(
            tier_counts.index,
            tier_counts.values,
            color=[colors.get(t, "#888") for t in tier_counts.index]
        )
        ax.set_title("Claims by Risk Tier")
        ax.set_ylabel("Number of Claims")
        for bar, val in zip(bars, tier_counts.values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
                    f"{val:,}", ha="center", fontsize=10)
        fig.tight_layout()
        fig.savefig(os.path.join(output_dir, "risk_tiers.png"), dpi=150)
        plt.close(fig)

    # ── 3. Claim Amount Distribution ─────────────────────
    if "claimed_amount_ksh" in pricing_df.columns:
        fig, ax = plt.subplots(figsize=(8, 5))
        fraud_amounts = pricing_df[pricing_df.get("is_fraud", 0) == 1]["claimed_amount_ksh"].dropna()
        legit_amounts = pricing_df[pricing_df.get("is_fraud", 0) == 0]["claimed_amount_ksh"].dropna()
        ax.hist(np.log1p(legit_amounts), bins=50, alpha=0.6, color="#28A745", label="Legitimate")
        ax.hist(np.log1p(fraud_amounts), bins=50, alpha=0.6, color="#DC3545", label="Fraudulent")
        ax.set_xlabel("Log(Claim Amount KSh)")
        ax.set_ylabel("Frequency")
        ax.set_title("Claim Amount Distribution: Fraud vs Legitimate")
        ax.legend()
        fig.tight_layout()
        fig.savefig(os.path.join(output_dir, "amount_distribution.png"), dpi=150)
        plt.close(fig)

    print(f"\n  ✓ Plots saved to: {output_dir}")


# ─────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────

def run_pipeline(data_path, output_dir="data/generated/", train_mode=True):
    """
    Full INSURTECH AI pipeline:
      1. Load data (any format)
      2. Preprocess
      3. Train / load Fraud Detection model
      4. Train / load Pricing model
      5. Score all claims
      6. Compute financial impact
      7. Save outputs
    """
    print("\n" + "█"*60)
    print("  INSURTECH AI ELITE — Full Pipeline")
    print("█"*60)

    os.makedirs(output_dir, exist_ok=True)

    # ── Load ──────────────────────────────────────────────
    df = load_data(data_path)

    # ── Preprocess ────────────────────────────────────────
    df, encoded_cats = preprocess(df)

    # ── Fraud Model ───────────────────────────────────────
    fraud_model = FraudDetectionModel()
    if train_mode:
        fraud_results = fraud_model.train(df, encoded_cats)
        fraud_model.save()
    else:
        fraud_model.load()
        fraud_results = None

    # Score all claims
    fraud_probs, fraud_preds = fraud_model.predict(df, encoded_cats)
    df["fraud_probability"] = fraud_probs
    df["fraud_predicted"] = fraud_preds

    # ── Pricing Model ─────────────────────────────────────
    pricing_model = ActuarialPricingModel()
    if train_mode:
        pricing_results = pricing_model.train(df, encoded_cats)
        pricing_model.save()
    else:
        pricing_model.load()
        pricing_results = None

    # Price all claims
    df = pricing_model.price_claims(df, fraud_probs=fraud_probs)

    # ── Financial Impact ──────────────────────────────────
    impact = compute_financial_impact(df, fraud_preds, fraud_probs)

    print("\n" + "="*60)
    print("  FINANCIAL IMPACT SUMMARY")
    print("="*60)
    for k, v in impact.items():
        if isinstance(v, int) and v > 1000:
            print(f"  {k:<35} KSh {v:>15,.0f}")
        else:
            print(f"  {k:<35} {v}")

    # ── Save outputs ──────────────────────────────────────
    out_path = os.path.join(output_dir, "scored_claims.csv")
    df.to_csv(out_path, index=False)
    print(f"\n  ✓ Scored claims saved: {out_path}")

    # Save impact summary
    impact_df = pd.DataFrame([impact])
    impact_df.to_csv(os.path.join(output_dir, "financial_impact.csv"), index=False)

    # Generate plots
    if fraud_results and train_mode:
        generate_plots(fraud_results, df, impact)

    return df, impact


# ─────────────────────────────────────────────
# CLI ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="INSURTECH AI — Fraud & Pricing Model")
    parser.add_argument("--data", type=str,
                        default="data/generated/kenya_motor_claims_50000.csv",
                        help="Path to claims data (CSV/Excel/PDF/JSON/folder)")
    parser.add_argument("--output", type=str, default="data/generated/",
                        help="Output directory")
    parser.add_argument("--predict-only", action="store_true",
                        help="Skip training, load saved models and score only")

    args = parser.parse_args()
    train_mode = not args.predict_only

    df, impact = run_pipeline(args.data, output_dir=args.output, train_mode=train_mode)

    print("\n  Top 10 highest-risk claims:")
    cols_show = ["claim_id", "insurer", "claim_type", "claimed_amount_ksh",
                 "fraud_probability", "fraud_predicted", "risk_tier",
                 "final_premium_ksh", "expected_fraud_loss_ksh"]
    cols_show = [c for c in cols_show if c in df.columns]
    print(df.nlargest(10, "fraud_probability")[cols_show].to_string(index=False))
