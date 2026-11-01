import numpy as np
import pandas as pd
import pytest
from dating_research.statistics import (gini, top_share, group_summary,
        bootstrap_rate_ratio, spearman_associations, spearman_by_gender)


def test_gini_equal_and_concentrated():
    assert gini([1,1,1]) == pytest.approx(0)
    assert gini([0,0,10]) == pytest.approx(2/3)
    assert gini([0,0,0]) == pytest.approx(0)
    assert top_share([0,0,0,10], .25) == 1
    with pytest.raises(ValueError): gini([-1,3])


def test_summary_and_bootstrap():
    rng = np.random.default_rng(42)
    n = 120
    df = pd.DataFrame({'gender':['Male']*60+['Female']*60,
        'likes_sent':rng.integers(5,100,n), 'matches':rng.integers(0,30,n),
        'recorded_days':rng.integers(2,50,n),
        'app_opens':rng.integers(10,150,n)})
    df['likes_exceed_matches'] = df['likes_sent'] > df['matches']
    df['likes_per_recorded_day'] = df['likes_sent']/df['recorded_days']
    df['matches_per_recorded_day'] = df['matches']/df['recorded_days']
    df['opens_per_recorded_day'] = df['app_opens']/df['recorded_days']
    df['matches_per_100_likes_sent'] = 100*df['matches']/df['likes_sent']
    groups = group_summary(df)
    assert groups['users'].sum() == n
    assert groups['match_count_gini'].between(0,1).all()
    stats = bootstrap_rate_ratio(df, draws=200, seed=123)
    assert stats['status'] == 'estimated'
    assert stats['ci95_low'] < stats['ci95_high']
    assert len(spearman_associations(df)) == 3


def test_gender_correlations_separate_opposite_rankings():
    df = pd.DataFrame({
        'gender': ['Female'] * 6 + ['Male'] * 6,
        'likes_per_recorded_day': list(range(6)) * 2,
        'matches_per_recorded_day': list(range(6)) + list(reversed(range(6))),
        'opens_per_recorded_day': list(range(6)) * 2,
    })
    results = spearman_by_gender(df)
    assert len(results) == 6
    for row in results:
        assert row['n'] == 6
        expected = -1 if row['gender'] == 'Male' and row['variable_y'] == 'matches_per_recorded_day' else 1
        assert row['rho'] == pytest.approx(expected)


def test_gender_correlations_handle_small_constant_and_missing_pairs():
    df = pd.DataFrame({
        'gender': ['Female'] * 6 + ['Male'] * 4,
        'likes_per_recorded_day': [1] * 10,
        'matches_per_recorded_day': list(range(10)),
        'opens_per_recorded_day': [0, 1, 2, 3, 4, np.nan, 6, 7, 8, 9],
    })
    for row in spearman_by_gender(df):
        if row['gender'] == 'Female' and row['variable_x'] == 'opens_per_recorded_day':
            assert row['n'] == 5
            assert row['rho'] == pytest.approx(1)
        else:
            assert row['rho'] is None
            assert row['p_value'] is None
