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
| `figures/` | Five plots, each in PNG and PDF format |

Use `--output results/<run-name>` to keep runs separate. Generated files in a
reused directory are overwritten. Raw CSVs are never copied into the results.
Inspect convergence status before interpreting models. An unstable fit is not a
supported result. Synthetic test outputs are software checks, not research data.

The legacy summary columns `matches_per_day_median`, `likes_per_day_median` and
`opens_per_day_median` all use **recorded app-open log dates**, not calendar days.
