# PROCESS.md — Methodology

## 1. Starting point vs. reality

The original project brief assumed five connected SEO analytics exports: keywords with search volume/difficulty/CPC, monthly website traffic, backlinks with domain authority growth, 6-month keyword ranking history, and named-competitor comparisons.

After loading and inspecting all five raw files, none of them matched that assumption. This section documents exactly what each file turned out to contain, since that finding drove every decision after it.

| # | File | Assumed | Actual |
|---|---|---|---|
| 1 | `01_SEO_Keywords_Raw.csv` | Keywords + volume/difficulty/CPC/rank | 375 rows = 15 keywords × their top-25 SERP results (title, H1, snippet, URL, indexed-result count). No volume, difficulty, or CPC field exists anywhere in the file. |
| 2 | `02_Website_Traffic_Raw.csv` | Monthly traffic/visitors/pageviews | 2,000 session-level rows (page views, session duration, bounce rate, traffic source, conversion rate). **No date field of any kind** — a monthly trend cannot be derived from this file. |
| 3 | `03_Backlinks_Raw.csv` | Backlink count + domain authority over time | 28 real referring-page rows (source title/URL, target URL, anchor text, a "Page ascore" authority score, "First seen" date) — but several rows also carry full scraped news-article text unrelated to SEO metrics. |
| 4 | `04_Search_Rankings_Raw.csv` | Keyword rankings over 6 months | 500 rows of on-page SEO factors (content length, keyword density, internal/external links, DA, PA, backlink count) plus a binary `ranking_improved` outcome. **No keyword names and no time series** — this is a factor-analysis dataset, not a ranking-history dataset. |
| 5 | `05_Competitor_Analysis_Raw.csv` | Named competitor site comparison | 250 rows of Source/Medium × Year × Month analytics (users, sessions, revenue, etc.), 2019–2020. Sources are anonymized single/double-letter codes (A, B, C, "l.M", etc.), not named competitor domains. This is the **only file with a genuine time series**. |

A quick technical note: `wc -l` on the raw files reported far higher row counts than the true row counts (e.g. 276,018 for file 1, which actually has 375 data rows) because several text fields contain embedded newlines. Row counts throughout this document are `pandas`-parsed row counts, not line counts.

## 2. Decision: use only what's real, keep the original folder/file structure

Given the mismatch, the options were: (a) invent plausible numbers to match the original brief, (b) leave placeholders everywhere something was missing, or (c) build every section from what the data actually supports and say so explicitly. Option (c) was chosen — confirmed directly by the project owner rather than assumed. No search volume, keyword difficulty, CPC, or per-keyword ranking history appears anywhere in this project, because none of it exists in the source data.

The originally requested folder structure (`01_Raw_Data/`, `02_Cleaned_Data/`, `data/`, `scripts/`, `03_Analysis/`, `PRESENTATION/`) was kept as specified. One addition: a `Competitor_Cleaned.csv` was added to `02_Cleaned_Data/` alongside the four originally named cleaned files, since the original brief's "4 cleaned CSVs" only accounted for 4 of the 5 raw sources.

## 3. Cleaning steps (`scripts/generate_data.py`)

Applied to every file:
- Drop exact duplicate rows (`drop_duplicates()`).
- Strip leading/trailing whitespace from all string columns.
- Drop rows missing required fields for that file's analysis (e.g. rows with an unparseable date).

File-specific steps:
- **Keywords (1):** parsed `rank` as integer; extracted a `top_domain` from each result URL via regex.
- **Traffic (2):** dropped any residual nulls; no further transformation needed (already close to clean).
- **Backlinks (3):** parsed `First seen` as a date and dropped unparseable rows; kept only the metric-relevant columns (`Page ascore`, `Domain`, `Source url`, `Target url`, `Anchor`, `First seen`) — the scraped article `text`/`title` columns were dropped since they carry no SEO metric and, in a few rows, unrelated news content.
- **Rankings (4):** dropped nulls; bucketed `domain_authority` into four bands (0–24, 25–49, 50–74, 75–100) for the ranking-factors aggregation.
- **Competitor/Source-Medium (5):** stripped thousands-separator commas and `%` signs from numeric-looking string columns (`Users`, `Sessions`, `Bounce Rate`, etc.) before converting to numeric types; built a `period` (`YYYY-MM`) column from `Year` + `Month of the year`.

## 4. How each simplified dashboard file was derived

| Output (`data/*.csv`) | Source file(s) | Derivation |
|---|---|---|
| `keywords_overview.csv` | File 1 | Grouped by keyword: mean `total_result` (search-competition proxy), count of tracked SERP entries, and the domain holding rank #1. |
| `traffic_sources.csv` | File 2 | Grouped by `Traffic Source`: session count, average bounce rate, average conversion rate, average time on page. |
| `backlinks.csv` | File 3 | Grouped by month (from `First seen`): new-backlink count, average page authority, running cumulative total. |
| `ranking_factors.csv` | File 4 | Grouped by DA band: page count, % with `ranking_improved = 1`, average backlink count, average content length. |
| `traffic_trend.csv` | File 5 | Grouped by `period` across **all** Source/Medium rows: summed sessions/pageviews/users, average bounce rate. This is the "traffic trend" the brief asked for — it comes from the competitor file because that's the only file with dates. |
| `competitor_comparison.csv` | File 5 | Grouped by `Source / Medium`, filtered to sources with ≥8 months of tracked history (to exclude one-off/incomplete codes), ranked by total sessions, with each source's share of total sessions computed. |

## 5. Why traffic and competitor sections both use File 5

Files 2 and 5 both relate to "traffic," but they don't share a time axis or a channel taxonomy, so they were **not merged**:
- File 2 gives channel-level engagement detail (bounce rate, conversion, time on page) as a single 2,000-session snapshot with no dates.
- File 5 gives month-by-month totals across anonymized source codes, with no engagement-quality metrics.

The dashboard's Traffic tab shows both, side by side, labeled separately. The Competitors tab reuses File 5 from a different angle (per-source totals and share, instead of per-month totals) — this is the same underlying data answering two different questions, not double-counting.

## 6. Known limitations, stated plainly

- **No search volume/difficulty/CPC anywhere.** The Keywords section works from indexed-result count as a competitiveness proxy, which is not the same signal as search volume.
- **File 2 has no dates.** Its numbers describe a snapshot, not a trend — do not read the Traffic tab's engagement breakdown as time-based.
- **File 4 has no keyword names.** The ranking-factors analysis describes generic on-page pages, not the same 15 keywords tracked in the Keywords tab. These two are separate analyses that happen to share a section.
- **File 5's source codes are anonymized** (and a few, like `l.M` and `l.K`, look like data-entry artifacts). "Competitor" language was avoided in favor of "channel"/"source" throughout, and the dashboard flags the concentration in source "A" (48.2% of sessions) as something to verify before repeating externally.
- **File 3 is small (28 rows) and short-dated (5 months).** Trend lines from this much data should be read directionally, not as a robust statistical trend.

## 7. Dashboard design decisions

- Built as a single self-contained HTML file with Chart.js **inlined** (not loaded from a CDN), so it opens and renders correctly offline — no internet connection needed to view it, and no risk of a broken chart if a CDN is unreachable.
- Palette and typography (Fraunces serif display + IBM Plex Sans body, ink-navy/terracotta/teal/amber palette) were chosen specifically for this "analytics ledger" subject matter rather than a generic dashboard template.
- Every section that reuses or reinterprets a dataset (Traffic vs. Competitors both from File 5; Keywords vs. Rankings both nominally about "keywords" but actually different datasets) carries an explicit note in the UI saying so, rather than leaving the connection implicit.

## 8. Challenges and how they were resolved

- **Row-count confusion from embedded newlines** (Section 1) — resolved by parsing with `pandas` and trusting `len(df)`, not `wc -l`.
- **Chart.js CDN blocked in the build/test sandbox** — resolved by installing `chart.js` via npm and inlining the UMD bundle directly into `index.html`, which also happens to make the shipped file more reliable for the end user (no external dependency at all).
- **A pie chart in the Competitors tab appeared blank in an early screenshot** — traced to a screenshot taken before Chart.js's entry animation had painted its first frame, not a real rendering bug. Confirmed by re-screenshotting with a longer wait; no code change was needed.
- **A metrics-summary table in the presentation deck initially overflowed the slide boundary** — fixed by reducing row height and font size slightly so all 6 rows fit within the slide margins.
- **Decorative accent stripes on cards in an early presentation draft** — removed and replaced with small color-coded dot indicators, in line with keeping visual devices meaningful rather than purely decorative.
