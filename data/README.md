# Data

Four layers, one direction of travel. Nothing flows backwards.

```text
data/raw/         Immutable downloaded source files.        Never edited. Never committed.
data/interim/     Cleaned, source-specific tables.          Reproducible. Never committed.
data/processed/   Model-ready county-window tables.         Reproducible. Never committed.
data/sample/      Tiny public fixtures for tests and CI.    Hand-authored. Always committed.
```

[`data_manifest.yaml`](data_manifest.yaml) is the source of truth for what a
dataset is, where it came from, and when it was retrieved. If a dataset is not
in the manifest, it may not be used.

## Rules

1. **Never edit a raw file by hand.** If a raw file is wrong, fix the
   transformation, not the input.
2. **Every interim and processed file must be recreatable by a script.** If you
   cannot regenerate it with `make download` and `make data`, it does not exist
   as far as the project is concerned.
3. **Large files stay out of Git.** `.gitignore` enforces this;
   `check-added-large-files` catches what slips through.
4. **Paths resolve from the repository root or from configuration.** Never a
   teammate's `Downloads` folder, never an absolute path.
5. **County FIPS are strings.** `037` and `021` lose meaning as integers.
6. **Timestamps are timezone-aware UTC internally.** Local time appears only at
   the display layer.
7. **Every processed table carries provenance** — creation timestamp, source
   versions, and the Git commit that produced it — in a sidecar JSON or in the
   Parquet metadata.

## Getting the data

```bash
make download   # NOAA Storm Events 2015-2024 + Census county boundaries
make data       # build data/processed/county_windows.parquet
```

Neither is implemented yet; see Milestones 1 and 3 in
[docs/build_guide.md](../docs/build_guide.md).

To work without any download:

```bash
STORMROUTE_DATA_MODE=sample make test
```

## Schemas

Canonical schemas for `events.parquet`, `county_windows.parquet`,
`predictions_2024.parquet`, and `demo_routes.geojson` live in
[docs/data_card.md](../docs/data_card.md).

A schema change requires, in one pull request labeled `area:data`: the updated
schema in the data card, updated validation tests, and notice to all three
teammates.

## What a negative label means

A negative `label_flood_event` means **no qualifying event was reported** in that
county-window. It does not mean the roads were safe, and it does not mean
nothing happened. Reporting is uneven across counties and across years. This
distinction is a correctness requirement, not a caveat — see
[docs/responsible_ai.md](../docs/responsible_ai.md).
