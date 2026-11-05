# Generated results

Run `python -m scripts.run_study` from the repository root. Generated files in
`results/tinder/` are ignored by Git; this guide is tracked.

| File | Contents |
|---|---|
| `FINDINGS.md` | Narrative findings and measurement caveats |
| `audit.json` | Input/usable counts, exclusions, gender counts and limitations |
| `dataset_manifest.json` | Source attribution, actual input SHA-256 and run settings |
| `overall.json` | Totals, medians, match-count Gini and top-decile share |
| `gender_summary.csv` | Descriptive summaries by recorded gender |
| `bootstrap_ci.json` | Female/Male pooled matches-per-recorded-day ratio and interval |
| `correlations.json` | Three Spearman rate associations |
| `correlations_by_gender.json` | The same three associations within each recorded gender, with pairwise N, rho and p-value |
| `models.csv` | Negative-binomial coefficients and rate ratios |
| `model_diagnostics.json` | Model status, formula, sample size and fit diagnostics |
| `figures/` | Five descriptive plots, up to three coefficient plots and one model-curve comparison, each in PNG and PDF format |
| `figures/coefficients_<model>.csv` | Plotted rate ratios and 95% Wald intervals (intercept and dispersion omitted) |
| `figures/model_prediction_curves.csv` | Plotted expected matches/recorded day, pointwise 95% mean confidence limits, and reference likes rate |

Use `--output results/<run-name>` to keep runs separate. Generated files in a
reused directory are overwritten. Raw CSVs are never copied into the results.
Inspect convergence status before interpreting models. An unstable fit is not a
supported result. Synthetic test outputs are software checks, not research data.

The legacy summary columns `matches_per_day_median`, `likes_per_day_median` and
`opens_per_day_median` all use **recorded app-open log dates**, not calendar days.

## Exploratory model plots

`06_coefficients_<model>` shows rate ratios on a log axis, with 95% Wald
confidence intervals and a reference at 1. Continuous terms represent one unit
of `log(1 + rate)`, not one extra like/open. In the interaction model the gender
contrast is at zero opens; the interaction is a ratio of rate ratios.

`07_model_match_rate_curves` compares Models 2 and 3 by recorded gender. Likes
per recorded day are fixed at the fitted sample pooled median (exported to CSV),
and expected counts use one recorded day (offset zero). Each curve covers its
own group's observed opening-rate range; rugs show observed support. The x-axis
is symmetric-log with a linear region up to one open per recorded day.

Bands are pointwise 95% Wald confidence intervals for the conditional mean:
`exp(X beta +/- 1.96 sqrt(X Cov(beta) X'))`, using all coefficient covariances.
They are neither individual prediction intervals nor simultaneous bands.
Only converged fits with finite parameters/standard errors produce model plots.
Skipped, failed and unstable fits remain documented in the diagnostics.
Use a fresh output directory to avoid retaining figures from an older run.
These are exploratory associations, not causal effects; recorded days are log
entries rather than verified calendar tenure.
