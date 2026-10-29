# Likes, Matches and Activity on Tinder

A reproducible Python research project investigating **likes sent, matches obtained,
recorded app-open activity and gender differences** using one publicly shared dataset.

The motivation is understanding dating apps such as Hinge; **the actual observations
are from Tinder, not Hinge**. Do not extrapolate findings to Hinge without data.

## Research questions

1. Do users record more **likes sent** than **total matches**?
2. How do observed likes, matches, and match-rate distributions differ across the
   male/female gender categories available in the source?
3. Is the frequency of **app opens** associated with match counts after adjusting
   for the number of dates in the app-open log and likes sent?
4. How concentrated are matches among users (Gini and top-10% share)?

`matches / likes_sent` is **not** the probability that a sent like became a
match; we lack which side initiated each recorded match. Likewise, app opens are
**not** minutes of app usage, and `no_of_days` is not independently verified
calendar tenure. See [the study design](docs/RESEARCH_DESIGN.md).

## Data

Author/host: [Ashley Xu, AIPIFinalDataset](https://github.com/Ashley-Xu/AIPIFinalDataset)
(`Tinder_Data_v3_Clean_Edition.csv`). According to its author, it was sourced
from volunteer-submitted SwipeStats exports with permission. The file publicly
listed in October 2026 had **1,209 participant rows**, subject to validation and
exclusion rules. It includes `swipe_likes`, `no_of_matches`, `sum_app_opens`,
`no_of_days`, `gender`; age and partner-interest codes are optional. No incoming
likes or genuine screen-time minutes are available.

**The original CSV is deliberately not included.** It contains additional
sensitive fields such as birth dates and city names. The loader only reads a
small, predefined set of non-identifying columns, and the downloader writes the
source file into the ignored `data/` directory. Review source license and
privacy conditions before publishing any derived data.

## Quick start (Ubuntu, Debian, WSL)

From the extracted project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m scripts.run_study
```

No account, API key, Github push or Hinge login is necessary.

`python -m scripts.run_study` performs both steps. To run them separately, use
`python -m scripts.download_data` and then `python -m scripts.run_analysis`.

The downloader verifies the required CSV columns and stores a SHA-256 checksum
and download date next to the local file. Network access is needed **only** to
download the publicly hosted CSV. Reuse an existing download or supply a local
file when offline:

```bash
python -m scripts.run_analysis --input /absolute/path/to/your.csv \
    --output results/local_study --bootstrap 2000 --seed 42
```

To force a fresh source download:

```bash
python -m scripts.download_data --force
```

## Results

When executed, the project generates the following **from your actual data**:

```text
results/tinder/
    FINDINGS.md                 # Narrative descriptive report + caveats
    audit.json                  # Cleaning, exclusions, source limitations
    overall.json                # Total likes, matches, Gini, top-decile share
    gender_summary.csv          # Gender-separated descriptive measures
    bootstrap_ci.json           # Female/Male matches/recorded-day rate ratio
    correlations.json           # Spearman associations
    model_diagnostics.json      # Model convergence, formula, n and AIC
    models.csv                  # Negative-binomial coefficient table
    dataset_manifest.json      # Input SHA-256 + provenance
    figures/
        01_like_match_distributions.{png,pdf}
        02_likes_vs_matches.{png,pdf}
        03_match_rates_by_gender.{png,pdf}
        04_app_opens_vs_matches.{png,pdf}
        05_lorenz_match_counts.{png,pdf}
```

The statistical analysis uses:

- Descriptive counts and rates, without confusing likes sent with likes received.
- Participant-level bootstrap intervals for **descriptive** gender rate ratios.
- Spearman correlations for monotonic associations.
- Negative binomial regression with offset `log(recorded_days)` and a gender–activity interaction.
- Gini coefficients and Lorenz curves for match-count concentration.

Do not treat results as representative population estimates, and do not label
any results as causal, Hinge-specific, or evidence of hypergamy.

## Validate the code

```bash
python -m pytest -q
```

Unit tests use **synthetic input solely to check the software**; simulated
values are never included in empirical reports.

## Layout

```text
dating_likes_matches_study/
├── dating_research/
│   ├── source.py          # import, validate, derive descriptives
│   ├── statistics.py      # Gini, bootstraps, correlations
│   ├── models.py          # negative binomial regression
│   ├── figures.py         # plots saved locally
│   └── report.py          # Markdown findings from actual records
├── scripts/
│   ├── download_data.py   # validated source download
│   ├── run_analysis.py    # independent analysis of a local CSV
│   └── run_study.py       # one-command download and analysis
├── tests/
├── docs/
│   ├── RESEARCH_DESIGN.md
│   └── DATA_DICTIONARY.md
├── data/                   # source download saved locally, excluded from git
└── requirements.txt
```

## Next-stage research

The Hinge-specific question requires actual Hinge user records containing sent
likes, received likes, match origin, app exposure and separately measured screen
minutes. An analysis of aggregate likes/matches alone cannot identify
socioeconomic hypergamy; that would need paired partner attributes and choices.
