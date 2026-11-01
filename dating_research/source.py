"""Import only aggregate behavioural columns, never sensitive profile fields."""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

# The public source includes birth dates, cities, names/job details etc. We do NOT
# load or export those fields. Raw files remain local and gitignored.
REQUIRED = {
    'gender': 'gender',
    'swipe_likes': 'likes_sent',
    'no_of_matches': 'matches',
    'sum_app_opens': 'app_opens',
    'no_of_days': 'recorded_days',
}
OPTIONAL = {'user_age': 'reported_age', 'interestedIn': 'interested_in'}


def load_tinder(path: str | Path) -> tuple[pd.DataFrame, dict]:
    """Return validated participant records and a reproducible cleaning audit.

    recorded_days: number of dates in the app-open log, NOT calendar tenure.
    Source records are self-selected Tinder exports.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f'Missing data file: {path}. Run python -m scripts.download_data')
    columns = set(REQUIRED) | set(OPTIONAL)
    raw = pd.read_csv(path, usecols=lambda c: c in columns, low_memory=False)
    absent = sorted(set(REQUIRED) - set(raw))
    if absent:
        raise ValueError(f'CSV missing required columns: {absent}')
    if raw.empty:
        raise ValueError('The source CSV contains no participants')

    df = raw.rename(columns={**REQUIRED, **OPTIONAL}).copy()
    audit = {'original_rows': int(len(df)), 'source_file': path.name,
             'raw_columns_selected': sorted(raw.columns.tolist())}
    df['gender'] = (
        df['gender'].astype('string').str.strip().str.upper()
          .map({'M': 'Male', 'MALE': 'Male', 'F': 'Female', 'FEMALE': 'Female'})
    )
    for column in ['likes_sent', 'matches', 'app_opens', 'recorded_days']:
        df[column] = pd.to_numeric(df[column], errors='coerce')

    count_columns = ['likes_sent', 'matches', 'app_opens', 'recorded_days']
    valid = df['gender'].notna() & df[count_columns].notna().all(axis=1)
    valid &= (df[count_columns] >= 0).all(axis=1)
    valid &= (df['recorded_days'] > 0)
    valid &= np.logical_and.reduce([np.isclose(df[c], df[c].round()) for c in count_columns])
    audit['dropped_invalid_or_unrepresented_gender'] = int((~valid).sum())
    df = df.loc[valid].copy()
    if df.empty:
        raise ValueError('No valid rows after cleaning')

    if 'reported_age' in df:
        df['reported_age'] = pd.to_numeric(df['reported_age'], errors='coerce')
        df.loc[~df['reported_age'].between(18, 100), 'reported_age'] = np.nan
    if 'interested_in' in df:
        df['interested_in'] = (
            df['interested_in'].astype('string').str.strip().str.upper()
              .map({'F': 'Female', 'M': 'Male'})
        )

    # These ratios are descriptors. They are not causal effects or probabilities.
    df['likes_per_recorded_day'] = df['likes_sent'] / df['recorded_days']
    df['matches_per_recorded_day'] = df['matches'] / df['recorded_days']
    df['opens_per_recorded_day'] = df['app_opens'] / df['recorded_days']
    df['matches_per_100_likes_sent'] = np.where(
        df['likes_sent'] > 0, 100.0 * df['matches'] / df['likes_sent'], np.nan
    )
    df['likes_exceed_matches'] = df['likes_sent'] > df['matches']
    df['log_likes_rate'] = np.log1p(df['likes_per_recorded_day'])
    df['log_opens_rate'] = np.log1p(df['opens_per_recorded_day'])

    audit.update({
        'usable_rows': int(len(df)),
        'gender_counts': {str(k): int(v) for k, v in df['gender'].value_counts().items()},
        'zero_likes_users': int((df['likes_sent'] == 0).sum()),
        'zero_matches_users': int((df['matches'] == 0).sum()),
        'matches_greater_than_likes_sent_users': int((df['matches'] > df['likes_sent']).sum()),
        'age_observed': int(df['reported_age'].notna().sum()) if 'reported_age' in df else 0,
        'limitations': [
            'Volunteer-submitted Tinder exports are not representative; gender groups are imbalanced.',
            'Recorded days are dates with app-opening data, not independently verified tenure.',
            'App opens are not time spent in minutes.',
            'Matches include responses to incoming likes; matches/likes_sent is not a probability.',
            'No incoming likes, match-initiation direction, or profile-impression measures.',
        ],
    })
    return df.reset_index(drop=True), audit
