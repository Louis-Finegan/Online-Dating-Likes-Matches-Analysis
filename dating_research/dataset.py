"""The sole empirical data source and shared repository paths."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILENAME = "Tinder_Data_v3_Clean_Edition.csv"
SOURCE_URL = "https://github.com/Ashley-Xu/AIPIFinalDataset"
URL = (
    "https://raw.githubusercontent.com/Ashley-Xu/"
    "AIPIFinalDataset/main/Tinder_Data_v3_Clean_Edition.csv"
)
DEFAULT_INPUT = ROOT / "data" / FILENAME
DEFAULT_OUTPUT = ROOT / "results" / "tinder"
