"""Produce Cameron's real NOAA count tables after verifying saved cleaned exports."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
import pandas as pd

from stormroute.config import REPO_ROOT, load_config
from stormroute.data.noaa import sha256_of
from stormroute.data.validation import NC_COUNTY_FIPS, validate_events

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main() -> None:
    config = load_config("data")
    root = REPO_ROOT / "data/interim"
    provenance_path = root / "events.provenance.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    input_hashes = {key.replace("\\", "/"): value for key, value in provenance["outputs"].items()}
    for filename in ("events.parquet", "events.csv"):
        path = root / filename
        key = path.relative_to(REPO_ROOT).as_posix()
        if sha256_of(path) != input_hashes[key]:
            raise ValueError(f"Saved export no longer matches provenance: {filename}")
    events = pd.read_parquet(root / "events.parquet")
    validate_events(events, config["label"]["hazard_event_types"])
    if events.isna().any().any() or len(events) != provenance["rows"]:
        raise ValueError("Unexpected missing fields or row count in saved events")
    csv = pd.read_csv(
        root / "events.csv",
        dtype={"event_id": str, "episode_id": str, "county_fips": str},
        float_precision="round_trip",
    )
    for column in ("begin_utc", "end_utc"):
        csv[column] = pd.to_datetime(csv[column], utc=True)
    pd.testing.assert_frame_equal(events, csv.astype(events.dtypes.to_dict()))
    years = range(config["period"]["start_year"], config["period"]["end_year"] + 1)
    groups = {
        "year": (events["begin_utc"].dt.year, list(years)),
        "month": (events["begin_utc"].dt.month, list(range(1, 13))),
        "county_fips": (events["county_fips"], sorted(NC_COUNTY_FIPS)),
        "event_type": (events["event_type"], config["label"]["hazard_event_types"]),
    }
    tables = {}
    output = root / "noaa_descriptive"
    output.mkdir(parents=True, exist_ok=True)
    annotated = events.copy()
    annotated["duration_hours"] = (
        events["end_utc"] - events["begin_utc"]
    ).dt.total_seconds() / 3600
    annotated["review_zero_duration"] = annotated["duration_hours"].eq(0)
    summaries = {}
    for column in ("duration_hours", "injuries", "deaths", "property_damage_usd"):
        values = annotated[column].astype(float)
        if not values.ge(0).all():
            raise ValueError(f"Missing or negative values need review: {column}")
        threshold = float(values.quantile(0.99))
        flag = f"review_upper_tail_{column}"
        annotated[flag] = values.ge(threshold) & values.gt(0)
        summaries[column] = {
            "rows": len(values),
            "missing": int(values.isna().sum()),
            "zero": int(values.eq(0).sum()),
            "positive": int(values.gt(0).sum()),
            "sum": float(values.sum()),
            "median": float(values.median()),
            "p95": float(values.quantile(0.95)),
            "p99": threshold,
            "max": float(values.max()),
            "upper_tail_review_count": int(annotated[flag].sum()),
        }
    flags = [c for c in annotated.columns if str(c).startswith("review_")]
    annotated["review_any"] = annotated[flags].any(axis=1)
    pd.testing.assert_frame_equal(annotated.loc[:, events.columns], events)
    annotated.to_parquet(output / "events_review.parquet", index=False)
    annotated.to_csv(output / "events_review.csv", index=False)
    annotated.loc[annotated["review_any"]].to_csv(output / "review_queue.csv", index=False)
    pd.testing.assert_frame_equal(pd.read_parquet(output / "events_review.parquet"), annotated)
    for name, (values, categories) in groups.items():
        counts = values.value_counts().reindex(categories, fill_value=0)
        if int(counts.sum()) != len(events):
            raise ValueError(f"Counts do not reconcile: {name}")
        table = counts.rename("event_count").rename_axis(name).reset_index()
        table["share_of_retained_events"] = table["event_count"] / len(events)
        table.to_csv(output / f"counts_by_{name}.csv", index=False)
        tables[name] = table.to_dict(orient="records")

    figure, axes = plt.subplots(2, 2, figsize=(13, 9))
    for axis, name in zip(axes.flat, groups, strict=True):
        table = pd.DataFrame(tables[name])
        if name == "county_fips":
            table = table.sort_values(["event_count", "county_fips"], ascending=[False, True]).head(
                10
            )
        axis.bar(table[name].astype(str), table["event_count"], color="#246b8e")
        axis.set_title("Top 10 counties (FIPS)" if name == "county_fips" else f"By {name}")
        axis.set_ylabel("Reported event records")
        axis.tick_params(axis="x", rotation=45)
    figure.suptitle(f"NC NOAA retained events, 2015-2024 (n={len(events):,}); onset in UTC")
    figure.tight_layout()
    figure_path = REPO_ROOT / "outputs/figures/noaa_real_event_counts.png"
    figure.savefig(figure_path, dpi=160)
    plt.close(figure)
    payload = {
        "source": "Saved real-release NOAA cleaned events; not sample data",
        "source_release": provenance["source_release"],
        "source_archive_sha256": provenance["source_archive_sha256"],
        "input_sha256": provenance["outputs"],
        "provenance_sha256": sha256_of(provenance_path),
        "script_sha256": sha256_of(Path(__file__)),
        "rows": len(events),
        "columns": len(events.columns),
        "missing_cells": int(events.isna().sum().sum()),
        "duplicate_event_ids": int(events["event_id"].duplicated().sum()),
        "csv_parquet_agree": True,
        "counties_with_reports": int(events["county_fips"].nunique()),
        "grouping": "UTC event onset; month pools all configured years",
        "limitations": [
            "Counts are event records, not unique storms, probabilities, or road risk",
            "Zero reports do not establish absence of flooding",
            "NOAA summer timestamp interpretation still awaits external verification",
            "Weather is not included; this is not a model-ready county-window table",
        ],
        "tables": tables,
        "duration_and_impact": summaries,
        "review_queue_rows": int(annotated["review_any"].sum()),
        "review_policy": (
            "Retain all records. Flag zero duration and positive values at or above each "
            "field's overall empirical 99th percentile (linear interpolation, ties included). "
            "Flags prioritize inspection; they do not establish errors. Impacts are outcomes, "
            "not prediction features. Timestamp source interpretation remains pending for all rows."
        ),
        "generated_files_sha256": {
            str(path.relative_to(REPO_ROOT).as_posix()): sha256_of(path)
            for path in [
                *sorted(output.glob("counts_by_*.csv")),
                output / "events_review.parquet",
                output / "events_review.csv",
                output / "review_queue.csv",
                figure_path,
            ]
        },
    }
    metrics = REPO_ROOT / "outputs/metrics/noaa_real_event_counts.json"
    metrics.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(
        f"Verified {len(events)} events; wrote counts, chart, annotated data, "
        f"and {int(annotated['review_any'].sum())} review candidates."
    )


if __name__ == "__main__":
    main()
