# Tinder: Likes, Matches and App Activity

A reproducible Python analysis of **one free, publicly shared Tinder dataset**:
Ashley Xu's `Tinder_Data_v3_Clean_Edition.csv`, derived from volunteer-submitted
SwipeStats exports. This repository uses that dataset exclusively.

## Research questions

1. How do users' counts of likes sent compare with their total matches?
2. How do likes, matches and recorded-day rates differ by recorded gender?
3. How is app-opening frequency associated with matches and likes sent?
4. How concentrated are match counts across the observed users?

The analysis retains descriptive summaries, participant bootstrap intervals,
Spearman correlations, three negative-binomial models, and Lorenz/Gini measures.
Correlations are reported both pooled and separately by recorded gender, with
sample sizes and exploratory p-values, in the JSON outputs and findings report.
See [research design and equations](docs/RESEARCH_DESIGN.md) and the
[data dictionary](docs/DATA_DICTIONARY.md).

## Dataset and limitations

[Ashley Xu's source repository](https://github.com/Ashley-Xu/AIPIFinalDataset)
hosts the [CSV](https://github.com/Ashley-Xu/AIPIFinalDataset/blob/main/Tinder_Data_v3_Clean_Edition.csv).
The verified file contains **1,209 participant rows**, including **1,059 M-coded
and 150 F-coded users** (87.6% and 12.4%). These are source counts before exclusions.
The current cleaning rules retain 983 rows; 226 have zero recorded days.
See [provenance, checksum and verification](docs/DATA_PROVENANCE.md).

- **Self-selection:** volunteers submitted their exports. This is not a
  representative sample of Tinder users or the wider dating population.
- **Gender imbalance:** the small female-coded group and potentially different
  partner pools limit comparisons. The source's M/F categories are not a complete
  representation of gender.
- **Likes sent only:** incoming likes, profile impressions and the initiator of
  each match are unavailable. `matches / likes_sent` is a descriptive ratio,
  not a conversion probability; it can exceed one.
- **App openings, not screen time:** `sum_app_opens` counts opening events. It
  cannot measure minutes of use.
- **Recorded days, not calendar time:** upstream code calculates `no_of_days`
  as `len(appOpens)`. This counts dates represented in the opening log, not
  elapsed days since account creation or necessarily days with positive activity.
  Rates and regression offsets use this imperfect denominator. They do not
  establish calendar-day match rates or causal effects of time spent.
- **Different observation windows:** totals can span different periods. Outliers,
  selection and reverse causation remain relevant. Bootstrap intervals do not
  correct these limitations.

Optional age and partner-interest fields are loaded but are **not model
covariates**. Partner-preference subgroup analysis is not currently implemented.
Match concentration does not establish desirability, partner status or relationship quality.

## Run the study

Use Python 3.10 or newer. Clone this repository and run commands from its root:

```bash
git clone https://github.com/Louis-Finegan/Online-Dating-Likes-Matches-Analysis.git
cd Online-Dating-Likes-Matches-Analysis
python -m venv .venv
```

Activate the environment on macOS/Linux:

```bash
source .venv/bin/activate
```

Or in Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Then install and run:

```bash
python -m pip install -r requirements.txt
python -m scripts.run_study
```

No account or API key is required. The first run downloads the CSV into `data/`,
validates its required columns and records a SHA-256 checksum and download time.
Existing downloads are reused. Results are written to `results/tinder/`.
Raw data and generated results remain local and are ignored by Git.

The two steps can also run separately:

```bash
python -m scripts.download_data
python -m scripts.run_analysis
```

For an offline copy of **the same source CSV**, or a separate output directory:

```bash
python -m scripts.run_analysis --input data/Tinder_Data_v3_Clean_Edition.csv --output results/local_study --bootstrap 2000 --seed 42
```

`--bootstrap` requires at least 100 draws. Reusing an output directory overwrites
its generated files. `python -m scripts.download_data --force` replaces the local
CSV only after the new download passes validation; retain your old copy if needed.
Schema validation alone does not prove a local file's identity: compare its checksum
with the provenance record.

## Repository structure

```text
Online-Dating-Likes-Matches-Analysis/
├── dating_research/          # Reusable Tinder analysis
│   ├── dataset.py            # Single source URL, filename and default paths
│   ├── source.py             # Selected-column loading, validation and rates
│   ├── statistics.py         # Summaries, bootstrap, correlations and Gini
│   ├── models.py             # Three negative-binomial specifications
│   ├── figures.py            # Five descriptive figures, PNG and PDF
│   ├── model_figures.py      # Model intervals, prediction curves and plotted CSVs
│   └── report.py             # Findings generated from the analysis
├── scripts/                 # Download, analyse and combined entry points
├── tests/                   # Network-free unit and pipeline tests
├── docs/                    # Research design, dictionary and provenance
├── data/                    # Local CSV and download manifest; README tracked
├── results/                 # Local generated outputs; README tracked
├── requirements.txt         # Analysis dependencies
└── requirements-dev.txt     # Analysis dependencies plus test runner
```

Open `results/tinder/FINDINGS.md` after running. The figures also include model
rate ratios with 95% confidence intervals and expected match-rate curves for
Models 2 and 3 with pointwise 95% confidence bands for the mean. These are not
individual prediction intervals. Plotted estimates are exported as CSVs; see
the [output guide](results/README.md) for interpretation. The output directory also holds
the cleaning audit, input manifest, group summaries, uncertainty estimates,
correlations, model diagnostics and figures. See the [output guide](results/README.md).
Check model convergence before interpreting coefficients.

## Tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Tests use synthetic fixtures only to verify the software, including the full
analysis pipeline and safe download replacement. They require no network and
their outputs are not empirical findings.

## Data handling

The source CSV includes sensitive profile fields. The loader reads only the
columns listed in the data dictionary; it does not export participant tables.
Some figures show individual observations of selected counts/rates, so review
outputs before sharing. Source attribution and use conditions are recorded in
[DATA_PROVENANCE.md](docs/DATA_PROVENANCE.md).

### Source-listed education

Model 4 adds the source's binary education category to Model 2 without
interactions. It exports coefficient tests, a same-sample likelihood-ratio test,
and coefficient/prediction figures. These categories describe the source field,
not verified qualifications. Missing or unrecognized education does not remove
users from the existing models. See the output guide for coding and limitations.

### Assumed employment from profession

Model 5 adds a binary proxy derived from `jobTitle` to the gender/likes/activity
baseline, without education or interactions. Under the requested rule, `False`
and `unknown` mean assumed unemployed; other nonempty titles mean assumed
employed. This measures a listing-based assumption, not verified employment.
Coefficient tests, same-sample likelihood-ratio tests, confidence plots and CSVs
are generated as for the education model. Missing titles affect only Model 5.

### Opens and likes interaction

Model 6 adds `log_opens_rate:log_likes_rate` to Model 2, with additive gender and
no education/employment terms. It includes coefficient tests, a same-sample
likelihood-ratio test, and Figure 8 showing predicted mean match rates at low,
median and high liking rates by gender. PNG/PDF figures and plotted CSV values
are generated by the usual analysis command; see the output guide for caveats.
