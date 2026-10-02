"""
generate_data.py
=================
Cleans the 5 raw Kaggle CSVs and produces the simplified CSVs used by the
dashboard (index.html).

IMPORTANT NOTE ON DATA REALITY (read PROCESS.md for full detail):
The raw files do not contain the fields the original brief assumed
(no search-volume/difficulty/CPC, no month-by-month keyword ranking history).
This script only derives metrics that are ACTUALLY present in the source
data - nothing is invented or simulated. Where a requested metric doesn't
exist in the data, it is simply left out.

Run:  python3 generate_data.py
Reads from ../01_Raw_Data/, writes cleaned files to ../02_Cleaned_Data/
and simplified dashboard files to ../data/
"""

import pandas as pd
import numpy as np
import os
import re

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "01_Raw_Data")
CLEAN_DIR = os.path.join(os.path.dirname(__file__), "..", "02_Cleaned_Data")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

os.makedirs(CLEAN_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)


def clean_common(df):
    """Generic cleaning: drop exact duplicate rows, strip whitespace from
    string columns."""
    df = df.drop_duplicates().copy()
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()
    return df


def domain_from_url(url):
    m = re.search(r"https?://(?:www\.)?([^/]+)", str(url))
    return m.group(1) if m else str(url)


# ---------------------------------------------------------------------------
# 1. KEYWORDS  (01_SEO_Keywords_Raw.csv)
#    Real content: 15 keywords x top-25 SERP results each (title, h1,
#    snippet, url, total_result). No volume/difficulty/CPC in the source.
# ---------------------------------------------------------------------------
kw = pd.read_csv(os.path.join(RAW_DIR, "01_SEO_Keywords_Raw.csv"))
kw = clean_common(kw)
kw = kw.dropna(subset=["words", "rank"])
kw["rank"] = kw["rank"].astype(int)
kw["top_domain"] = kw["links"].apply(domain_from_url)
kw.to_csv(os.path.join(CLEAN_DIR, "Keywords_Cleaned.csv"), index=False)

keywords_overview = (
    kw.groupby("words")
    .agg(
        avg_search_results=("total_result", "mean"),
        serp_entries_tracked=("rank", "count"),
        best_rank_domain=("top_domain", "first"),
    )
    .reset_index()
    .rename(columns={"words": "keyword"})
    .sort_values("avg_search_results", ascending=False)
)
keywords_overview["avg_search_results"] = keywords_overview["avg_search_results"].round(0).astype(int)
keywords_overview.to_csv(os.path.join(DATA_DIR, "keywords_overview.csv"), index=False)

# ---------------------------------------------------------------------------
# 2. WEBSITE TRAFFIC  (02_Website_Traffic_Raw.csv)
#    Real content: 2,000 session-level rows, no dates -> no month trend
#    possible from this file. Used for traffic-source / engagement breakdown.
# ---------------------------------------------------------------------------
tr = pd.read_csv(os.path.join(RAW_DIR, "02_Website_Traffic_Raw.csv"))
tr = clean_common(tr)
tr = tr.dropna()
tr.to_csv(os.path.join(CLEAN_DIR, "Traffic_Cleaned.csv"), index=False)

traffic_sources = (
    tr.groupby("Traffic Source")
    .agg(
        sessions=("Traffic Source", "count"),
        avg_bounce_rate=("Bounce Rate", "mean"),
        avg_conversion_rate=("Conversion Rate", "mean"),
        avg_time_on_page=("Time on Page", "mean"),
    )
    .reset_index()
)
for c in ["avg_bounce_rate", "avg_conversion_rate", "avg_time_on_page"]:
    traffic_sources[c] = traffic_sources[c].round(3)
traffic_sources.to_csv(os.path.join(DATA_DIR, "traffic_sources.csv"), index=False)

# ---------------------------------------------------------------------------
# 3. BACKLINKS  (03_Backlinks_Raw.csv)
#    Real content: 28 referring-page rows with a page authority score
#    ("Page ascore") and a "First seen" date. No long text fields are
#    carried into the cleaned/simplified output.
# ---------------------------------------------------------------------------
bl = pd.read_csv(os.path.join(RAW_DIR, "03_Backlinks_Raw.csv"))
bl = clean_common(bl)
bl["First seen"] = pd.to_datetime(bl["First seen"], errors="coerce")
bl = bl.dropna(subset=["First seen"])
bl_clean = bl[["Page ascore", "Domain", "Source url", "Target url", "Anchor", "First seen"]].copy()
bl_clean = bl_clean.rename(columns={"Page ascore": "page_authority_score", "First seen": "first_seen"})
bl_clean.to_csv(os.path.join(CLEAN_DIR, "Backlinks_Cleaned.csv"), index=False)

bl_clean["month"] = bl_clean["first_seen"].dt.to_period("M").astype(str)
backlinks_trend = (
    bl_clean.groupby("month")
    .agg(new_backlinks=("domain".title() if False else "Domain", "count"),
         avg_page_authority=("page_authority_score", "mean"))
    .reset_index()
    .sort_values("month")
)
backlinks_trend["avg_page_authority"] = backlinks_trend["avg_page_authority"].round(1)
backlinks_trend["cumulative_backlinks"] = backlinks_trend["new_backlinks"].cumsum()
backlinks_trend.to_csv(os.path.join(DATA_DIR, "backlinks.csv"), index=False)

# ---------------------------------------------------------------------------
# 4. SEARCH RANKINGS / ON-PAGE FACTORS  (04_Search_Rankings_Raw.csv)
#    Real content: 500 rows of on-page SEO factors + a binary
#    "ranking_improved" outcome. No keyword names or time series -> used
#    as a ranking-factors analysis rather than a per-keyword trend.
# ---------------------------------------------------------------------------
rk = pd.read_csv(os.path.join(RAW_DIR, "04_Search_Rankings_Raw.csv"))
rk = clean_common(rk)
rk = rk.dropna()
rk.to_csv(os.path.join(CLEAN_DIR, "Rankings_Cleaned.csv"), index=False)

def da_bucket(da):
    if da < 25: return "0-24"
    if da < 50: return "25-49"
    if da < 75: return "50-74"
    return "75-100"

rk["da_bucket"] = rk["domain_authority"].apply(da_bucket)
ranking_factors = (
    rk.groupby("da_bucket")
    .agg(
        pages=("da_bucket", "count"),
        improved_rate=("ranking_improved", "mean"),
        avg_backlink_count=("backlink_count", "mean"),
        avg_content_length=("content_length", "mean"),
    )
    .reset_index()
)
ranking_factors["improved_rate"] = (ranking_factors["improved_rate"] * 100).round(1)
ranking_factors["avg_backlink_count"] = ranking_factors["avg_backlink_count"].round(1)
ranking_factors["avg_content_length"] = ranking_factors["avg_content_length"].round(0).astype(int)
order = ["0-24", "25-49", "50-74", "75-100"]
ranking_factors["da_bucket"] = pd.Categorical(ranking_factors["da_bucket"], categories=order, ordered=True)
ranking_factors = ranking_factors.sort_values("da_bucket")
ranking_factors.to_csv(os.path.join(DATA_DIR, "ranking_factors.csv"), index=False)

# ---------------------------------------------------------------------------
# 5. COMPETITOR / SOURCE-MEDIUM ANALYSIS  (05_Competitor_Analysis_Raw.csv)
#    Real content: Source/Medium x Year x Month analytics rows. This is the
#    only file with a genuine time dimension, so it drives BOTH the overall
#    traffic trend AND the competitor comparison.
# ---------------------------------------------------------------------------
comp = pd.read_csv(os.path.join(RAW_DIR, "05_Competitor_Analysis_Raw.csv"))
comp = clean_common(comp)

num_cols = ["Users", "New Users", "Sessions", "Pageviews", "Transactions", "Revenue", "Quantity Sold"]
for c in num_cols:
    comp[c] = comp[c].astype(str).str.replace(",", "", regex=False).astype(float)
comp["Bounce Rate"] = comp["Bounce Rate"].astype(str).str.replace("%", "", regex=False).astype(float)
comp["Conversion Rate (%)"] = pd.to_numeric(comp["Conversion Rate (%)"], errors="coerce")
comp = comp.dropna(subset=["Year", "Month of the year"])
comp["Year"] = comp["Year"].astype(int)
comp["Month of the year"] = comp["Month of the year"].astype(int)
comp["period"] = comp["Year"].astype(str) + "-" + comp["Month of the year"].astype(str).str.zfill(2)
comp.to_csv(os.path.join(CLEAN_DIR, "Competitor_Cleaned.csv"), index=False)

# 5a. Overall traffic trend (all sources combined, by month)
traffic_trend = (
    comp.groupby("period")
    .agg(
        sessions=("Sessions", "sum"),
        pageviews=("Pageviews", "sum"),
        users=("Users", "sum"),
        avg_bounce_rate=("Bounce Rate", "mean"),
    )
    .reset_index()
    .sort_values("period")
)
traffic_trend["avg_bounce_rate"] = traffic_trend["avg_bounce_rate"].round(1)
traffic_trend.to_csv(os.path.join(DATA_DIR, "traffic_trend.csv"), index=False)

# 5b. Competitor comparison: top sources by total sessions across the period
top_sources = (
    comp.groupby("Source / Medium")
    .agg(total_sessions=("Sessions", "sum"), total_revenue=("Revenue", "sum"), months_tracked=("period", "nunique"))
    .reset_index()
    .sort_values("total_sessions", ascending=False)
)
top_sources = top_sources[top_sources["months_tracked"] >= 8].head(7)  # sources with consistent history
top_sources["market_share_pct"] = (top_sources["total_sessions"] / top_sources["total_sessions"].sum() * 100).round(1)
top_sources.to_csv(os.path.join(DATA_DIR, "competitor_comparison.csv"), index=False)

print("Done. Cleaned files in 02_Cleaned_Data/, simplified files in data/")
for f in sorted(os.listdir(DATA_DIR)):
    print(" -", f)
