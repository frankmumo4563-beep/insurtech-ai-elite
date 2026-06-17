"""
INSURTECH AI ELITE — Universal Data Ingestion Engine
=====================================================
Author: Frank Mumo | University of Nairobi | 2026

Accepts ANY of these formats and converts to standard CSV:
  - CSV files (.csv)
  - Excel files (.xlsx, .xls)
  - PDF claim forms (.pdf) — both structured tables and scanned forms
  - JSON files (.json)

Usage:
    python ingest.py --input path/to/file.pdf
    python ingest.py --input path/to/claims.xlsx
    python ingest.py --folder data/raw/   ← batch process all files in folder
"""

import os
import sys
import json
import argparse
import re
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd

# PDF processing
try:
    import pdfplumber
    PDF_PLUMBER = True
except ImportError:
    PDF_PLUMBER = False
    print("[WARN] pdfplumber not installed. Run: pip install pdfplumber")

try:
    import PyPDF2
    PYPDF2 = True
except ImportError:
    PYPDF2 = False

# Excel
try:
    import openpyxl
    OPENPYXL = True
except ImportError:
    OPENPYXL = False


# ─────────────────────────────────────────────
# STANDARD COLUMN SCHEMA
# (all ingested files are normalized to this)
# ─────────────────────────────────────────────
STANDARD_COLUMNS = [
    "claim_id", "insurer", "claim_type", "policy_number",
    "insured_id", "insured_age", "insured_gender", "insured_occupation",
    "county", "accident_date", "accident_time", "accident_hour",
    "night_incident", "police_report_filed", "police_station",
    "weather_conditions", "road_surface_condition", "reported_speed_kmh",
    "vehicle_make", "vehicle_model", "vehicle_year", "vehicle_age",
    "vehicle_reg", "engine_cc", "vehicle_use",
    "driver_age", "driver_gender", "driver_years_experience",
    "driver_license_valid", "driver_prior_accidents",
    "independent_witnesses", "witness_count",
    "other_vehicle_involved", "third_party_vehicles_count",
    "passengers_in_vehicle", "persons_injured",
    "claimed_amount_ksh", "garage_estimate_ksh", "settlement_amount_ksh",
    "excess_deductible_ksh", "sum_insured_ksh",
    "prior_claims_12m", "is_fraud",
]

# Mapping of common alternative column names → standard names
COLUMN_ALIASES = {
    # Insured / policy holder
    "name of insured": "insured_name",
    "full name of insured": "insured_name",
    "policy no": "policy_number",
    "policy number": "policy_number",
    "policy no.": "policy_number",
    "id/certificate of incorporation": "insured_id",
    "id no": "insured_id",
    "id no.": "insured_id",
    "pin no": "pin_number",
    "occupation/nature of business": "insured_occupation",
    "business/occupation": "insured_occupation",

    # Vehicle
    "make/model": "vehicle_make_model",
    "make & model": "vehicle_make_model",
    "when was the vehicle manufactured": "vehicle_year",
    "year of manufacture": "vehicle_year",
    "vehicle registration no": "vehicle_reg",
    "reg. no of vehicle": "vehicle_reg",
    "reg. no. of vehicle": "vehicle_reg",
    "hp/cc": "engine_cc",
    "carrying capacity": "carrying_capacity",

    # Driver
    "driver's date of birth": "driver_dob",
    "actual date of birth": "driver_dob",
    "how long has the driver been driving": "driver_years_experience",
    "how long has he been driving motor vehicle": "driver_years_experience",
    "was the driver in anyway to blame": "driver_at_fault",
    "was he in any way to blame for the accident": "driver_at_fault",
    "did the driver admit liability": "driver_admitted_liability",
    "did he admit liability": "driver_admitted_liability",
    "has the driver had previous accidents": "driver_prior_accidents",
    "has he had any previous accident": "driver_prior_accidents",

    # Accident
    "when did the accident occur": "accident_date",
    "time of accident": "accident_time",
    "place of accident": "accident_location",
    "type of road surface": "road_surface_condition",
    "estimated speed before accident": "reported_speed_kmh",
    "weather conditions": "weather_conditions",
    "did police take particulars": "police_report_filed",
    "to which police station": "police_station",
    "what lights were showing": "lights_showing",

    # Claim amounts
    "claimed amount": "claimed_amount_ksh",
    "amount claimed": "claimed_amount_ksh",
    "claim amount": "claimed_amount_ksh",
    "estimate for repairs": "garage_estimate_ksh",
    "settlement": "settlement_amount_ksh",
    "sum insured": "sum_insured_ksh",
    "excess": "excess_deductible_ksh",
}


# ─────────────────────────────────────────────
# FORMAT DETECTORS
# ─────────────────────────────────────────────

def detect_format(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".csv":
        return "csv"
    elif ext in [".xlsx", ".xls"]:
        return "excel"
    elif ext == ".pdf":
        return "pdf"
    elif ext == ".json":
        return "json"
    else:
        return "unknown"


# ─────────────────────────────────────────────
# READERS
# ─────────────────────────────────────────────

def read_csv(file_path):
    """Read CSV — try multiple encodings and delimiters."""
    for encoding in ["utf-8", "latin-1", "cp1252"]:
        for sep in [",", ";", "\t"]:
            try:
                df = pd.read_csv(file_path, encoding=encoding, sep=sep, low_memory=False)
                if df.shape[1] > 1:
                    print(f"  ✓ CSV read: {df.shape[0]:,} rows × {df.shape[1]} columns")
                    return df
            except Exception:
                continue
    raise ValueError(f"Could not parse CSV: {file_path}")


def read_excel(file_path):
    """Read Excel — tries all sheets, picks the largest."""
    xl = pd.ExcelFile(file_path)
    best_df = None
    best_size = 0
    for sheet in xl.sheet_names:
        try:
            df = xl.parse(sheet)
            if df.size > best_size:
                best_df = df
                best_size = df.size
        except Exception:
            continue
    if best_df is not None:
        print(f"  ✓ Excel read: {best_df.shape[0]:,} rows × {best_df.shape[1]} columns")
        return best_df
    raise ValueError(f"Could not read Excel: {file_path}")


def read_json(file_path):
    """Read JSON — handles records or list format."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        df = pd.DataFrame(data)
    elif isinstance(data, dict):
        # Try common nested patterns
        for key in ["claims", "data", "records", "results"]:
            if key in data and isinstance(data[key], list):
                df = pd.DataFrame(data[key])
                break
        else:
            df = pd.DataFrame([data])
    print(f"  ✓ JSON read: {df.shape[0]:,} rows × {df.shape[1]} columns")
    return df


def read_pdf(file_path):
    """
    Read PDF claim forms.
    Strategy:
      1. Try pdfplumber for structured tables
      2. Fall back to text extraction + field parsing
    Returns a DataFrame with extracted fields.
    """
    print(f"  ℹ Reading PDF: {os.path.basename(file_path)}")

    extracted_records = []

    # ── STRATEGY 1: Table extraction ─────────────────────
    if PDF_PLUMBER:
        try:
            with pdfplumber.open(file_path) as pdf:
                all_tables = []
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        if table and len(table) > 1:
                            all_tables.append(table)

                if all_tables:
                    # Flatten tables into DataFrame
                    for table in all_tables:
                        headers = [str(h).strip().lower() if h else "" for h in table[0]]
                        for row in table[1:]:
                            if any(cell for cell in row if cell):
                                record = dict(zip(headers, [str(c).strip() if c else "" for c in row]))
                                extracted_records.append(record)

                    if extracted_records:
                        df = pd.DataFrame(extracted_records)
                        print(f"  ✓ PDF tables extracted: {df.shape[0]} records")
                        return normalize_columns(df)

        except Exception as e:
            print(f"  ⚠ Table extraction failed: {e}")

    # ── STRATEGY 2: Text field parsing ───────────────────
    raw_text = extract_pdf_text(file_path)
    if raw_text:
        record = parse_claim_form_text(raw_text)
        if record:
            df = pd.DataFrame([record])
            print(f"  ✓ PDF text parsed: {df.shape[1]} fields extracted")
            return normalize_columns(df)

    # ── STRATEGY 3: Return empty template ────────────────
    print("  ⚠ PDF parsing yielded no structured data.")
    print("    Returning empty template — fill in manually or use CSV input.")
    return pd.DataFrame(columns=STANDARD_COLUMNS)


def extract_pdf_text(file_path):
    """Extract raw text from PDF."""
    text = ""

    if PDF_PLUMBER:
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        text += t + "\n"
            if text.strip():
                return text
        except Exception:
            pass

    if PYPDF2:
        try:
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    t = page.extract_text()
                    if t:
                        text += t + "\n"
            return text
        except Exception:
            pass

    return text


def parse_claim_form_text(text):
    """
    Parse free-form claim form text into structured fields.
    Uses regex patterns for common Kenyan motor claim form fields.
    """
    record = {}
    lines = text.split("\n")

    # Key-value patterns
    patterns = {
        "policy_number": r"policy\s*no[.:]?\s*([A-Z0-9/\-]+)",
        "vehicle_reg": r"reg(?:istration)?\s*no[.:]?\s*([A-Z]{2,3}\s*\d{3}[A-Z]?)",
        "claimed_amount_ksh": r"(?:claim|amount|ksh|kes)[:\s]+([0-9,]+)",
        "accident_date": r"(?:date of accident|when did).*?(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
        "accident_time": r"time.*?(\d{1,2}:\d{2}\s*(?:am|pm)?)",
        "reported_speed_kmh": r"speed.*?(\d+)\s*km",
        "police_station": r"police\s*station[:\s]+([A-Za-z\s]+?)(?:\n|$)",
        "vehicle_make": r"make[/\s]*model[:\s]+([A-Za-z]+)",
        "vehicle_year": r"(?:manufactured|year)[:\s]+(\d{4})",
        "engine_cc": r"(?:hp|cc|engine)[:\s]+(\d+)",
    }

    text_lower = text.lower()
    for field, pattern in patterns.items():
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            value = match.group(1).strip().replace(",", "")
            # Try numeric conversion
            try:
                record[field] = float(value)
            except ValueError:
                record[field] = value

    # Boolean fields
    def find_yes_no(keyword):
        idx = text_lower.find(keyword)
        if idx == -1:
            return None
        snippet = text_lower[idx:idx+100]
        if "yes" in snippet:
            return True
        elif "no" in snippet:
            return False
        return None

    record["police_report_filed"] = find_yes_no("police take particulars")
    record["driver_license_valid"] = find_yes_no("full or provisional licence")
    record["other_vehicle_involved"] = find_yes_no("other vehicle")

    return {k: v for k, v in record.items() if v is not None}


# ─────────────────────────────────────────────
# NORMALIZATION
# ─────────────────────────────────────────────

def normalize_columns(df):
    """
    Rename columns using COLUMN_ALIASES mapping.
    Standardize data types.
    """
    # Lowercase and strip column names
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Apply aliases
    rename_map = {}
    for col in df.columns:
        col_clean = col.strip().lower().rstrip("?.:*")
        if col_clean in COLUMN_ALIASES:
            rename_map[col] = COLUMN_ALIASES[col_clean]
    df = df.rename(columns=rename_map)

    # Add missing standard columns as NaN
    for col in STANDARD_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan

    # Type coercions
    numeric_cols = [
        "claimed_amount_ksh", "garage_estimate_ksh", "settlement_amount_ksh",
        "sum_insured_ksh", "excess_deductible_ksh", "reported_speed_kmh",
        "driver_age", "vehicle_year", "engine_cc", "witness_count",
        "passengers_in_vehicle", "persons_injured", "prior_claims_12m",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(",", "").str.extract(r"(\d+\.?\d*)")[0],
                errors="coerce"
            )

    # Derive engineered features if base fields exist
    df = engineer_features(df)

    return df


def engineer_features(df):
    """Add the same engineered fraud-detection features as the simulator."""

    if "accident_hour" not in df.columns or df["accident_hour"].isna().all():
        if "accident_time" in df.columns:
            df["accident_hour"] = pd.to_datetime(
                df["accident_time"], format="%H:%M", errors="coerce"
            ).dt.hour

    if "accident_hour" in df.columns:
        df["night_incident_flag"] = (
            (df["accident_hour"] >= 22) | (df["accident_hour"] <= 5)
        ).astype(int)

    if "driver_age" in df.columns:
        df["young_driver_flag"] = (df["driver_age"] < 25).astype(int)

    if "police_report_filed" in df.columns:
        df["no_police_flag"] = (~df["police_report_filed"].astype(bool)).astype(int)

    if "independent_witnesses" in df.columns:
        df["no_witness_flag"] = (~df["independent_witnesses"].astype(bool)).astype(int)

    if "vehicle_year" in df.columns:
        df["vehicle_age"] = 2026 - df["vehicle_year"]

    if "claimed_amount_ksh" in df.columns and "garage_estimate_ksh" in df.columns:
        df["amount_to_estimate_ratio"] = (
            df["claimed_amount_ksh"] / df["garage_estimate_ksh"].replace(0, np.nan)
        ).round(4)

    return df


def add_claim_ids(df, prefix="CLM"):
    """Add claim IDs if missing."""
    if "claim_id" not in df.columns or df["claim_id"].isna().all():
        df["claim_id"] = [f"{prefix}{str(i+1).zfill(6)}" for i in range(len(df))]
    return df


# ─────────────────────────────────────────────
# MAIN INGEST FUNCTION
# ─────────────────────────────────────────────

def ingest_file(file_path, output_dir="data/raw/processed/"):
    """
    Ingest a single file (CSV/Excel/PDF/JSON) → standardized CSV.

    Returns
    -------
    pd.DataFrame
    """
    print(f"\n{'─'*50}")
    print(f"  Ingesting: {os.path.basename(file_path)}")

    fmt = detect_format(file_path)
    print(f"  Format detected: {fmt.upper()}")

    if fmt == "csv":
        df = read_csv(file_path)
    elif fmt == "excel":
        df = read_excel(file_path)
    elif fmt == "pdf":
        df = read_pdf(file_path)
    elif fmt == "json":
        df = read_json(file_path)
    else:
        print(f"  ✗ Unsupported format: {fmt}")
        return None

    df = normalize_columns(df)
    df = add_claim_ids(df)

    # Save standardized CSV
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    out_path = os.path.join(output_dir, f"{base_name}_standardized.csv")
    df.to_csv(out_path, index=False)
    print(f"  ✓ Saved standardized CSV: {out_path}")
    print(f"  ✓ Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")

    return df


def ingest_folder(folder_path, output_dir="data/raw/processed/"):
    """
    Batch ingest all supported files in a folder.
    Concatenates into one combined dataset.
    """
    supported_exts = [".csv", ".xlsx", ".xls", ".pdf", ".json"]
    files = [
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if os.path.splitext(f)[1].lower() in supported_exts
    ]

    if not files:
        print(f"  No supported files found in: {folder_path}")
        return None

    print(f"\n  Found {len(files)} file(s) to process...")
    dfs = []
    for f in files:
        df = ingest_file(f, output_dir=output_dir)
        if df is not None and not df.empty:
            dfs.append(df)

    if dfs:
        combined = pd.concat(dfs, ignore_index=True)
        combined_path = os.path.join(output_dir, "combined_claims.csv")
        combined.to_csv(combined_path, index=False)
        print(f"\n  ✓ Combined dataset: {combined.shape[0]:,} rows")
        print(f"  ✓ Saved to: {combined_path}")
        return combined

    return None


# ─────────────────────────────────────────────
# CLI ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="INSURTECH AI — Universal Data Ingestion Engine"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input", type=str, help="Path to a single file (CSV/PDF/Excel/JSON)")
    group.add_argument("--folder", type=str, help="Path to folder for batch processing")
    parser.add_argument("--output", type=str, default="data/raw/processed/", help="Output directory")

    args = parser.parse_args()

    if args.input:
        df = ingest_file(args.input, output_dir=args.output)
        if df is not None:
            print("\n  Preview:")
            print(df.head(5).to_string(index=False))
    elif args.folder:
        df = ingest_folder(args.folder, output_dir=args.output)
