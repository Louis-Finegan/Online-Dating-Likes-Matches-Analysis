from pathlib import Path
import pandas as pd
import numpy as np
import pytest
from dating_research.source import load_tinder


def sample_data():
    return pd.DataFrame({
        'gender': ['M', 'F', 'M', 'F', None],
        'swipe_likes': [5, 0, 10, 10, 8],
        'no_of_matches': [8, 3, 0, -1, 2],
        'sum_app_opens': [10, 0, 15, 12, 4],
        'no_of_days': [5, 2, 5, 4, 3],
        'birthDate': ['not read'] * 5,
        'cityName': ['not read'] * 5,
    })


def test_load_validates_and_avoids_sensitive_fields(tmp_path):
    path = tmp_path / 'source.csv'
    sample_data().to_csv(path, index=False)
    df, audit = load_tinder(path)
    assert len(df) == 3
    assert audit['dropped_invalid_or_unrepresented_gender'] == 2
    assert 'cityName' not in df.columns
    assert 'birthDate' not in df.columns
    assert set(df['gender']) == {'Male', 'Female'}
    assert df.loc[0, 'matches_per_100_likes_sent'] == 160
    assert np.isnan(df.loc[1, 'matches_per_100_likes_sent'])
    assert audit['matches_greater_than_likes_sent_users'] == 2


def test_missing_required_columns(tmp_path):
    path = tmp_path / 'missing.csv'
    pd.DataFrame({'gender': ['M'], 'swipe_likes': [1]}).to_csv(path,index=False)
    with pytest.raises(ValueError, match='missing required columns'):
        load_tinder(path)


def test_missing_source(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_tinder(tmp_path / 'missing.csv')


def test_fractional_counts_dropped(tmp_path):
    path = tmp_path / 'invalid.csv'
    pd.DataFrame({'gender':['M','F'], 'swipe_likes':[1.5,3],
                  'no_of_matches':[1,1], 'sum_app_opens':[2,4],
                  'no_of_days':[1,2]}).to_csv(path,index=False)
    df, audit = load_tinder(path)
    assert len(df) == 1
    assert audit['dropped_invalid_or_unrepresented_gender'] == 1
