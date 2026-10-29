"""Figures for an exploratory research report; no data-dependent color coding."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def _save(directory: Path, name: str):
    plt.tight_layout()
    plt.savefig(directory / f'{name}.png', dpi=180, bbox_inches='tight')
    plt.savefig(directory / f'{name}.pdf', bbox_inches='tight')
    plt.close()


def make_figures(df, output: str | Path) -> list[str]:
    directory = Path(output)
    directory.mkdir(parents=True, exist_ok=True)
    figures = []

    # Counts are heavily right-skewed; plot log1p transformed values, not fake log-zero.
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(np.log1p(df['likes_sent']), bins=40, alpha=0.6, label='Likes sent')
    ax.hist(np.log1p(df['matches']), bins=40, alpha=0.6, label='Matches')
    ax.set(xlabel='log(1 + participant count)', ylabel='Participants',
           title='Distribution of likes sent and matches')
    ax.legend()
    _save(directory, '01_like_match_distributions');figures.append('01_like_match_distributions')

    fig, ax = plt.subplots(figsize=(8, 5))
    for label, group in df.groupby('gender', observed=True):
        ax.scatter(np.log1p(group['likes_sent']), np.log1p(group['matches']),
                   label=str(label), s=18, alpha=0.45)
    ax.set(xlabel='log(1 + likes sent)', ylabel='log(1 + total matches)',
           title='Likes versus matches, by recorded gender')
    ax.legend()
    _save(directory, '02_likes_vs_matches');figures.append('02_likes_vs_matches')

    fig, ax = plt.subplots(figsize=(8, 5))
    groups = [(str(k), g) for k, g in df.groupby('gender', observed=True)]
    values = [np.log1p(g['matches_per_recorded_day']) for _, g in groups]
    ax.boxplot(values, tick_labels=[k for k, _ in groups], showfliers=False)
    ax.set(xlabel='Gender', ylabel='log(1 + matches / recorded day)',
           title='Observed match rates by gender (not tenure-adjusted)')
    _save(directory, '03_match_rates_by_gender');figures.append('03_match_rates_by_gender')

    fig, ax = plt.subplots(figsize=(8, 5))
    for label, group in df.groupby('gender', observed=True):
        ax.scatter(np.log1p(group['opens_per_recorded_day']),
                   np.log1p(group['matches_per_recorded_day']),
                   s=18, alpha=0.45, label=str(label))
    ax.set(xlabel='log(1 + app opens / recorded day)',
           ylabel='log(1 + matches / recorded day)',
           title='App opening activity and matches (not screen time)')
    ax.legend()
    _save(directory, '04_app_opens_vs_matches');figures.append('04_app_opens_vs_matches')

    fig, ax = plt.subplots(figsize=(8, 5))
    for label, group in [('All participants', df)] + groups:
        x = np.sort(group['matches'].to_numpy(float))
        cum = np.concatenate(([0.0], np.cumsum(x)))
        cum = cum / cum[-1] if cum[-1] > 0 else np.zeros_like(cum)
        ax.plot(np.linspace(0, 1, len(cum)), cum, label=label)
    ax.plot([0, 1], [0, 1], linestyle='--', label='Equal distribution')
    ax.set(xlabel='Cumulative proportion of participants (fewest matches first)',
           ylabel='Cumulative proportion of matches',
           title='Lorenz curves: inequality in observed match counts')
    ax.legend()
    _save(directory, '05_lorenz_match_counts');figures.append('05_lorenz_match_counts')
    return figures
