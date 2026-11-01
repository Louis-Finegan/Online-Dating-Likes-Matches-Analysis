#!/usr/bin/env python3
"""Run a reproducible exploratory study from the cleaned Tinder CSV."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dating_research.source import load_tinder
from dating_research.dataset import DEFAULT_INPUT, DEFAULT_OUTPUT, SOURCE_URL, URL
from dating_research.statistics import (group_summary, overall_summary,
                                         bootstrap_rate_ratio, spearman_associations, spearman_by_gender)
from dating_research.models import fit_models
from dating_research.figures import make_figures
from dating_research.report import write_report


def save_json(path: Path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def main(argv=None):
    parser = argparse.ArgumentParser(description='Analyse observed Tinder likes, matches and app opens')
    parser.add_argument('--input', type=Path, default=DEFAULT_INPUT)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--bootstrap', type=int, default=2000)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args(argv)
    data, audit = load_tinder(args.input)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    summary = group_summary(data)
    total = overall_summary(data)
    uncertainty = bootstrap_rate_ratio(data, draws=args.bootstrap, seed=args.seed)
    correlation = spearman_associations(data)
    gender_correlations = spearman_by_gender(data)
    coefficients, diagnostics = fit_models(data)
    summary.to_csv(output / 'gender_summary.csv', index=False)
    coefficients.to_csv(output / 'models.csv', index=False)
    save_json(output / 'audit.json', audit)
    save_json(output / 'overall.json', total)
    save_json(output / 'bootstrap_ci.json', uncertainty)
    save_json(output / 'correlations.json', correlation)
    save_json(output / 'correlations_by_gender.json', gender_correlations)
    save_json(output / 'model_diagnostics.json', diagnostics)
    save_json(output / 'dataset_manifest.json', {
        'source': 'Ashley Xu / SwipeStats publicly shared Tinder dataset',
        'source_url': SOURCE_URL,
        'download_url': URL,
        'sha256': hashlib.sha256(args.input.read_bytes()).hexdigest(),
        'filename': args.input.name,
        'record_count': audit['usable_rows'],
        'original_rows': audit['original_rows'],
        'bootstrap_draws_requested': args.bootstrap,
        'seed': args.seed,
    })
    figs = make_figures(data, output / 'figures')
    write_report(output, audit, total, summary, uncertainty, correlation, diagnostics,
                 gender_correlations=gender_correlations)
    print(f'Analysed {len(data):,} records. Figures: {len(figs)}.')
    print(summary[['gender', 'users', 'likes_sent_median', 'matches_median',
                   'pooled_matches_per_recorded_day']].to_string(index=False))
    print(f'Report: {output / "FINDINGS.md"}')
    print('NOTE: Matches / likes sent is not a probability. App opens are not minutes.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
