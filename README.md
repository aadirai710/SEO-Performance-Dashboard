# Signal — SEO Performance Dashboard

An internship project: an interactive dashboard covering keyword visibility, traffic, backlinks, and on-page ranking factors, built from five independent Kaggle CSV exports.

**Important context before you look at anything else:** the five raw files do not match a single connected SEO analytics export — each one uses a different structure, and some don't contain the fields a typical SEO brief would expect (no search volume, keyword difficulty, or CPC anywhere in the data; no keyword-level ranking history). Rather than inventing numbers to fill those gaps, this project uses only what's actually in the data and documents the gaps openly. See `PROCESS.md` for the full reasoning and every assumption made.

## How to view the dashboard

Open `index.html` in any browser — double-click it, no server or internet connection required. All charts (Chart.js) and data are embedded directly in the file.

## Data sources

Five raw CSV exports (originally from Kaggle, provided directly for this project — no live links to preserve, see `01_Raw_Data/` for the files as received):

| File | Real content |
|---|---|
| `01_SEO_Keywords_Raw.csv` | 15 keywords, each with its top-25 ranked SERP results (title, snippet, URL, indexed-result count) |
| `02_Website_Traffic_Raw.csv` | 2,000 individual sessions with channel, bounce rate, and conversion data (no dates) |
| `03_Backlinks_Raw.csv` | 28 referring-page rows with a page authority score and a "first seen" date |
| `04_Search_Rankings_Raw.csv` | 500 pages audited for on-page SEO factors, with a binary "ranking improved" outcome |
| `05_Competitor_Analysis_Raw.csv` | Monthly traffic by anonymized "Source/Medium" code, 2019–2020 |

## File structure

```
seo-dashboard/
├── index.html                    Interactive dashboard (self-contained, works offline)
├── dashboard_preview.png         Static screenshot of the Overview tab
│
├── 01_Raw_Data/                  The 5 CSVs exactly as provided
├── 02_Cleaned_Data/               Deduplicated, type-corrected versions of each raw file
├── data/                          Simplified CSVs that feed the dashboard directly
│   ├── keywords_overview.csv
│   ├── traffic_trend.csv
│   ├── traffic_sources.csv
│   ├── backlinks.csv
│   ├── ranking_factors.csv
│   └── competitor_comparison.csv
│
├── scripts/
│   └── generate_data.py          Cleans 01_Raw_Data/ → 02_Cleaned_Data/ + data/
│
├── 03_Analysis/
│   ├── Key_Findings.docx
│   └── Recommendations.docx
│
├── PRESENTATION/
│   ├── Dashboard_Screenshots.pptx
│   └── assets/                   Screenshots used inside the deck
│
├── README.md                     This file
└── PROCESS.md                    Full methodology, cleaning steps, and assumptions
```

## Running the data pipeline yourself

```bash
cd scripts
python3 generate_data.py
```

Requires `pandas` and `numpy`. Reads from `../01_Raw_Data/`, writes cleaned files to `../02_Cleaned_Data/` and the dashboard's data files to `../data/`. Re-running it is safe — it always regenerates fresh output from the raw files.

## What each dashboard section actually shows

- **Overview** — top-line KPIs plus the one real time series available (monthly traffic, 2019–2020) and the most contested keywords.
- **Keywords** — the 15 tracked keywords ranked by total indexed results (a proxy for competitiveness, since no volume/difficulty data exists), plus a separate on-page ranking-factors breakdown from the 500-page audit.
- **Traffic** — the monthly trend and the 2,000-session channel snapshot, shown side by side rather than merged, since they don't share a time axis.
- **Backlinks** — month-by-month growth and average linking-page authority from the 28 logged links.
- **Competitors** — the "Source/Medium" file read as a channel comparison. The codes (A, B, C…) are not named competitor sites; treat this section as internal channel comparison, not third-party benchmarking.

See `PROCESS.md` for why each of these choices was made.
