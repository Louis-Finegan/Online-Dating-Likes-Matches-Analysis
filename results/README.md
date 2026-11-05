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
| `figures/` | Five descriptive plots, up to five coefficient plots and one model-curve comparison, each in PNG and PDF format |
| `figures/coefficients_<model>.csv` | Plotted rate ratios and 95% Wald intervals (intercept and dispersion omitted) |
| `figures/model_prediction_curves.csv` | Plotted expected matches/recorded day, pointwise 95% mean confidence limits, and reference likes rate |

Use `--output results/<run-name>` to keep runs separate. Generated files in a
reused directory are overwritten. Raw CSVs are never copied into the results.
Inspect convergence status before interpreting models. An unstable fit is not a
supported result. Synthetic test outputs are software checks, not research data.

The legacy summary columns `matches_per_day_median`, `likes_per_day_median` and
`opens_per_day_median` all use **recorded app-open log dates**, not calendar days.

## Exploratory model plots

`06_coefficients_<model>` shows rate ratios on a linear axis, with 95% Wald
confidence intervals and a reference at 1. Continuous terms represent one unit
of `log(1 + rate)`, not one extra like/open. In the interaction model the gender
contrast is at zero opens; the interaction is a ratio of rate ratios.

`07_model_match_rate_curves` compares Models 2 and 3 by recorded gender, plus Model 4 by gender and source-listed education and Model 5 by gender and assumed employment. Likes
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

## Education model (Model 4)

`education_adjusted` adds `C(education_group)` to Model 2, with no interactions.
The two exact source strings map to `No listed education` (reference) and
`Listed education`. They must not be interpreted as verified qualifications or
absence of schooling; the original field's missingness/encoding is uncertain.
Unrecognized/missing strings remain missing, and only this model excludes them.
The audit records education category counts and missing/unrecognized values.
Both education categories need at least ten observations; otherwise this model
is skipped. No degrees or ordered education scores are inferred.

`models.csv` contains coefficient Wald p-values and 95% rate-ratio intervals as
for other models. `model_diagnostics.json` additionally records an education
likelihood-ratio test against Model 2 refitted on the identical complete-case
sample. Its null is that all education coefficients equal zero. Tests are
exploratory, model-based, and unadjusted for multiple comparisons.
The curve CSV includes `education_group` for Model 4; each curve uses that
specific gender/education subgroup's observed opening range. Conditional likes
are fixed at the full fitted sample median. Sparse subgroups imply weak support.

## Profession proxy model (Model 5)

`employment_adjusted` adds `C(employment_group)` to Model 2 **instead of
education**, with no interactions. Following the requested assumption, trimmed,
case-insensitive `False` and `unknown` in `jobTitle` map to `Unemployed (assumed)`
(reference); every other nonempty recorded value maps to `Employed (assumed)`.
This intentionally includes student/ambiguous titles: it is a job-listing proxy,
not verified employment status. Blank/missing values remain missing rather than
being classified as employed. An absent optional column skips this model.
Raw profession strings are discarded after classification and are not exported.

As for Model 4, coefficients have Wald p-values and 95% intervals, and diagnostics
include a same-sample likelihood-ratio test versus the activity baseline.
Both proxy groups require at least ten observations. The audit records counts,
missingness, and the rule. Prediction curves include `employment_group`, use
subgroup-specific observed opening ranges, and hold likes at the pooled median.
Dashed lines show the assumed-employed or education-listed categories; colors
retain gender. All tests are exploratory and unadjusted for multiple comparisons.
