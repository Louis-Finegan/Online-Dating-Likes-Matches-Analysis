"""Generate a self-contained Markdown report from observed results only."""
from __future__ import annotations
from pathlib import Path
import json


def _fmt(x, places=3):
    if x is None:
        return 'Not estimated'
    return f'{x:,.{places}f}'


def write_report(out: str | Path, audit, totals, groups, bootstrap, correlations, models,
                 gender_correlations=None):
    out = Path(out)
    source = (out / 'dataset_manifest.json')
    manifest = json.loads(source.read_text()) if source.exists() else {}
    lines = [
        '# Likes, Matches and App Activity: Exploratory Findings', '',
        '> Generated from observed CSV records. This document is descriptive and',
        '> exploratory evidence from the sole Tinder dataset, not a causal study.', '',
        '## Source and sample', '',
        '- Dataset: publicly shared, user-contributed **Tinder** summary CSV (Ashley Xu / SwipeStats).',
        f'- Usable participants: **{audit["usable_rows"]:,}** of {audit["original_rows"]:,} rows.',
        f'- Download/source SHA-256: `{manifest.get("sha256", "not recorded; run downloader first")}`.',
        '- All results are from volunteer-submitted Tinder exports. No population sampling weights.',
        '- The variable `no_of_days` means dates represented in app-open records.', '',
        '## Overall descriptive findings', '',
        f'- Likes sent, summed over users: **{totals["likes_sent_total"]:,}**.',
        f'- Matches, summed over users: **{totals["matches_total"]:,}**.',
        f'- Median sent likes per participant: **{_fmt(totals["likes_sent_median"], 1)}**.',
        f'- Median total matches per participant: **{_fmt(totals["matches_median"], 1)}**.',
        f'- Share with more likes sent than total matches: **{_fmt(100 * totals["share_likes_sent_exceed_matches"],1)}%**.',
        f'- Match-count Gini coefficient: **{_fmt(totals["gini_matches"])}**.',
        f'- Share of matches held by the top 10% of observed users: **{_fmt(100 * totals["top_10pct_match_share"],1)}%**.', '',
        '**Important:** `matches/likes_sent` is NOT a genuine match-conversion',
        'probability because matches may have started from incoming likes.', '',
        '## Gender-group descriptive comparison', '',
        '| Gender | Users | Median likes sent | Median matches | Pooled matches / recorded day | Match-count Gini |',
        '|---|---:|---:|---:|---:|---:|',
    ]
    for _, row in groups.iterrows():
        lines.append('| {} | {:,} | {} | {} | {} | {} |'.format(
            row['gender'], int(row['users']), _fmt(row['likes_sent_median'], 1),
            _fmt(row['matches_median'], 1), _fmt(row['pooled_matches_per_recorded_day']),
            _fmt(row['match_count_gini'])))
    lines += ['', 'For the pooled Female/Male recorded-day match-rate ratio:']
    if bootstrap.get('status') == 'estimated':
        lines.append(f'- Estimate **{_fmt(bootstrap["rate_ratio"])}**; participant-bootstrap 95% interval **[{_fmt(bootstrap["ci95_low"])}, {_fmt(bootstrap["ci95_high"])}]** ({bootstrap["bootstrap_draws"]} resamples).')
    else:
        lines.append(f'- Not estimated: {bootstrap.get("reason", "unspecified")}.')
    lines += [
        '- The bootstrap quantifies sample variation under resampling participants;',
        '  it does not repair non-random recruitment or unmatched dating pools.', '',
        '## Rank-based correlations', '',
        '| Variable X | Variable Y | N | Spearman rho | Exploratory p-value |',
        '|---|---|---:|---:|---:|',
    ]
    for r in correlations:
        p = 'Not estimated' if r['p_value'] is None else f'{r["p_value"]:.3g}'
        lines.append(f'| {r["variable_x"]} | {r["variable_y"]} | {r["n"]} | {_fmt(r["rho"])} | {p} |')
    if gender_correlations is not None:
        lines += ['', '### Correlations within recorded gender', '',
                  '| Gender | Variable X | Variable Y | N | Spearman rho | Exploratory p-value |',
                  '|---|---|---|---:|---:|---:|']
        for r in gender_correlations:
            p = 'Not estimated' if r['p_value'] is None else f'{r["p_value"]:.3g}'
            lines.append(f'| {r["gender"]} | {r["variable_x"]} | {r["variable_y"]} | {r["n"]} | {_fmt(r["rho"])} | {p} |')
        lines += ['', 'These are within-group associations between recorded-day rates.',
                  'A smaller group does not automatically imply a nonsignificant result.',
                  'P-values use the asymptotic Spearman approximation and are unadjusted for',
                  'multiple comparisons; interpret them cautiously, especially in smaller groups.',
                  'Different coefficients or significance levels do not establish a between-group difference.',
                  'All rates share a recorded-day denominator. Stratification does not remove',
                  'that dependence, self-selection, other confounding or reverse causation.', '']
    lines += ['', '## Exploratory count regression', '',
              'See `models.csv` and `model_diagnostics.json` for estimated NB coefficients,',
              'incidence-rate ratios, convergence and diagnostics. Do not interpret',
              'coefficients as causal effects.', '']
    for m in models:
        status = m['status']
        n = m.get('n', 'n/a')
        lines.append(f'- **{m["name"]}**: {status}; observations={n}.')
    lines += [
        '', '## Important limitations', '',
        '1. These are historical, self-selected Tinder exports with imbalanced gender groups.',
        '2. Incoming likes, initiator of each match, impressions and match timing are unknown.',
        '3. App opens are not measured minutes of use. Time spent cannot be tested.',
        '4. Recorded days are app-open log dates, not independently verified account tenure.',
        '5. Users volunteered exports, and gender groups have potentially different partner pools.',
        '6. Same-user totals have different observation windows and may include extreme outliers.',
        '7. Correlation with app activity is vulnerable to reverse causation (matches lead to opens).',
        '8. Gini of match counts measures outcome concentration, not desirability or hypergamy.',
        '9. No relationship outcomes are measured; this study cannot test relationship quality.',
        '', '## Figures', '',
        '- `figures/01_like_match_distributions`: skewed count distributions.',
        '- `figures/02_likes_vs_matches`: cross-user counts by gender.',
        '- `figures/03_match_rates_by_gender`: recorded-day rates by gender.',
        '- `figures/04_app_opens_vs_matches`: app-open frequency versus matches.',
        '- `figures/05_lorenz_match_counts`: match-count inequality.',
        '- `figures/06_coefficients_<model>`: converged model rate ratios and 95% Wald intervals.',
        '- `figures/07_model_match_rate_curves`: Models 2/3 expected matches per recorded day,',
        '  with pointwise 95% mean confidence bands, not individual prediction intervals.',
        '  Likes/day is held at the fitted sample pooled median; curves stay within each gender’s observed opening range.',
        '- Model figures are omitted for skipped, failed or unstable fits. Plotted values are exported as CSVs.', '',
        '## Reproducibility', '',
        '- Code: `python -m scripts.run_analysis` in this repository.',
        f'- Random seed: {manifest.get("seed", "not recorded")}; requested bootstrap draws: {manifest.get("bootstrap_draws_requested", "not recorded")}.',
        '- Input checks and cleaning information: `audit.json`.',
        '- The original source CSV is deliberately not copied into result folders.', '',
    ]
    (out / 'FINDINGS.md').write_text('\n'.join(lines), encoding='utf-8')
