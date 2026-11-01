# Data dictionary

Only these source variables are read by the project:

| Original CSV | Research field | Interpretation |
|---|---|---|
| `gender` | `gender` | M/F mapped to Male/Female; unknown codes excluded from those comparisons |
| `swipe_likes` | `likes_sent` | Total positive swipes / likes **sent** |
| `no_of_matches` | `matches` | Total matches (irrespective of initiating side) |
| `no_of_days` | `recorded_days` | Number of dates in the app-open log, **not independently verified tenure** |
| `sum_app_opens` | `app_opens` | Count of app-open events, **not minutes** |
| `user_age` (optional) | `reported_age` | Upstream age at account creation; values outside 18–100 set to missing; not a model covariate |
| `interestedIn` (optional) | `interested_in` | M/F mapped to Male/Female; other codes, including `M and F`, currently become missing; not used in summaries or models |

Derived columns:

- `likes_per_recorded_day = likes_sent / recorded_days`
- `matches_per_recorded_day = matches / recorded_days`
- `opens_per_recorded_day = app_opens / recorded_days`
- `matches_per_100_likes_sent = 100 * matches / likes_sent` for positive sent likes;
  **descriptive ratio, NOT conversion probability**.
- `likes_exceed_matches = likes_sent > matches`
- `log_likes_rate = log1p(likes_per_recorded_day)`
- `log_opens_rate = log1p(opens_per_recorded_day)`

Negative or noninteger counts, zero/nonpositive recorded days, missing essential
variables and unrepresented gender codes are excluded with an audit count.
Optional age or partner preference can be missing; they are not used for causal
adjustment or subgroup analysis. No sexual orientation is inferred. The source
contains 57 `M and F` entries; the current loader does not analyse this category.
No user IDs, cities, dates of birth, occupations, messages or
individual participant rows are written into the results directory.

`recorded_days` counts date entries in the app-opening log, not calendar duration
or necessarily days with positive opens. See [the upstream derivation](DATA_PROVENANCE.md).
The existing summary CSV's `*_per_day_median` columns also use recorded days.
