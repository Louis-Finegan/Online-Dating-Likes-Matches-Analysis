# Dataset provenance

## Sole source

- Host/author: [Ashley Xu, AIPIFinalDataset](https://github.com/Ashley-Xu/AIPIFinalDataset).
- File: [Tinder_Data_v3_Clean_Edition.csv](https://github.com/Ashley-Xu/AIPIFinalDataset/blob/main/Tinder_Data_v3_Clean_Edition.csv).
- Origin: volunteer-submitted Tinder exports via SwipeStats. The author's README
  states that website-owner permission was obtained and names the Community Data
  License Agreement – Sharing – Version 1.0. Consult the source's terms before
  redistribution; public availability is not a blanket permission for every use.

The repository analyses this CSV only. Local input flags support saved copies of
that file; there is no multi-source adapter or separate platform data pipeline.

## Verified snapshot

The file inspected on 1 November 2026 has:

| Measure | Count |
|---|---:|
| Participant rows before exclusions | 1,209 |
| M-coded users | 1,059 |
| F-coded users | 150 |
| Rows with zero recorded days | 226 |
| Rows retained by the current loader | 983 |

SHA-256:

```text
082b9fa20eaa1fbdc12b77135c484dabed3dfc4683df6ec444c8c4faa0852446
```

The source URL follows its `main` branch and can change. These counts describe
this checksum, not a guarantee about future downloads. The downloader records
the retrieved checksum, URL and UTC time in the adjacent `.download.json`.
Each analysis records the actual input checksum and run settings in
`dataset_manifest.json`; compare checksums before treating runs as equivalent.

## Meaning of recorded days

The upstream [extraction code](https://github.com/Ashley-Xu/AIPIFinalDataset/blob/main/json_to_csv.py)
sets `no_of_days = len(app_opens)`. After merging with match summaries, the
[cleaning code](https://github.com/Ashley-Xu/AIPIFinalDataset/blob/main/cleaning.py)
renames `no_of_days_x` to `no_of_days`. Thus this is the number of date entries
in the app-opening log. It is not elapsed calendar time and does not establish
that each entry has a positive number of opens. The original logs are not
available here for independent verification of coverage.

The source's `user_age` is calculated from birth date and account creation date,
not age at download. It is optional and not included in the current regressions.

## Preservation and privacy

Raw downloads stay in the ignored `data/` directory. Existing CSVs are reused
unless replacement is explicitly requested. The loader selects only required
counts, recorded gender and optional age/partner-interest fields. Raw profile
fields and participant tables are not copied into results. Scatter plots still
represent participant-level count/rate observations and should be reviewed
before publication.
