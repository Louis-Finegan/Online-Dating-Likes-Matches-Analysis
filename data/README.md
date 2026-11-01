# Data directory

Run `python -m scripts.download_data` from the project root to obtain the free,
publicly shared Tinder CSV. The original CSV is not redistributed here. The CSV
contains fields this project never reads (such as dates of birth and cities).
Treat it as private, do not upload it to public repositories, and review the
source author's license and ethics notes before any public publication.

The sole input is `Tinder_Data_v3_Clean_Edition.csv`; the adjacent
`Tinder_Data_v3_Clean_Edition.download.json` records its download URL, timestamp
and SHA-256. Existing downloads are preserved unless `--force` is specified.
See [verified provenance and sample counts](../docs/DATA_PROVENANCE.md).
Analysis outputs belong in `results/`, not this directory.
