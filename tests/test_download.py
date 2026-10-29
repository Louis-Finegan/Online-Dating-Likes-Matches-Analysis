"""Network-free tests for the download and validation workflow."""
import io
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.download_data import URL, download_data, validate_csv

CSV_DATA = (
    b"gender,swipe_likes,no_of_matches,no_of_days,sum_app_opens\n"
    b"M,10,2,5,12\nF,8,4,5,20\n"
)


def test_download_and_manifest(tmp_path):
    target = tmp_path / "tinder.csv"
    with patch("scripts.download_data.request.urlopen", return_value=io.BytesIO(CSV_DATA)) as mocked:
        result = download_data(target)
    assert mocked.call_count == 1
    assert result["status"] == "downloaded"
    assert result["rows"] == 2
    assert result["source"] == URL
    assert result["sha256"]
    assert target.read_bytes() == CSV_DATA
    assert json.loads(target.with_suffix(".download.json").read_text())["rows"] == 2


def test_existing_download_not_overwritten(tmp_path):
    target = tmp_path / "tinder.csv"
    target.write_bytes(CSV_DATA)
    with patch("scripts.download_data.request.urlopen") as mocked:
        result = download_data(target)
    assert result["status"] == "already_exists"
    mocked.assert_not_called()


def test_force_replaces_existing_download(tmp_path):
    target = tmp_path / "tinder.csv"
    target.write_bytes(CSV_DATA)
    more_rows = CSV_DATA + b"M,6,0,4,4\n"
    with patch("scripts.download_data.request.urlopen", return_value=io.BytesIO(more_rows)):
        result = download_data(target, force=True)
    assert result["rows"] == 3
    assert validate_csv(target) == 3


def test_invalid_download_preserves_existing_file(tmp_path):
    target = tmp_path / "tinder.csv"
    target.write_bytes(CSV_DATA)
    with patch("scripts.download_data.request.urlopen", return_value=io.BytesIO(b"<html>Error</html>")):
        with pytest.raises(ValueError, match="missing required columns"):
            download_data(target, force=True)
    assert target.read_bytes() == CSV_DATA
    assert list(tmp_path.glob(".tinder-download-*.csv")) == []


def test_invalid_existing_file_warns(tmp_path):
    target = tmp_path / "tinder.csv"
    target.write_text("wrong,header\n1,2\n")
    with pytest.raises(ValueError, match="missing required columns"):
        download_data(target)
