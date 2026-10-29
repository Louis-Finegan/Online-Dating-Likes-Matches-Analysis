#!/usr/bin/env python3
"""One-command pipeline: download the public CSV and run the research analysis."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
from urllib.error import URLError
from scripts.download_data import download_data, ROOT, FILENAME
from scripts.run_analysis import main as analyse_main


def main(argv=None):
    parser = argparse.ArgumentParser(description='Download and analyse public Tinder likes/matches data')
    parser.add_argument('--data', type=Path, default=ROOT / 'data' / FILENAME,
                        help='Local data path; download only if missing')
    parser.add_argument('--output', type=Path, default=ROOT / 'results' / 'tinder')
    parser.add_argument('--force-download', action='store_true')
    parser.add_argument('--bootstrap', type=int, default=2000)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args(argv)
    try:
        result = download_data(args.data, force=args.force_download)
    except (OSError, URLError, ValueError) as exc:
        print(f'Dataset download failed: {exc}', file=sys.stderr)
        print('If you downloaded the CSV manually, pass its path using --data.', file=sys.stderr)
        return 1
    print(f'Dataset: {result["status"]}, {result["rows"]:,} source rows.')
    return analyse_main(['--input', str(args.data), '--output', str(args.output),
                         '--bootstrap', str(args.bootstrap), '--seed', str(args.seed)])


if __name__ == '__main__':
    raise SystemExit(main())
