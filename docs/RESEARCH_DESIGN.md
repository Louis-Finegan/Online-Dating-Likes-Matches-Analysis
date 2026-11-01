# Research design: what we can estimate and what we cannot

## Working title

**Tinder: Likes, Matches and App Activity**

## Study population

The public CSV consists of voluntary Tinder export submissions via SwipeStats,
reshared by Ashley Xu. This is a **convenience sample**, not a probability sample.
The author reports use-permission for a subset; verify the original license
before redistributing any part of the data or publishing individual observations.

Raw CSVs can include sensitive profile fields. Our loader only reads the
analysis columns listed in the data dictionary. Scatter plots show individual
count/rate observations; other plots summarise distributions. See the
[verified source counts and checksum](DATA_PROVENANCE.md): 1,209 rows before
cleaning, with 1,059 M-coded and 150 F-coded users. This gender imbalance limits
precision and comparisons; resampling does not remove selection bias.

## Hypotheses / estimands

**H1 (descriptive):** What is the sample proportion whose count of sent likes
exceeds their total match count? `P(L_s > M)` over observed participants.
This is expected in a selective platform, but does not by itself establish a
behavioural effect: many matches arise from incoming likes, not just sent likes.

**H2 (gender):** Compare observed distributions of `L_s`, `M`, and `M/D`
between male- and female-coded participants. Report descriptive rate ratio

    R = [sum_{Female} M_i / sum_{Female} D_i]
        / [sum_{Male} M_i / sum_{Male} D_i].

Bootstrap participants within each recorded gender group (not individual
interactions) to provide a 95% percentile interval. **Do not interpret this
interval as design-based uncertainty for all Tinder users.** Gender groups
may face very different dating pools, orientation distributions and paywall
constraints. The dataset does not provide enough context to identify why.

**H3 (activity):** Is app-open frequency associated with matches? Examine rank
correlations for opens/recorded day, likes/recorded day and matches/recorded day. App opens are an imperfect
proxy for activity; this does **not** measure minutes or establish that longer
usage causes more matches. Reverse causation is plausible.

Repeat the same three Spearman comparisons within each recorded gender and
report pairwise sample size, rho and two-sided p-value in
`correlations_by_gender.json` and `FINDINGS.md`. The pooled `correlations.json`
remains unchanged. P-values use the asymptotic approximation and are unadjusted
for multiple testing; smaller-group p-values deserve particular caution.
A smaller sample does not automatically imply statistical nonsignificance.
Differences in coefficients or p-values are not a formal test of differences
between genders. Shared denominators and other confounding remain after stratification.

**H4 (distribution):** Characterise inequality using Gini on total match counts,
Lorenz curves and the share of matches held by the top 10% of observed users.
These quantify outcomes, not actual profile impressions or desirability.

## Modelling

For participant i with M_i matches and D_i recorded app-open dates, fit

    M_i ~ NegativeBinomial(mu_i, alpha)
    log(mu_i) = log(D_i) + beta_0 + beta_G Gender_i
             + beta_L log(1 + LikesSent_i / D_i)
             + beta_A log(1 + AppOpens_i / D_i).

The first specification uses gender alone; the second is shown above.
A third specification adds the gender-by-log-opens-rate interaction to the second.
Age and partner preference are not included in these models.
The model uses an **offset** of `log(D_i)` to approximate exposure, but `D_i` is
not calendar tenure: it is the count of dates with recorded app-open data.
As both numerator and denominator come from related activity histories, this
choice can induce dependence between predictors. Coefficients are exploratory.

Check convergence (`model_diagnostics.json`); do not interpret an unstable fit.
The `alpha` parameter measures overdispersion, not a rate ratio. For other
coefficients, exponentiating the estimate yields an incidence rate ratio for
one unit of the relevant predictor, holding the other terms constant.

No causal claim can be supported without accounting for selection, unmeasured
exposure, subscription, geographic pool size, orientation, and feedback between
matches and app use. No multiple-comparison adjustment is made to exploratory
correlations; treat reported p-values as descriptive diagnostics.

## Critical measurement distinctions

- `L_s` counts **likes sent**, while the author's CSV does not show likes received.
- `M` counts total matches, not necessarily matches arising from sent likes.
- `M/L_s` may exceed one and is **not a binomial response probability**.
- `D` counts dates with app opens in a source extraction, not total tenure.
- `A` counts app-open events, not screen-time minutes.
- Users may upload data spanning different time periods and account states.
- The dataset has no exposure/impression counts to distinguish preference from visibility.
- The cross-section includes no information about relationship formation quality.

## Interpretation boundary

Match-count inequality cannot establish partner-status preferences, desirability
or relationship quality. Those outcomes are outside this dataset's scope.

## Figures and tables

1. Log(1+count) distributions of sent likes and matches.
2. Likes–matches scatter with gender grouping.
3. Matches per recorded app-open day by gender.
4. App opens per recorded day versus matches per recorded day.
5. Lorenz curves and Gini for the match-count distribution.
6. Group summary, bootstrap interval, rank correlations, count-model estimates.

## References and provenance

- Source: https://github.com/Ashley-Xu/AIPIFinalDataset
- Raw dataset: https://github.com/Ashley-Xu/AIPIFinalDataset/blob/main/Tinder_Data_v3_Clean_Edition.csv
- SwipeStats research context: https://www.swipestats.io/research

The project uses this Tinder CSV exclusively and makes no claim to a
representative sample. Full source verification is in [DATA_PROVENANCE.md](DATA_PROVENANCE.md).
