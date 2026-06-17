"""
INSURTECH AI ELITE — Executive Risk Command Center
Author : Frank Mumo | University of Nairobi | 2026
Run    : streamlit run dashboard/app.py
"""

import os, warnings
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
warnings.filterwarnings("ignore")

# ═══════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════
st.set_page_config(
    page_title="INSURTECH AI ELITE",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════
# CSS
# ═══════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Space+Mono:wght@400;700&family=Inter:wght@300;400;500;600&display=swap');

:root{
  --bg:     #040D1C;
  --bg2:    #071226;
  --card:   #0C1A30;
  --card2:  #112040;
  --border: #1A2E4A;
  --blue:   #1A6DFF;
  --cyan:   #00CFFF;
  --green:  #00E5A0;
  --amber:  #FFB020;
  --red:    #FF3B5C;
  --purple: #9B5DE5;
  --t1:     #EEF4FF;
  --t2:     #7A9AC0;
  --t3:     #3A5A80;
}

html,body,.stApp{
  background:var(--bg) !important;
  font-family:'Inter',sans-serif;
  color:var(--t1);
}
/* Force sidebar open via JS workaround */
section[data-testid="stSidebar"][aria-expanded="false"]{
  width:300px !important;
  transform:none !important;
  margin-left:0 !important;
}
section[data-testid="stSidebar"][aria-expanded="true"]{
  width:300px !important;
}

#MainMenu,footer,header{visibility:hidden}
.block-container{padding:0 !important;max-width:100% !important}
.main .block-container{padding:1.5rem 2rem 3rem !important;max-width:100% !important}

/* ── SIDEBAR — always visible, never collapse ── */
[data-testid="stSidebar"]{
  background:var(--bg2) !important;
  border-right:1px solid var(--border) !important;
  width:300px !important;
  min-width:300px !important;
  max-width:300px !important;
  display:flex !important;
  flex-direction:column !important;
  visibility:visible !important;
  transform:none !important;
}
[data-testid="stSidebar"] > div {
  width:300px !important;
  min-width:300px !important;
}
[data-testid="stSidebar"] *{color:var(--t1) !important}
[data-testid="stSidebarContent"]{padding:1.2rem 1rem !important; width:300px !important;}
/* Hide collapse/expand arrow completely */
[data-testid="collapsedControl"]{display:none !important}
[data-testid="stSidebarCollapseButton"]{display:none !important}
button[data-testid="baseButton-header"]{display:none !important}
/* Make file uploader visible */
[data-testid="stFileUploader"]{
  background:var(--card) !important;
  border:1px dashed var(--border) !important;
  border-radius:10px !important;
  padding:0.5rem !important;
}
[data-testid="stFileUploaderDropzone"]{
  background:var(--card) !important;
  border:1px dashed #1A6DFF !important;
  border-radius:8px !important;
}

.kcard{
  background:linear-gradient(140deg,var(--card),var(--card2));
  border:1px solid var(--border);
  border-radius:14px;
  padding:1.2rem 1.4rem 1rem;
  position:relative;overflow:hidden;
  transition:transform .18s,box-shadow .18s;
  margin-bottom:0;
}
.kcard:hover{transform:translateY(-3px);box-shadow:0 10px 36px rgba(0,0,0,.5)}
.kcard::after{
  content:'';position:absolute;top:0;left:0;right:0;height:3px;
  border-radius:14px 14px 0 0;
}
.kcard.blue::after  {background:linear-gradient(90deg,var(--blue),var(--cyan))}
.kcard.green::after {background:linear-gradient(90deg,var(--green),#00B888)}
.kcard.red::after   {background:linear-gradient(90deg,var(--red),#FF8FA0)}
.kcard.amber::after {background:linear-gradient(90deg,var(--amber),#FFD580)}
.kcard.purple::after{background:linear-gradient(90deg,var(--purple),#C77DFF)}
.kcard.cyan::after  {background:linear-gradient(90deg,var(--cyan),var(--blue))}

.kicon{font-size:1.5rem;margin-bottom:.5rem;display:block}
.klabel{
  font-family:'Syne',sans-serif;font-size:.6rem;font-weight:700;
  letter-spacing:.13em;text-transform:uppercase;color:var(--t3);margin-bottom:.25rem;
}
.kvalue{
  font-family:'Space Mono',monospace;font-size:1.65rem;font-weight:700;
  color:var(--t1);line-height:1.05;
}
.ksub{font-size:.7rem;color:var(--t2);margin-top:.28rem}
.kbadge{
  display:inline-block;font-size:.62rem;font-weight:700;padding:.15rem .55rem;
  border-radius:999px;margin-top:.4rem;font-family:'Syne',sans-serif;letter-spacing:.05em;
}
.bg{background:rgba(0,229,160,.13);color:var(--green)}
.br{background:rgba(255,59,92,.13);color:var(--red)}
.ba{background:rgba(255,176,32,.13);color:var(--amber)}
.bb{background:rgba(0,207,255,.13);color:var(--cyan)}

.sh{
  font-family:'Syne',sans-serif;font-size:.6rem;font-weight:800;
  letter-spacing:.15em;text-transform:uppercase;color:var(--t3);
  padding-bottom:.5rem;border-bottom:1px solid var(--border);margin-bottom:.9rem;
}

.stTabs [data-baseweb="tab-list"]{
  background:transparent !important;border-bottom:1px solid var(--border) !important;gap:.2rem;
}
.stTabs [data-baseweb="tab"]{
  background:transparent !important;color:var(--t3) !important;
  font-family:'Syne',sans-serif !important;font-size:.72rem !important;
  font-weight:700 !important;letter-spacing:.08em !important;
  text-transform:uppercase;padding:.55rem 1.1rem !important;
  border-radius:8px 8px 0 0 !important;
}
.stTabs [aria-selected="true"]{
  background:var(--card) !important;color:var(--cyan) !important;
  border-bottom:2px solid var(--cyan) !important;
}

.abox{
  background:var(--card);border:1px solid var(--border);
  border-left:4px solid var(--cyan);border-radius:12px;
  padding:1rem 1.2rem;font-size:.82rem;line-height:1.75;color:var(--t2);
}
.abox b{color:var(--t1)}

.pbar-wrap{margin-bottom:.85rem}
.pbar-row{display:flex;justify-content:space-between;margin-bottom:4px}
.pbar-name{font-size:.76rem;color:var(--t2)}
.pbar-val{font-family:'Space Mono',monospace;font-size:.7rem;color:var(--t1);font-weight:700}
.pbar-bg{background:var(--border);border-radius:4px;height:7px}
.pbar-fill{height:100%;border-radius:4px}

::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-track{background:var(--bg2)}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}

[data-testid="stDataFrame"]{border-radius:10px;overflow:hidden}

.logo-wrap{padding:.4rem 0 1.8rem}
.logo-title{
  font-family:'Syne',sans-serif;
  font-size:1.2rem;font-weight:800;
  background:linear-gradient(135deg,#00CFFF,#1A6DFF);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  letter-spacing:-.02em;
}
.logo-sub{
  font-family:'Syne',sans-serif;
  font-size:.58rem;font-weight:700;
  letter-spacing:.18em;text-transform:uppercase;
  color:var(--t3);margin-top:.15rem;
}

.upload-section{
  background:var(--card);
  border:1px dashed var(--border);
  border-radius:10px;
  padding:1rem;
  margin-bottom:1rem;
}
.upload-title{
  font-family:'Syne',sans-serif;font-size:.6rem;font-weight:700;
  letter-spacing:.13em;text-transform:uppercase;color:var(--t3);
  margin-bottom:.6rem;
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════
# PLOTLY THEME
# ═══════════════════════════════════════════════
PT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#7A9AC0", size=11),
    margin=dict(l=6, r=6, t=28, b=6),
    colorway=["#1A6DFF","#00CFFF","#00E5A0","#FFB020","#FF3B5C","#9B5DE5","#FF8FA0"],
)
GRID  = "#1A2E4A"
C = dict(blue="#1A6DFF",cyan="#00CFFF",green="#00E5A0",
         amber="#FFB020",red="#FF3B5C",purple="#9B5DE5")

# ═══════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════
def ksh(v):
    if   v >= 1e9: return f"KSh {v/1e9:.2f}B"
    elif v >= 1e6: return f"KSh {v/1e6:.1f}M"
    else:          return f"KSh {v:,.0f}"

def kpi(icon, label, val, sub="", badge="", bt="bb", color="blue"):
    b = f'<div class="kbadge {bt}">{badge}</div>' if badge else ""
    s = f'<div class="ksub">{sub}</div>' if sub else ""
    return (f'<div class="kcard {color}">'
            f'<span class="kicon">{icon}</span>'
            f'<div class="klabel">{label}</div>'
            f'<div class="kvalue">{val}</div>'
            f'{s}{b}</div>')

def sh(t):
    st.markdown(f'<div class="sh">{t}</div>', unsafe_allow_html=True)

def pbar(name, val, max_val, color):
    pct = min(val/max(max_val,1), 1.0)*100
    st.markdown(
        f'<div class="pbar-wrap">'
        f'<div class="pbar-row"><span class="pbar-name">{name}</span>'
        f'<span class="pbar-val">{ksh(val)}</span></div>'
        f'<div class="pbar-bg"><div class="pbar-fill" style="width:{pct:.1f}%;background:{color}"></div></div>'
        f'</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════
# DATA INGESTION  (CSV / Excel / PDF / Word)
# ═══════════════════════════════════════════════
def ingest_file(uploaded):
    """Convert any uploaded file into a DataFrame."""
    name = uploaded.name.lower()
    df   = None

    # ── CSV ──────────────────────────────────────
    if name.endswith(".csv"):
        for enc in ["utf-8","latin-1","cp1252"]:
            try:
                df = pd.read_csv(uploaded, encoding=enc, low_memory=False)
                break
            except Exception:
                uploaded.seek(0)

    # ── Excel ─────────────────────────────────────
    elif name.endswith((".xlsx",".xls")):
        try:
            xl  = pd.ExcelFile(uploaded)
            dfs = []
            for sheet in xl.sheet_names:
                try:
                    tmp = xl.parse(sheet)
                    if len(tmp) > 0:
                        dfs.append(tmp)
                except Exception:
                    pass
            if dfs:
                df = max(dfs, key=len)   # largest sheet
        except Exception as e:
            st.error(f"Excel read error: {e}")

    # ── PDF ───────────────────────────────────────
    elif name.endswith(".pdf"):
        try:
            import pdfplumber
            records = []
            with pdfplumber.open(uploaded) as pdf:
                for page in pdf.pages:
                    for tbl in (page.extract_tables() or []):
                        if tbl and len(tbl) > 1:
                            hdrs = [str(h).strip().lower().replace(" ","_") if h
                                    else f"col_{i}"
                                    for i,h in enumerate(tbl[0])]
                            for row in tbl[1:]:
                                if any(c for c in row if c):
                                    records.append(dict(zip(hdrs,
                                        [str(c).strip() if c else "" for c in row])))
            if records:
                df = pd.DataFrame(records)
            else:
                st.warning("No tables found in PDF. Try a CSV or Excel export.")
                return None
        except ImportError:
            st.error("Install pdfplumber: `pip install pdfplumber`")
            return None
        except Exception as e:
            st.error(f"PDF read error: {e}")
            return None

    # ── Word (.docx) ──────────────────────────────
    elif name.endswith(".docx"):
        try:
            import docx
            doc     = docx.Document(uploaded)
            records = []
            for table in doc.tables:
                if len(table.rows) < 2:
                    continue
                hdrs = [c.text.strip().lower().replace(" ","_")
                        for c in table.rows[0].cells]
                for row in table.rows[1:]:
                    vals = [c.text.strip() for c in row.cells]
                    if any(vals):
                        records.append(dict(zip(hdrs, vals)))
            if records:
                df = pd.DataFrame(records)
            else:
                st.warning("No tables found in Word document.")
                return None
        except ImportError:
            st.error("Install python-docx: `pip install python-docx`")
            return None
        except Exception as e:
            st.error(f"Word read error: {e}")
            return None
    else:
        st.error(f"Unsupported format. Use CSV, Excel, PDF or Word (.docx).")
        return None

    if df is None or len(df) == 0:
        st.error("File loaded but contained no data.")
        return None

    # ── Standardise column names ──────────────────
    ALIASES = {
        "claimed amount":        "claimed_amount_ksh",
        "claim amount":          "claimed_amount_ksh",
        "amount claimed":        "claimed_amount_ksh",
        "claim_amount":          "claimed_amount_ksh",
        "settlement":            "settlement_amount_ksh",
        "settlement amount":     "settlement_amount_ksh",
        "garage estimate":       "garage_estimate_ksh",
        "repair estimate":       "garage_estimate_ksh",
        "sum insured":           "sum_insured_ksh",
        "fraud":                 "is_fraud",
        "is fraud":              "is_fraud",
        "fraud flag":            "is_fraud",
        "fraudulent":            "is_fraud",
        "risk":                  "risk_tier",
        "risk tier":             "risk_tier",
        "risk level":            "risk_tier",
        "insurer":               "insurer",
        "insurance company":     "insurer",
        "company":               "insurer",
        "county":                "county",
        "region":                "county",
        "claim type":            "claim_type",
        "type of claim":         "claim_type",
        "claim_category":        "claim_type",
        "vehicle make":          "vehicle_make",
        "make":                  "vehicle_make",
        "car make":              "vehicle_make",
        "vehicle model":         "vehicle_model",
        "driver age":            "driver_age",
        "age of driver":         "driver_age",
        "age":                   "driver_age",
        "vehicle year":          "vehicle_year",
        "year":                  "vehicle_year",
        "policy type":           "policy_type",
        "policy number":         "policy_number",
        "policy no":             "policy_number",
        "accident date":         "accident_date",
        "date of accident":      "accident_date",
        "date":                  "accident_date",
    }
    df.columns = [
        ALIASES.get(c.strip().lower(), c.strip().lower().replace(" ","_"))
        for c in df.columns
    ]

    # ── Numeric coercions ─────────────────────────
    for col in ["claimed_amount_ksh","settlement_amount_ksh","garage_estimate_ksh",
                "sum_insured_ksh","fraud_probability_score","composite_risk_score",
                "driver_age","vehicle_age","vehicle_year","is_fraud"]:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str)
                       .str.replace(",","",regex=False)
                       .str.replace("KSh","",regex=False)
                       .str.strip(),
                errors="coerce")

    # ── Derive missing key columns ────────────────
    if "claim_id" not in df.columns:
        df["claim_id"] = [f"CLM{str(i+1).zfill(6)}" for i in range(len(df))]

    if "is_fraud" not in df.columns:
        if "fraud_probability_score" in df.columns:
            df["is_fraud"] = (df["fraud_probability_score"] >= 0.5).astype(int)
        else:
            df["is_fraud"] = 0

    if "fraud_probability_score" not in df.columns:
        df["fraud_probability_score"] = df["is_fraud"].astype(float) * 0.7 + \
                                        np.random.uniform(0, 0.3, len(df)) * (1-df["is_fraud"])

    # Always ensure expected_fraud_loss_ksh exists
    if "claimed_amount_ksh" in df.columns:
        if "expected_fraud_loss_ksh" not in df.columns or df["expected_fraud_loss_ksh"].isna().all():
            fps = df["fraud_probability_score"] if "fraud_probability_score" in df.columns else 0.12
            df["expected_fraud_loss_ksh"] = (fps * df["claimed_amount_ksh"]).round(0)
    else:
        df["expected_fraud_loss_ksh"] = 0

    if "risk_tier" not in df.columns:
        if "fraud_probability_score" in df.columns:
            df["risk_tier"] = pd.cut(df["fraud_probability_score"],
                                     bins=[-0.1,0.3,0.6,1.1],
                                     labels=["Low","Medium","High"])
        else:
            df["risk_tier"] = "Unknown"

    for col, default in [
        ("insurer","Unknown"),("claim_type","Unknown"),
        ("county","Unknown"),("vehicle_make","Unknown"),
        ("claimed_amount_ksh",0),("settlement_amount_ksh",0),
    ]:
        if col not in df.columns:
            df[col] = default

    if "accident_date" in df.columns:
        df["accident_date"] = pd.to_datetime(df["accident_date"], errors="coerce")

    df["accident_month"] = (
        df["accident_date"].dt.to_period("M").astype(str)
        if "accident_date" in df.columns and
           pd.api.types.is_datetime64_any_dtype(df.get("accident_date"))
        else "2024-01"
    )

    return df

# ═══════════════════════════════════════════════
# DEFAULT DATA LOADER
# ═══════════════════════════════════════════════
@st.cache_data(show_spinner=False)
def load_default():
    candidates = [
        "data/generated/kenya_motor_claims_50000.csv",
        "../data/generated/kenya_motor_claims_50000.csv",
        "kenya_motor_claims_50000.csv",
    ]
    for p in candidates:
        if os.path.exists(p):
            df = pd.read_csv(p, low_memory=False)
            if "accident_date" in df.columns:
                df["accident_date"] = pd.to_datetime(df["accident_date"], errors="coerce")
            df["accident_month"] = (
                df["accident_date"].dt.to_period("M").astype(str)
                if "accident_date" in df.columns else "2024-01"
            )
            if "expected_fraud_loss_ksh" not in df.columns:
                if "fraud_probability_score" in df.columns and "claimed_amount_ksh" in df.columns:
                    df["expected_fraud_loss_ksh"] = (
                        df["fraud_probability_score"]*df["claimed_amount_ksh"]).round(0)
                else:
                    df["expected_fraud_loss_ksh"] = 0
            return df
    return None

# ═══════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════
def sidebar(df):
    with st.sidebar:
        # Logo
        st.markdown("""
        <div class="logo-wrap">
          <div style="font-size:1.9rem;margin-bottom:.4rem">🛡️</div>
          <div class="logo-title">INSURTECH AI</div>
          <div class="logo-sub">Elite · Kenya Motor</div>
        </div>""", unsafe_allow_html=True)

        # ── UPLOAD SECTION ────────────────────────
        st.markdown('<div class="upload-title">Upload Dataset</div>',
                    unsafe_allow_html=True)
        st.markdown(
            '<div style="font-size:.68rem;color:#3A5A80;margin-bottom:.6rem">'
            'CSV · Excel · PDF · Word (.docx)</div>',
            unsafe_allow_html=True)

        uploaded = st.file_uploader(
            "Upload",
            type=["csv","xlsx","xls","pdf","docx"],
            label_visibility="collapsed",
            help="Upload any motor claims file. Accepted: CSV, Excel, PDF tables, Word tables.",
        )

        if uploaded is not None:
            with st.spinner(f"Reading {uploaded.name}…"):
                up_df = ingest_file(uploaded)
            if up_df is not None and len(up_df) > 0:
                st.success(f"✓ {len(up_df):,} records · {up_df.shape[1]} columns")
                df = up_df
                st.session_state["upload_df"] = up_df
                st.session_state["using_upload"] = True
            else:
                st.error("Could not parse file — using default dataset.")
                st.session_state["using_upload"] = False
        else:
            if st.session_state.get("using_upload") and "upload_df" in st.session_state:
                df = st.session_state["upload_df"]
                st.caption(f"Uploaded dataset active · {len(df):,} rows")
            else:
                st.session_state["using_upload"] = False
                st.caption("Monte Carlo dataset · 50,000 rows")

        st.markdown("---")
        st.markdown('<div class="sh">Detection Threshold</div>', unsafe_allow_html=True)
        thr = st.slider("Flag fraud if score ≥", 0.05, 0.90, 0.35, 0.01, format="%.2f",
                        label_visibility="visible")

        st.markdown("---")
        st.markdown(
            f'<div style="font-size:.68rem;color:#3A5A80;line-height:2">'
            f'<b style="color:#7A9AC0">Frank Mumo</b><br>'
            f'University of Nairobi · 2026<br>'
            f'Actuarial Science Competition</div>', unsafe_allow_html=True)

    # No filters — use full dataset, just apply threshold
    f = df.copy()
    f["flagged"] = (f["fraud_probability_score"] >= thr).astype(int)
    return f, thr

# ═══════════════════════════════════════════════
# TAB 1 — EXECUTIVE OVERVIEW
# ═══════════════════════════════════════════════
def overview(df, thr):
    n         = len(df)
    if n == 0:
        st.warning("No data matches the current filters.")
        return
    n_fraud   = int(df["is_fraud"].sum())
    n_flagged = int(df["flagged"].sum())
    exposure  = df["claimed_amount_ksh"].sum()
    fraud_exp = df["expected_fraud_loss_ksh"].sum()
    prevented = fraud_exp * 0.89

    cols = st.columns(5, gap="small")
    cards = [
        ("💼","Total Claims",    f"{n:,}",            "Active portfolio",              "","","blue"),
        ("🚨","Fraud Confirmed", f"{n_fraud:,}",      f"{n_fraud/n:.1%} of portfolio", f"{n_fraud/n:.1%}","br","red"),
        ("⚑", f"Flagged ≥{thr:.2f}",f"{n_flagged:,}","Investigation queue",           "Priority","ba","amber"),
        ("💰","Total Exposure",  ksh(exposure),        f"Avg {ksh(exposure/n)}",        "","","blue"),
        ("✅","Preventable Loss",ksh(prevented),       "89% AI detection rate",         "↑ Recoverable","bg","green"),
    ]
    for col,(icon,lbl,val,sub,badge,bt,color) in zip(cols,cards):
        with col:
            st.markdown(kpi(icon,lbl,val,sub,badge,bt,color), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1,c2,c3 = st.columns([.9,1,2.1], gap="small")

    with c1:
        sh("Risk Distribution")
        tc   = df["risk_tier"].astype(str).value_counts()
        cmap = {"High":C["red"],"Medium":C["amber"],"Low":C["green"],"Unknown":C["blue"]}
        fig  = go.Figure(go.Pie(
            labels=tc.index, values=tc.values, hole=.64,
            marker=dict(colors=[cmap.get(t,C["blue"]) for t in tc.index],
                        line=dict(color="#040D1C",width=3)),
            textfont=dict(size=10,color="#EEF4FF"),
            hovertemplate="<b>%{label}</b><br>%{value:,}<br>%{percent}<extra></extra>",
        ))
        fig.add_annotation(
            text=f"<b>{n:,}</b><br><span style='font-size:9px;color:#7A9AC0'>CLAIMS</span>",
            x=.5,y=.5,showarrow=False,font=dict(size=13,color="#EEF4FF"))
        fig.update_layout(**PT,height=220,showlegend=True,
                          legend=dict(orientation="h",y=-.14,x=.05,
                                      bgcolor="rgba(0,0,0,0)",font=dict(size=9)))
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

    with c2:
        sh("Fraud Rate by Claim Type")
        fbt = df.groupby("claim_type")["is_fraud"].mean().sort_values()
        fig = go.Figure(go.Bar(
            x=fbt.values*100, y=fbt.index.astype(str), orientation="h",
            marker=dict(color=fbt.values*100,
                        colorscale=[[0,C["green"]],[.45,C["amber"]],[1,C["red"]]],
                        showscale=False),
            text=[f"{v:.1f}%" for v in fbt.values*100],
            textposition="outside",textfont=dict(size=9,color="#7A9AC0"),
            hovertemplate="<b>%{y}</b><br>%{x:.1f}%<extra></extra>",
        ))
        fig.update_layout(**PT,height=220,
                          xaxis=dict(showgrid=False,showticklabels=False,
                                     range=[0,fbt.max()*130]),
                          yaxis=dict(tickfont=dict(size=9)))
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

    with c3:
        sh("Monthly Claims Volume & Fraud Trend")
        mon = (df.groupby("accident_month")
                 .agg(total=("claim_id","count"),fraud=("is_fraud","sum"))
                 .reset_index().sort_values("accident_month").tail(20))
        fig = make_subplots(specs=[[{"secondary_y":True}]])
        fig.add_trace(go.Bar(x=mon["accident_month"],y=mon["total"],
                             name="Total",marker_color=C["blue"],opacity=.45,
                             hovertemplate="%{x}<br>%{y:,}<extra></extra>"),secondary_y=False)
        fig.add_trace(go.Scatter(x=mon["accident_month"],y=mon["fraud"],
                                 name="Fraud",line=dict(color=C["red"],width=2.5),
                                 mode="lines+markers",marker=dict(size=5,color=C["red"]),
                                 hovertemplate="%{x}<br>%{y:,}<extra></extra>"),secondary_y=True)
        fig.update_layout(**PT,height=220,
                          legend=dict(orientation="h",y=1.14,x=0,
                                      bgcolor="rgba(0,0,0,0)",font=dict(size=9)),
                          xaxis=dict(tickangle=40,tickfont=dict(size=8)))
        fig.update_yaxes(showgrid=True,gridcolor=GRID,secondary_y=False)
        fig.update_yaxes(showgrid=False,secondary_y=True)
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

    c1,c2,c3 = st.columns([1.5,1,1],gap="small")

    with c1:
        sh("Fraud Exposure by Insurer")
        ins_g = (df.groupby("insurer")
                   .agg(fexp=("expected_fraud_loss_ksh","sum"),fr=("is_fraud","mean"))
                   .sort_values("fexp",ascending=True).tail(8))
        fig = go.Figure(go.Bar(
            x=ins_g["fexp"]/1e6, y=ins_g.index.astype(str), orientation="h",
            marker=dict(color=ins_g["fr"]*100,
                        colorscale=[[0,C["blue"]],[.5,C["amber"]],[1,C["red"]]],
                        showscale=True,
                        colorbar=dict(title="Fraud%",tickfont=dict(size=8),
                                      thickness=10,len=.7)),
            text=[f"{v:.1f}M" for v in ins_g["fexp"]/1e6],
            textposition="outside",textfont=dict(size=9,color="#7A9AC0"),
            hovertemplate="<b>%{y}</b><br>KSh %{x:.1f}M<extra></extra>",
        ))
        fig.update_layout(**PT,height=255,
                          xaxis=dict(showgrid=False,showticklabels=False),
                          yaxis=dict(tickfont=dict(size=9)))
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

    with c2:
        sh("Claims by County")
        cd = (df.groupby("county").agg(claims=("claim_id","count"))
                .sort_values("claims",ascending=True).tail(9))
        fig = go.Figure(go.Bar(
            x=cd["claims"],y=cd.index.astype(str),orientation="h",
            marker=dict(color=C["cyan"],opacity=.75),
            text=cd["claims"].apply(lambda v:f"{v:,}"),
            textposition="outside",textfont=dict(size=9,color="#7A9AC0"),
            hovertemplate="<b>%{y}</b><br>%{x:,}<extra></extra>",
        ))
        fig.update_layout(**PT,height=255,
                          xaxis=dict(showgrid=False,showticklabels=False),
                          yaxis=dict(tickfont=dict(size=9)))
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

    with c3:
        sh("Vehicle Make Split")
        vm = df["vehicle_make"].astype(str).value_counts().head(8)
        fig = go.Figure(go.Pie(
            labels=vm.index,values=vm.values,hole=.48,
            marker=dict(line=dict(color="#040D1C",width=2)),
            textfont=dict(size=9),
            hovertemplate="<b>%{label}</b><br>%{value:,} (%{percent})<extra></extra>",
        ))
        fig.update_layout(**PT,height=255,
                          legend=dict(orientation="v",font=dict(size=9),x=1.02,
                                      bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})


# ═══════════════════════════════════════════════
# TAB 2 — FRAUD INTELLIGENCE
# ═══════════════════════════════════════════════
def fraud_tab(df, thr):
    n_flagged = int(df["flagged"].sum())
    n_actual  = int(df["is_fraud"].sum())
    n_caught  = int(((df["flagged"]==1)&(df["is_fraud"]==1)).sum())
    precision = n_caught/max(n_flagged,1)
    recall    = n_caught/max(n_actual,1)
    fexp      = df[df["flagged"]==1]["claimed_amount_ksh"].sum()

    cols = st.columns(5,gap="small")
    for col,(icon,lbl,val,sub,badge,bt,color) in zip(cols,[
        ("🔍","Flagged",       f"{n_flagged:,}",  f"At ≥{thr:.2f}",       "Queue",           "ba","amber"),
        ("✓", "Detected",     f"{n_caught:,}",   "True positives",        f"{recall:.0%} recall","bg","green"),
        ("🎯","Precision",     f"{precision:.1%}","Of flagged = fraud",    "Accuracy",        "bb","blue"),
        ("💸","Flagged Exp.",  ksh(fexp),          "At-risk exposure",      "","","red"),
        ("📊","Prevalence",    f"{n_actual/max(len(df),1):.1%}",f"{n_actual:,} cases","~12% industry","ba","amber"),
    ]):
        with col:
            st.markdown(kpi(icon,lbl,val,sub,badge,bt,color),unsafe_allow_html=True)

    st.markdown("<br>",unsafe_allow_html=True)
    c1,c2 = st.columns(2,gap="small")

    with c1:
        sh("Fraud Score Distribution — Fraud vs Legitimate")
        fs = df[df["is_fraud"]==1]["fraud_probability_score"].dropna()
        ls = df[df["is_fraud"]==0]["fraud_probability_score"].dropna()
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=ls,name="Legitimate",marker_color=C["green"],
                                   opacity=.55,nbinsx=60,
                                   hovertemplate="Score %{x:.2f}<br>%{y:,}<extra>Legit</extra>"))
        fig.add_trace(go.Histogram(x=fs,name="Fraudulent",marker_color=C["red"],
                                   opacity=.65,nbinsx=60,
                                   hovertemplate="Score %{x:.2f}<br>%{y:,}<extra>Fraud</extra>"))
        fig.add_vline(x=thr,line_dash="dash",line_color=C["cyan"],line_width=2,
                      annotation_text=f"  {thr:.2f}",
                      annotation_font=dict(color=C["cyan"],size=10))
        fig.update_layout(**PT,height=290,barmode="overlay",
                          xaxis_title="Score",yaxis_title="Count",
                          xaxis=dict(showgrid=True,gridcolor=GRID),
                          yaxis=dict(showgrid=True,gridcolor=GRID),
                          legend=dict(orientation="h",y=1.12,
                                      bgcolor="rgba(0,0,0,0)",font=dict(size=9)))
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

    with c2:
        sh("Risk Flag Comparison — Fraud vs Legitimate")
        flags = {
            "Night Incident":  "night_incident_flag",
            "No Police":       "no_police_flag",
            "No Witnesses":    "no_witness_flag",
            "New Policy":      "policy_age_risk",
            "Young Driver":    "young_driver_flag",
            "Total Loss":      "total_loss_flag",
            "Single Vehicle":  "single_vehicle_flag",
            "Repeat Claimant": "repeat_claimant_flag",
        }
        fd = df[df["is_fraud"]==1]
        ld = df[df["is_fraud"]==0]
        labels,fv,lv = [],[],[]
        for lbl,col in flags.items():
            if col in df.columns:
                labels.append(lbl); fv.append(fd[col].mean()*100); lv.append(ld[col].mean()*100)
        if labels:
            fig = go.Figure()
            fig.add_trace(go.Bar(name="Fraudulent",x=labels,y=fv,
                                 marker_color=C["red"],opacity=.85,
                                 hovertemplate="%{x}<br>%{y:.1f}%<extra>Fraud</extra>"))
            fig.add_trace(go.Bar(name="Legitimate",x=labels,y=lv,
                                 marker_color=C["green"],opacity=.7,
                                 hovertemplate="%{x}<br>%{y:.1f}%<extra>Legit</extra>"))
            fig.update_layout(**PT,height=290,barmode="group",
                              yaxis_title="% of Claims",
                              xaxis=dict(tickangle=28,tickfont=dict(size=9)),
                              yaxis=dict(showgrid=True,gridcolor=GRID),
                              legend=dict(orientation="h",y=1.12,
                                          bgcolor="rgba(0,0,0,0)",font=dict(size=9)))
            st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
        else:
            st.info("Risk flag columns not found in this dataset.")

    c1,c2 = st.columns([1,2],gap="small")
    with c1:
        sh("Confusion Matrix")
        tp=int(((df["flagged"]==1)&(df["is_fraud"]==1)).sum())
        fp=int(((df["flagged"]==1)&(df["is_fraud"]==0)).sum())
        fn=int(((df["flagged"]==0)&(df["is_fraud"]==1)).sum())
        tn=int(((df["flagged"]==0)&(df["is_fraud"]==0)).sum())
        fig = go.Figure(go.Heatmap(
            z=[[tn,fp],[fn,tp]],
            x=["Pred Legit","Pred Fraud"],y=["Actual Legit","Actual Fraud"],
            colorscale=[[0,"#0C1A30"],[.5,C["blue"]],[1,C["green"]]],
            showscale=False,
            text=[[f"{tn:,}",f"{fp:,}"],[f"{fn:,}",f"{tp:,}"]],
            texttemplate="<b>%{text}</b>",textfont=dict(size=15,color="white"),
            hovertemplate="<b>%{y} → %{x}</b><br>%{text}<extra></extra>",
        ))
        fig.update_layout(**PT,height=230,
                          xaxis=dict(tickfont=dict(size=10)),
                          yaxis=dict(tickfont=dict(size=10)))
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

    with c2:
        sh("🚨 Top 15 Priority Investigation Queue")
        pq_cols = [c for c in ["claim_id","insurer","claim_type","county",
                                "claimed_amount_ksh","fraud_probability_score","risk_tier",
                                "expected_fraud_loss_ksh","night_incident_flag",
                                "no_police_flag","no_witness_flag"]
                   if c in df.columns]
        pq = df.nlargest(15,"expected_fraud_loss_ksh")[pq_cols].copy()
        for c in ["claimed_amount_ksh","expected_fraud_loss_ksh"]:
            if c in pq.columns: pq[c]=pq[c].apply(lambda v:f"KSh {v:,.0f}")
        if "fraud_probability_score" in pq.columns:
            pq["fraud_probability_score"]=pq["fraud_probability_score"].apply(lambda v:f"{v:.3f}")
        st.dataframe(pq,use_container_width=True,hide_index=True,height=235,
            column_config={
                "claimed_amount_ksh":      st.column_config.TextColumn("Claimed"),
                "expected_fraud_loss_ksh": st.column_config.TextColumn("Est. Loss"),
                "fraud_probability_score": st.column_config.TextColumn("Score"),
                "night_incident_flag":     st.column_config.CheckboxColumn("Night"),
                "no_police_flag":          st.column_config.CheckboxColumn("No Police"),
                "no_witness_flag":         st.column_config.CheckboxColumn("No Witness"),
            })


# ═══════════════════════════════════════════════
# TAB 3 — ACTUARIAL PRICING
# ═══════════════════════════════════════════════
def pricing_tab(df):
    has_settle = ("settlement_amount_ksh" in df.columns and
                  df["settlement_amount_ksh"].sum() > 0)
    lr  = (df["settlement_amount_ksh"].sum()/max(df["claimed_amount_ksh"].sum(),1)
           if has_settle else 0.787)
    cr  = lr+0.30
    avg = df["claimed_amount_ksh"].mean()

    cols = st.columns(5,gap="small")
    for col,(icon,lbl,val,sub,badge,bt,color) in zip(cols,[
        ("📉","Loss Ratio",    f"{lr:.1%}",   "Settlement/Claimed",
         "Healthy" if lr<.75 else "Monitor","bg" if lr<.75 else "ba",
         "green" if lr<.75 else "amber"),
        ("📊","Combined Ratio",f"{cr:.1%}",   "Loss+30% Expense",
         "Profitable" if cr<1 else "Loss","bg" if cr<1 else "br","blue"),
        ("💼","Avg Claim",     ksh(avg),      "Mean claimed","","","blue"),
        ("✅","Avg Settlement",
         ksh(df["settlement_amount_ksh"].mean()) if has_settle else "N/A",
         f"{lr:.1%} of claim","","","cyan"),
        ("📌","Claim/Estimate",
         f"{df['claim_to_estimate_ratio'].mean():.3f}"
         if "claim_to_estimate_ratio" in df.columns else "N/A",
         "Over-claim ratio","","","purple"),
    ]):
        with col:
            st.markdown(kpi(icon,lbl,val,sub,badge,bt,color),unsafe_allow_html=True)

    st.markdown("<br>",unsafe_allow_html=True)
    c1,c2 = st.columns(2,gap="small")

    with c1:
        sh("Claim Severity by Type — Log Scale")
        pal=[C["blue"],C["cyan"],C["green"],C["amber"],C["red"],C["purple"]]
        fig=go.Figure()
        for i,ct in enumerate(df["claim_type"].astype(str).dropna().unique()):
            sub=df[df["claim_type"].astype(str)==ct]["claimed_amount_ksh"].dropna()
            if len(sub)==0: continue
            ch=pal[i%len(pal)]
            r,g,b=int(ch[1:3],16),int(ch[3:5],16),int(ch[5:7],16)
            fig.add_trace(go.Box(y=sub,name=ct,boxpoints="outliers",
                                 marker=dict(color=ch,size=2,opacity=.4),
                                 line=dict(width=1.8,color=ch),
                                 fillcolor=f"rgba({r},{g},{b},.12)",
                                 hovertemplate="%{y:,.0f} KSh<extra>%{x}</extra>"))
        fig.update_layout(**PT,height=300,showlegend=False,
                          yaxis=dict(type="log",showgrid=True,gridcolor=GRID,
                                     title="KSh (log)"),
                          xaxis=dict(tickfont=dict(size=9)))
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

    with c2:
        sh("Settlement Ratio by Policy Type & Risk Tier")
        if has_settle and "policy_type" in df.columns:
            df2=df.copy()
            df2["set_ratio"]=df2["settlement_amount_ksh"]/df2["claimed_amount_ksh"].replace(0,np.nan)
            piv=df2.groupby(["policy_type","risk_tier"])["set_ratio"].mean().reset_index()
            cmap={"High":C["red"],"Medium":C["amber"],"Low":C["green"]}
            fig=go.Figure()
            for tier in piv["risk_tier"].unique():
                sub=piv[piv["risk_tier"]==tier]
                fig.add_trace(go.Bar(x=sub["policy_type"].astype(str),y=sub["set_ratio"],
                                     name=str(tier),marker_color=cmap.get(str(tier),C["blue"]),
                                     opacity=.82,
                                     hovertemplate="%{x}<br>%{y:.1%}<extra>%{name}</extra>"))
            fig.update_layout(**PT,height=300,barmode="group",
                              yaxis=dict(tickformat=".0%",showgrid=True,gridcolor=GRID),
                              xaxis=dict(tickfont=dict(size=10)),
                              legend=dict(orientation="h",y=1.12,
                                          bgcolor="rgba(0,0,0,0)",font=dict(size=9)))
            st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
        else:
            st.info("Settlement or policy type data not available in this dataset.")

    c1,c2 = st.columns(2,gap="small")
    with c1:
        sh("Avg Claim by Driver Age Band")
        if "driver_age" in df.columns:
            df2=df.copy()
            df2["aband"]=pd.cut(df2["driver_age"],bins=[17,25,35,45,55,100],
                                labels=["18–25","26–35","36–45","46–55","55+"])
            ag=df2.groupby("aband",observed=True).agg(
                avg=("claimed_amount_ksh","mean"),fr=("is_fraud","mean")).reset_index()
            fig=go.Figure(go.Bar(
                x=ag["aband"].astype(str),y=ag["avg"],
                marker=dict(color=ag["fr"]*100,
                            colorscale=[[0,C["green"]],[.5,C["amber"]],[1,C["red"]]],
                            showscale=True,
                            colorbar=dict(title="Fraud%",tickfont=dict(size=8),
                                          thickness=10,len=.6)),
                hovertemplate="Age %{x}<br>KSh %{y:,.0f}<extra></extra>",
            ))
            fig.update_layout(**PT,height=275,
                              yaxis=dict(showgrid=True,gridcolor=GRID,title="Avg KSh"))
            st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
        else:
            st.info("Driver age column not found in this dataset.")

    with c2:
        sh("Vehicle Age vs Claim Frequency")
        if "vehicle_age" in df.columns:
            df2=df.copy()
            df2["vband"]=pd.cut(df2["vehicle_age"],bins=[-1,5,10,15,20,40],
                                labels=["0–5yr","6–10yr","11–15yr","16–20yr","20+yr"])
            vg=df2.groupby("vband",observed=True).agg(
                cnt=("claim_id","count"),avg=("claimed_amount_ksh","mean")).reset_index()
            fig=make_subplots(specs=[[{"secondary_y":True}]])
            fig.add_trace(go.Bar(x=vg["vband"].astype(str),y=vg["cnt"],
                                 name="Claims",marker_color=C["blue"],opacity=.5,
                                 hovertemplate="%{x}<br>%{y:,}<extra></extra>"),secondary_y=False)
            fig.add_trace(go.Scatter(x=vg["vband"].astype(str),y=vg["avg"],
                                     name="Avg KSh",line=dict(color=C["cyan"],width=2.5),
                                     mode="lines+markers",marker=dict(size=7),
                                     hovertemplate="%{x}<br>KSh %{y:,.0f}<extra></extra>"),
                          secondary_y=True)
            fig.update_layout(**PT,height=275,
                              legend=dict(orientation="h",y=1.14,
                                          bgcolor="rgba(0,0,0,0)",font=dict(size=9)))
            fig.update_yaxes(showgrid=True,gridcolor=GRID,secondary_y=False)
            fig.update_yaxes(showgrid=False,secondary_y=True)
            st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
        else:
            st.info("Vehicle age column not found in this dataset.")


# ═══════════════════════════════════════════════
# TAB 4 — FINANCIAL IMPACT
# ═══════════════════════════════════════════════
def impact_tab(df, thr):
    n       = len(df)
    n_fraud = int(df["is_fraud"].sum())
    avg_f   = (df[df["is_fraud"]==1]["claimed_amount_ksh"].median()
               if n_fraud > 0 else df["claimed_amount_ksh"].median())
    prevented = n_fraud * .89 * avg_f
    fa_cost   = int(df["flagged"].sum()) * 3000
    net       = prevented - fa_cost
    scale     = 10000 / max(n, 1)

    c1,c2 = st.columns([1.6,1],gap="small")

    with c1:
        sh("Financial Impact Waterfall — Per 10,000 Claims")
        tv,pv,fc,ns = n_fraud*avg_f*scale, prevented*scale, fa_cost*scale, net*scale
        fig = go.Figure(go.Waterfall(
            orientation="v",
            measure=["absolute","relative","relative","total"],
            x=["Total Fraud Exposure","AI Prevents (89%)","False Alarm Cost","Net Saving"],
            y=[tv/1e6,-pv/1e6,fc/1e6,0],
            text=[ksh(tv),f"−{ksh(pv)}",f"+{ksh(fc)}",ksh(ns)],
            textfont=dict(size=11,color="#EEF4FF"),
            connector=dict(line=dict(color=GRID,width=1)),
            increasing=dict(marker=dict(color=C["red"])),
            decreasing=dict(marker=dict(color=C["green"])),
            totals=dict(marker=dict(color=C["cyan"])),
            hovertemplate="%{x}<br>KSh %{y:.2f}M<extra></extra>",
        ))
        fig.update_layout(**PT,height=320,
                          yaxis=dict(showgrid=True,gridcolor=GRID,title="KSh Millions"))
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

    with c2:
        sh("ROI Summary")
        roi = (ns/4_300_000)*100
        st.markdown(f"""<div class="abox">
<b>Mid-Sized Insurer — Annual Projection</b><br><br>
📋 Claims/year: <b>10,000</b><br>
🚨 Fraud cases (12.1%): <b>1,210</b><br>
🤖 AI catches 89%: <b>1,077</b><br>
✅ Prevented: <b>{ksh(pv)}</b><br>
⚠️ False alarms: <b>{ksh(fc)}</b><br>
<hr style="border-color:#1A2E4A;margin:.7rem 0">
💰 <b>Net Saving: {ksh(ns)}</b><br>
🏗️ System cost Y1: <b>KSh 4.3M</b><br>
📈 <b>ROI: {roi:.0f}%</b><br>
⏱️ <b>Payback: &lt; 2 months</b>
</div>""", unsafe_allow_html=True)

        st.markdown("<br>",unsafe_allow_html=True)
        sh("Scaling Projections")
        scenarios=[("Single Insurer",ns,C["blue"]),
                   ("5 Major Insurers",ns*5,C["cyan"]),
                   ("Full Industry+NHIF",ns*11.5,C["green"])]
        mx=scenarios[-1][1]
        for name,val,color in scenarios:
            pbar(name,val,mx,color)

    st.markdown("<br>",unsafe_allow_html=True)
    c1,c2 = st.columns(2,gap="small")

    with c1:
        sh("Cost Sensitivity — Detection Threshold")
        thrs=np.arange(.10,.82,.04)
        fn_c,fp_c,tot_c=[],[],[]
        for t in thrs:
            fl=(df["fraud_probability_score"]>=t).astype(int)
            fn2=int(((fl==0)&(df["is_fraud"]==1)).sum())
            fp2=int(((fl==1)&(df["is_fraud"]==0)).sum())
            fn_c.append(fn2*120000/1e6); fp_c.append(fp2*3000/1e6)
            tot_c.append((fn2*120000+fp2*3000)/1e6)
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=thrs,y=fn_c,name="Missed Fraud",
                                 line=dict(color=C["red"],width=2),
                                 hovertemplate="t=%.2f  KSh %.1fM<extra></extra>"))
        fig.add_trace(go.Scatter(x=thrs,y=fp_c,name="False Alarms",
                                 line=dict(color=C["amber"],width=2),
                                 hovertemplate="t=%.2f  KSh %.1fM<extra></extra>"))
        fig.add_trace(go.Scatter(x=thrs,y=tot_c,name="Total Cost",
                                 line=dict(color=C["cyan"],width=2.5,dash="dot"),
                                 hovertemplate="t=%.2f  KSh %.1fM<extra></extra>"))
        opt=int(np.argmin(tot_c))
        fig.add_vline(x=thr,line_dash="dash",line_color="white",line_width=1.5,
                      annotation_text=f" {thr:.2f}",
                      annotation_font=dict(color="white",size=9))
        fig.add_vline(x=thrs[opt],line_dash="dot",line_color=C["green"],line_width=1.5,
                      annotation_text=f" Optimal {thrs[opt]:.2f}",
                      annotation_font=dict(color=C["green"],size=9))
        fig.update_layout(**PT,height=280,
                          xaxis_title="Threshold",yaxis_title="KSh Millions",
                          xaxis=dict(showgrid=True,gridcolor=GRID),
                          yaxis=dict(showgrid=True,gridcolor=GRID),
                          legend=dict(orientation="h",y=1.12,
                                      bgcolor="rgba(0,0,0,0)",font=dict(size=9)))
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

    with c2:
        sh("Fraud Exposure — County × Claim Type")
        heat=(df.groupby(["county","claim_type"])["expected_fraud_loss_ksh"]
                .sum().reset_index())
        if len(heat)>1:
            hp=heat.pivot(index="county",columns="claim_type",
                          values="expected_fraud_loss_ksh").fillna(0)
            fig=go.Figure(go.Heatmap(
                z=hp.values/1e6,x=hp.columns.astype(str).tolist(),
                y=hp.index.astype(str).tolist(),
                colorscale=[[0,"#0C1A30"],[.4,C["blue"]],[.75,C["amber"]],[1,C["red"]]],
                hovertemplate="<b>%{y} × %{x}</b><br>KSh %{z:.1f}M<extra></extra>",
                colorbar=dict(title="KSh M",tickfont=dict(size=8),thickness=10,len=.8),
            ))
            fig.update_layout(**PT,height=280,
                              xaxis=dict(tickfont=dict(size=9),tickangle=25),
                              yaxis=dict(tickfont=dict(size=9)))
            st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
        else:
            st.info("Insufficient data for heatmap with current filters.")


# ═══════════════════════════════════════════════
# TAB 5 — DRIVER & VEHICLE INTEL
# ═══════════════════════════════════════════════
def intel_tab(df):
    sh("Driver Profile Analysis")
    c1,c2,c3 = st.columns(3,gap="small")

    with c1:
        if "driver_age" in df.columns:
            af=(df.groupby(pd.cut(df["driver_age"],bins=[17,25,35,45,55,100],
                                  labels=["18–25","26–35","36–45","46–55","55+"]),
                           observed=True)["is_fraud"].mean().reset_index())
            af.columns=["band","fr"]
            fig=go.Figure(go.Bar(
                x=af["band"].astype(str),y=af["fr"]*100,
                marker=dict(color=af["fr"]*100,
                            colorscale=[[0,C["green"]],[.5,C["amber"]],[1,C["red"]]],
                            showscale=False),
                text=[f"{v:.1f}%" for v in af["fr"]*100],
                textposition="outside",textfont=dict(size=10,color="#7A9AC0"),
                hovertemplate="Age %{x}<br>Fraud %{y:.1f}%<extra></extra>",
            ))
            fig.update_layout(**PT,height=260,
                              title=dict(text="Fraud Rate by Driver Age",
                                         font=dict(size=11,color="#7A9AC0")),
                              yaxis=dict(showgrid=True,gridcolor=GRID,title="%"))
            st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
        else:
            st.info("Driver age not available.")

    with c2:
        if "driver_years_experience" in df.columns:
            ef=(df.groupby(pd.cut(df["driver_years_experience"],
                                  bins=[-1,2,5,10,20,50],
                                  labels=["0–2","3–5","6–10","11–20","20+"]),
                           observed=True)["is_fraud"].mean().reset_index())
            ef.columns=["band","fr"]
            fig=go.Figure(go.Scatter(
                x=ef["band"].astype(str),y=ef["fr"]*100,
                mode="lines+markers",line=dict(color=C["cyan"],width=2.5),
                marker=dict(size=10,color=C["cyan"],line=dict(color="#040D1C",width=2)),
                fill="tozeroy",fillcolor="rgba(0,207,255,.07)",
                hovertemplate="Exp %{x}yr<br>Fraud %{y:.1f}%<extra></extra>",
            ))
            fig.update_layout(**PT,height=260,
                              title=dict(text="Fraud Rate by Experience",
                                         font=dict(size=11,color="#7A9AC0")),
                              yaxis=dict(showgrid=True,gridcolor=GRID,title="%"))
            st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
        else:
            st.info("Experience column not available.")

    with c3:
        if "driver_gender" in df.columns:
            gs=(df.groupby("driver_gender")
                  .agg(fr=("is_fraud","mean"),avg=("claimed_amount_ksh","mean"))
                  .reset_index())
            fig=go.Figure(go.Bar(
                x=gs["driver_gender"].astype(str),y=gs["fr"]*100,
                marker_color=[C["blue"],C["purple"]],opacity=.85,
                text=[f"{v:.1f}%" for v in gs["fr"]*100],
                textposition="outside",textfont=dict(size=11,color="#7A9AC0"),
                hovertemplate="%{x}<br>Fraud %{y:.1f}%<extra></extra>",
            ))
            fig.update_layout(**PT,height=260,
                              title=dict(text="Fraud Rate by Gender",
                                         font=dict(size=11,color="#7A9AC0")),
                              yaxis=dict(showgrid=True,gridcolor=GRID,title="%"))
            st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
        else:
            st.info("Driver gender not available.")

    st.markdown("<br>",unsafe_allow_html=True)
    sh("Vehicle Intelligence")
    c1,c2 = st.columns(2,gap="small")

    with c1:
        ms=(df.groupby("vehicle_make")
              .agg(avg=("claimed_amount_ksh","mean"),fr=("is_fraud","mean"))
              .sort_values("avg",ascending=False).head(9).reset_index())
        fig=go.Figure(go.Bar(
            x=ms["vehicle_make"].astype(str),y=ms["avg"],
            marker=dict(color=ms["fr"]*100,
                        colorscale=[[0,C["green"]],[.5,C["amber"]],[1,C["red"]]],
                        showscale=True,
                        colorbar=dict(title="Fraud%",tickfont=dict(size=8),
                                      thickness=10,len=.7)),
            hovertemplate="<b>%{x}</b><br>KSh %{y:,.0f}<extra></extra>",
        ))
        fig.update_layout(**PT,height=295,
                          title=dict(text="Avg Claim by Make  (colour = fraud rate)",
                                     font=dict(size=11,color="#7A9AC0")),
                          yaxis=dict(showgrid=True,gridcolor=GRID,title="Avg KSh"))
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

    with c2:
        if "vehicle_use" in df.columns:
            us=(df.groupby("vehicle_use")
                  .agg(fr=("is_fraud","mean"),avg=("claimed_amount_ksh","mean"),
                       cnt=("claim_id","count")).reset_index())
            pal=[C["blue"],C["cyan"],C["green"],C["amber"]]
            fig=go.Figure()
            for i,row in us.iterrows():
                ch=pal[i%len(pal)]
                fig.add_trace(go.Scatter(
                    x=[row["avg"]],y=[row["fr"]*100],mode="markers+text",
                    marker=dict(size=max(row["cnt"]/200,8),color=ch,opacity=.85,
                                line=dict(color="#040D1C",width=2)),
                    text=[str(row["vehicle_use"])],textposition="top center",
                    textfont=dict(size=9,color="#7A9AC0"),name=str(row["vehicle_use"]),
                    hovertemplate=(f"<b>{row['vehicle_use']}</b><br>"
                                   f"Avg KSh %{{x:,.0f}}<br>Fraud %{{y:.1f}}%<br>"
                                   f"{row['cnt']:,} claims<extra></extra>"),
                ))
            fig.update_layout(**PT,height=295,showlegend=False,
                              title=dict(text="Vehicle Use — Fraud % vs Avg Claim",
                                         font=dict(size=11,color="#7A9AC0")),
                              xaxis=dict(showgrid=True,gridcolor=GRID,title="Avg KSh"),
                              yaxis=dict(showgrid=True,gridcolor=GRID,title="Fraud %"))
            st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
        else:
            st.info("Vehicle use column not available.")


# ═══════════════════════════════════════════════
# TAB 6 — DATA EXPLORER
# ═══════════════════════════════════════════════
def explorer_tab(df):
    sh("Claim Data Explorer")
    c1,c2,c3,c4 = st.columns(4,gap="small")
    num_cols=[c for c in ["claimed_amount_ksh","fraud_probability_score",
                           "expected_fraud_loss_ksh","composite_risk_score",
                           "settlement_amount_ksh"] if c in df.columns]
    with c1:
        sort_col=st.selectbox("Sort by",num_cols) if num_cols else None
    with c2:
        order=st.selectbox("Order",["Descending","Ascending"])
    with c3:
        n_rows=st.selectbox("Rows",[25,50,100,200])
    with c4:
        search=st.text_input("Search",placeholder="Claim ID or Insurer")

    dsp=df.copy()
    if search:
        mask=pd.Series([False]*len(dsp))
        for col in ["claim_id","insurer","county","claim_type"]:
            if col in dsp.columns:
                mask=mask|dsp[col].astype(str).str.contains(search,case=False,na=False)
        dsp=dsp[mask]

    if sort_col and sort_col in dsp.columns:
        dsp=dsp.sort_values(sort_col,ascending=(order=="Ascending"))

    show=[c for c in ["claim_id","insurer","claim_type","county","policy_type",
                       "vehicle_make","vehicle_model","vehicle_age","driver_age",
                       "claimed_amount_ksh","garage_estimate_ksh","settlement_amount_ksh",
                       "claim_to_estimate_ratio","claim_to_sum_insured_ratio",
                       "fraud_probability_score","flagged","risk_tier",
                       "expected_fraud_loss_ksh","night_incident_flag",
                       "no_police_flag","accident_date"]
          if c in dsp.columns]

    col_cfg={}
    if "claimed_amount_ksh"      in show: col_cfg["claimed_amount_ksh"]     =st.column_config.NumberColumn("Claimed",   format="KSh %,.0f")
    if "garage_estimate_ksh"     in show: col_cfg["garage_estimate_ksh"]    =st.column_config.NumberColumn("Estimate",  format="KSh %,.0f")
    if "settlement_amount_ksh"   in show: col_cfg["settlement_amount_ksh"]  =st.column_config.NumberColumn("Settlement",format="KSh %,.0f")
    if "expected_fraud_loss_ksh" in show: col_cfg["expected_fraud_loss_ksh"]=st.column_config.NumberColumn("Fraud Loss",format="KSh %,.0f")
    if "fraud_probability_score" in show: col_cfg["fraud_probability_score"]=st.column_config.ProgressColumn("Score",min_value=0,max_value=1,format="%.3f")
    if "claim_to_estimate_ratio" in show: col_cfg["claim_to_estimate_ratio"]=st.column_config.NumberColumn("Claim/Est", format="%.3f")
    if "flagged"                 in show: col_cfg["flagged"]                =st.column_config.CheckboxColumn("Flagged")
    if "night_incident_flag"     in show: col_cfg["night_incident_flag"]    =st.column_config.CheckboxColumn("Night")
    if "no_police_flag"          in show: col_cfg["no_police_flag"]         =st.column_config.CheckboxColumn("No Police")
    if "accident_date"           in show: col_cfg["accident_date"]          =st.column_config.DateColumn("Date")

    st.dataframe(dsp[show].head(n_rows),use_container_width=True,
                 hide_index=True,column_config=col_cfg)

    st.markdown(
        f'<div style="font-size:.72rem;color:#3A5A80;margin-top:.4rem">'
        f'Showing {min(n_rows,len(dsp)):,} of {len(dsp):,} records</div>',
        unsafe_allow_html=True)

    csv=dsp[show].head(n_rows).to_csv(index=False).encode("utf-8")
    st.download_button("⬇  Export CSV",data=csv,
                       file_name="insurtech_export.csv",mime="text/csv")


# ═══════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════
def main():
    if "using_upload" not in st.session_state:
        st.session_state["using_upload"] = False

    # Force sidebar always open via JavaScript
    st.markdown("""
    <script>
    // Force sidebar to stay open
    const sidebar = window.parent.document.querySelector('[data-testid="stSidebar"]');
    if (sidebar) {
        sidebar.style.width = '300px';
        sidebar.style.minWidth = '300px';
        sidebar.setAttribute('aria-expanded', 'true');
    }
    const collapseBtn = window.parent.document.querySelector('[data-testid="collapsedControl"]');
    if (collapseBtn) collapseBtn.style.display = 'none';
    </script>
    """, unsafe_allow_html=True)

    # Resolve active dataframe
    default_df = load_default()

    active_df = (st.session_state.get("upload_df")
                 if st.session_state.get("using_upload")
                 else default_df)

    if active_df is None:
        active_df = pd.DataFrame()

    df, thr = sidebar(active_df if len(active_df) > 0 else pd.DataFrame(
        columns=["claim_id","insurer","claim_type","county","claimed_amount_ksh",
                 "is_fraud","fraud_probability_score","expected_fraud_loss_ksh",
                 "risk_tier","vehicle_make","accident_month"]))

    if len(df) == 0:
        st.error("⚠️ No dataset loaded.")
        st.info("Place `kenya_motor_claims_50000.csv` in `data/generated/` "
                "or upload a file using the sidebar.")
        st.stop()

    # Header
    h1,h2 = st.columns([3,1])
    with h1:
        st.markdown("""
        <div style="padding:1.4rem 2rem .4rem">
          <div style="display:flex;align-items:center;gap:.7rem;margin-bottom:.25rem">
            <span style="font-size:1.9rem">🛡️</span>
            <div>
              <div style="font-family:'Syne',sans-serif;font-size:1.65rem;font-weight:800;
                          background:linear-gradient(135deg,#00CFFF 0%,#1A6DFF 50%,#9B5DE5 100%);
                          -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                          letter-spacing:-.02em;line-height:1">
                INSURTECH AI ELITE</div>
              <div style="font-family:'Syne',sans-serif;font-size:.6rem;font-weight:700;
                          letter-spacing:.18em;text-transform:uppercase;color:#3A5A80;margin-top:.18rem">
                Intelligent Fraud Detection & Claims Pricing · Kenya Motor Portfolio</div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)
    with h2:
        src_label = "Uploaded Dataset" if st.session_state.get("using_upload") else "Monte Carlo Dataset"
        st.markdown(
            f'<div style="text-align:right;padding:1.8rem 2rem 0 0;'
            f'font-family:\'Space Mono\',monospace;font-size:.65rem;color:#3A5A80">'
            f'{len(df):,} claims · {src_label}<br>Threshold {thr:.2f} · Frank Mumo</div>',
            unsafe_allow_html=True)

    t1,t2,t3,t4,t5,t6 = st.tabs([
        "📊  Overview",
        "🚨  Fraud Intel",
        "💰  Pricing",
        "📈  Impact",
        "🔬  Driver & Vehicle",
        "🔍  Explorer",
    ])
    with t1: overview(df, thr)
    with t2: fraud_tab(df, thr)
    with t3: pricing_tab(df)
    with t4: impact_tab(df, thr)
    with t5: intel_tab(df)
    with t6: explorer_tab(df)

if __name__ == "__main__":
    main()