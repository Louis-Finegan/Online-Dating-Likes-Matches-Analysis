#!/usr/bin/env python3
"""Download and validate the project's sole publicly shared Tinder dataset.

Usage (from any directory):
    python scripts/download_data.py
    python scripts/download_data.py --force
    python scripts/download_data.py --output data/Tinder_Data_v3_Clean_Edition.csv
"""

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from urllib import error, request

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dating_research.dataset import FILENAME, URL, DEFAULT_INPUT
from dating_research.source import REQUIRED

REQUIRED_COLUMNS = set(REQUIRED)
MAX_BYTES = 20 * 1024 * 1024


def validate_csv(path: Path) -> int:
    """Check file schema and return count of data rows (without parsing identifiers)."""
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV is missing required columns: {sorted(missing)}")
        row_count = sum(1 for row in reader if any(v for v in row.values()))
    if row_count == 0:
        raise ValueError("Downloaded CSV has no participant records")
    return row_count


def download_data(output: Path, *, force: bool = False) -> dict:
    """Download atomically, validate columns, and record reproducibility metadata."""
    output = Path(output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    if output.exists() and not force:
        rows = validate_csv(output)
        return {"status": "already_exists", "file": str(output), "rows": rows}

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=output.parent, prefix=".tinder-download-", suffix=".csv", delete=False
        ) as target:
            temp_path = Path(target.name)
            req = request.Request(URL, headers={"User-Agent": "LikesMatchesResearch/1.0"})
            with request.urlopen(req, timeout=30) as source:
                length = 0
                while True:
                    chunk = source.read(1024 * 128)
                    if not chunk:
                        break
                    length += len(chunk)
                    if length > MAX_BYTES:
                        raise ValueError("Download unexpectedly exceeds 20 MB")
                    target.write(chunk)

        rows = validate_csv(temp_path)
        sha256 = hashlib.sha256(temp_path.read_bytes()).hexdigest()
        temp_path.replace(output)
        temp_path = None
        metadata = {
            "status": "downloaded",
            "file": str(output),
            "source": URL,
            "rows": rows,
            "bytes": output.stat().st_size,
            "sha256": sha256,
            "downloaded_utc": datetime.now(timezone.utc).isoformat(),
            "notes": "Self-selected Tinder exports; not population-representative.",
        }
        manifest = output.with_suffix(".download.json")
        manifest.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        return metadata
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Download the free Tinder likes/matches CSV")
    parser.add_argument("--output", type=Path, default=DEFAULT_INPUT,
                        help="Destination CSV (default: project data directory)")
    parser.add_argument("--force", action="store_true", help="Replace an existing CSV after validation")
    args = parser.parse_args()
    try:
        result = download_data(args.output, force=args.force)
    except (OSError, ValueError, error.URLError) as exc:
        print(f"Download failed: {exc}", file=sys.stderr)
        return 1

    print(f"{result['status']}: {result['file']} ({result['rows']:,} data rows)")
    if result["status"] == "downloaded":
        print("Verified columns and recorded SHA-256 checksum in adjacent .download.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
