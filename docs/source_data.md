# Milestone 1 source-data handoff

Owner: Cameron (Econ/Stats). NOAA implementation: Mason. Boundary implementation:
CS lead. Status: documentation prepared; retrieval and ingestion QA pending.

## Inputs and scope

| Input | Required at this milestone | Selection and destination |
|---|---|---|
| NOAA Storm Events details | Yes | Annual 2015–2024 detail files; `data/raw/noaa_storm_events/` |
| Census TIGER/Line counties | Yes | `tl_2024_us_county.zip`; `data/raw/census_tiger/` |
| NOAA location files | Only if the geography audit needs them | Join to details by event ID; retain multiple locations per event |
| Weather, terrain, vulnerability, live services | No | Registered for later milestones; provider and coverage decisions remain pending |

Use the URLs and filename patterns in [the manifest](../data/data_manifest.yaml).
Keep national source files intact. Select North Carolina during transformation,
using state FIPS `37`, and retain exactly Flood, Flash Flood, and Debris Flow.
Heavy Rain and Coastal Flood are outside the project's locked label scope.

The [NOAA export dictionary](https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/Storm-Data-Export-Format.pdf)
distinguishes county, forecast-zone, and marine codes. A zone identifier is not
a county FIPS. Preserve event IDs and original time fields; interpret the source
timezone before converting to UTC. Damage values are estimates with suffixes;
missing damage is not automatically zero. These fields support descriptive QA,
not weather features.

Use the [2024 Census boundary vintage](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.2024.html)
consistently across historical years. Verify 100 unique NC county GEOIDs after
filtering. Construct county-coded NOAA keys from two-character state and
three-character county strings, then check membership in the boundary table.
This is a project validation requirement, not proof that all source records join.

## Retrieval evidence contract

For each required dataset, the downloader must replace the manifest's `TBD`
retrieval fields only after a successful download:

1. `access_date`: actual retrieval timestamp in UTC, as a quoted ISO-8601 string.
2. `resolved_files`: exact upstream filenames, including NOAA creation suffixes.
3. `checksum`: mapping from every resolved filename to its lowercase SHA-256
   digest, calculated over the original downloaded bytes.

Store files beneath the registered repository-relative raw path. For NOAA,
record one selected details file per year, rather than mixing revisions of the
same year. Resolve filenames against the registered source URL. A missing year
or a filename without a checksum makes the retrieval incomplete. Keep any
refresh explicit: do not silently replace an existing file with different bytes.
On reuse, verify the recorded digest and retain the original retrieval time.

Documentation access does not count as data retrieval. A future source timestamp,
a guessed checksum, or a digest of an extracted CSV in place of its downloaded
gzip is not valid evidence. Raw data remain untracked. Preserve the source
attribution and license entries in the manifest when recording a retrieval.

## Review evidence requested from ingestion owners

| Evidence | Owner | Acceptance check |
|---|---|---|
| Retrieval inventory | Mason / CS lead | Ten details years and one county archive, exact filenames and verified digests |
| NOAA QA table | Mason | Raw, state-filtered, hazard-filtered, duplicate, invalid-time, unresolved-geography, and retained counts with documented denominators |
| Identity checks | Mason | Duplicate event IDs surfaced; identical versus conflicting duplicates distinguished |
| Time checks | Mason | UTC-aware parsed times; missing or reversed intervals counted and handled explicitly |
| Geography checks | CS lead / Mason | 100 unique boundary keys; unmatched and zone-coded events counted without invented county assignments |
| Reproduction | Ingestion owners | One command in a fresh Codespace; sample mode works offline |
| Independent review | Cameron | Reconcile counts, inspect exclusions, and link test output and QA artifacts |

The existing ingestion scripts and tests are placeholders. This document does
not certify that they pass. The full Milestone 1 acceptance criteria remain
open until implementation and evidence are available.

## Interpretation and EDA handoff

The tracked [sample files](../data/sample/README.md) are hand-authored fixtures.
They exercise edge cases; their frequencies, damage totals, and positive rate
are not estimates for North Carolina. They do not establish full temporal or
geographic coverage. Missing reports do not establish absence of flooding.

Before the Milestone 2 gate, resolve the beginning-versus-overlap label conflict
listed in [the data card](data_card.md), audit unresolved geography, and select
the weather provider. Cameron's next deliverables are counts by year, month,
county and type, missingness and quality summaries, and interpretation review.
Use retrieved data for empirical conclusions and keep sample smoke-test
results visibly separate. No EDA approval or model result is implied here.
