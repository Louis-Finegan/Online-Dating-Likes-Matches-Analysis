"""Descriptive and uncertainty estimates; participant is the sampling unit."""
from __future__ import annotations

import math
import numpy as np
import pandas as pd
from scipy.stats import spearmanr


def gini(values) -> float:
    """Gini for nonnegative observed counts; zero for an all-zero sample."""
    x = np.asarray(values, dtype=float)
    if not len(x) or not np.isfinite(x).all() or (x < 0).any():
        raise ValueError('gini requires nonempty finite nonnegative counts')
    total = x.sum()
    if total == 0:
        return 0.0
    x = np.sort(x)
    n = len(x)
    return float(2 * np.dot(np.arange(1, n + 1), x) / (n * total) - (n + 1) / n)


def top_share(values, proportion: float = 0.10) -> float:
    x = np.asarray(values, dtype=float)
    if not len(x) or not np.isfinite(x).all() or (x < 0).any():
        raise ValueError('top_share requires valid nonnegative counts')
    if not 0 < proportion <= 1:
        raise ValueError('proportion must be between 0 and 1')
    if x.sum() == 0:
        return 0.0
    count = max(1, math.ceil(len(x) * proportion))
    return float(np.sort(x)[-count:].sum() / x.sum())


def group_summary(df: pd.DataFrame) -> pd.DataFrame:
    result = []
    for group_name, sub in df.groupby('gender', observed=True):
        result.append({
            'gender': group_name,
            'users': int(len(sub)),
            'likes_sent_total': int(sub['likes_sent'].sum()),
            'matches_total': int(sub['matches'].sum()),
            'recorded_days_total': int(sub['recorded_days'].sum()),
            'likes_sent_median': float(sub['likes_sent'].median()),
            'matches_median': float(sub['matches'].median()),
            'matches_per_day_median': float(sub['matches_per_recorded_day'].median()),
            'likes_per_day_median': float(sub['likes_per_recorded_day'].median()),
            'opens_per_day_median': float(sub['opens_per_recorded_day'].median()),
            'pooled_matches_per_recorded_day': float(sub['matches'].sum() / sub['recorded_days'].sum()),
            'pooled_likes_per_recorded_day': float(sub['likes_sent'].sum() / sub['recorded_days'].sum()),
            'share_likes_sent_exceed_matches': float(sub['likes_exceed_matches'].mean()),
            'median_matches_per_100_likes_sent': float(sub['matches_per_100_likes_sent'].median()),
            'match_count_gini': gini(sub['matches'].to_numpy()),
            'top_10pct_share_of_matches': top_share(sub['matches'].to_numpy()),
            'zero_match_share': float((sub['matches'] == 0).mean()),
        })
    return pd.DataFrame(result).sort_values('gender').reset_index(drop=True)


def overall_summary(df: pd.DataFrame) -> dict:
    return {
        'participants': int(len(df)),
        'likes_sent_total': int(df['likes_sent'].sum()),
        'matches_total': int(df['matches'].sum()),
        'share_likes_sent_exceed_matches': float(df['likes_exceed_matches'].mean()),
        'matches_median': float(df['matches'].median()),
        'likes_sent_median': float(df['likes_sent'].median()),
        'gini_matches': gini(df['matches'].to_numpy()),
        'top_10pct_match_share': top_share(df['matches'].to_numpy()),
    }


def bootstrap_rate_ratio(df: pd.DataFrame, numerator='Female', denominator='Male',
                         draws: int = 2000, seed: int = 42) -> dict:
    """95% percentile CI for a pooled match/day rate ratio, resampling people.

    This is descriptive uncertainty for the volunteered sample, not a valid
    population-representative interval absent a sampling design.
    """
    if draws < 100:
        raise ValueError('draws must be at least 100')
    arrays = []
    for group in (numerator, denominator):
        sub = df.loc[df['gender'] == group, ['matches', 'recorded_days']].to_numpy(float)
        if len(sub) < 5:
            return {'status': 'not_estimated', 'reason': 'need at least five users in each group'}
        arrays.append(sub)
    (a, b) = arrays
    rate_b = b[:, 0].sum() / b[:, 1].sum()
    if rate_b <= 0:
        return {'status': 'not_estimated', 'reason': 'zero denominator-group rate'}
    estimate = float((a[:, 0].sum() / a[:, 1].sum()) / rate_b)
    rng = np.random.default_rng(seed)
    samples = np.empty(draws, float)
    for j in range(draws):
        xa = a[rng.integers(len(a), size=len(a))]
        xb = b[rng.integers(len(b), size=len(b))]
        denominator_rate = xb[:, 0].sum() / xb[:, 1].sum()
        samples[j] = (xa[:, 0].sum() / xa[:, 1].sum()) / denominator_rate if denominator_rate > 0 else np.nan
    samples = samples[np.isfinite(samples)]
    if len(samples) < draws * 0.95:
        return {'status': 'not_estimated', 'reason': 'unstable bootstrap denominator'}
    low, high = np.quantile(samples, [0.025, 0.975])
    return {'status': 'estimated', 'comparison': f'{numerator}/{denominator}',
            'rate_ratio': estimate, 'ci95_low': float(low), 'ci95_high': float(high),
            'bootstrap_draws': int(len(samples)), 'seed': seed}


def spearman_associations(df: pd.DataFrame) -> list[dict]:
    results = []
    pairs = [
        ('likes_per_recorded_day', 'matches_per_recorded_day'),
        ('opens_per_recorded_day', 'matches_per_recorded_day'),
        ('likes_per_recorded_day', 'opens_per_recorded_day'),
    ]
    for a, b in pairs:
        x = df[[a, b]].replace([np.inf, -np.inf], np.nan).dropna()
        if len(x) < 5 or x[a].nunique() < 2 or x[b].nunique() < 2:
            results.append({'variable_x': a, 'variable_y': b, 'n': len(x), 'rho': None, 'p_value': None})
            continue
        out = spearmanr(x[a], x[b])
        results.append({'variable_x': a, 'variable_y': b, 'n': len(x),
                        'rho': float(out.statistic), 'p_value': float(out.pvalue)})
    return results
