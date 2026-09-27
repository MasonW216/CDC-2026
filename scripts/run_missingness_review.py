"""Execute scoped notebook missingness or event-count reviews on verified inputs."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import nbformat
from nbclient import NotebookClient

from stormroute.config import REPO_ROOT, load_config
from stormroute.data.noaa import DETAILS_FILENAME, sha256_of

ARCHIVE_SHA256 = "858deeb5f332dd24a14f0e288b4ab7e2babd704116a05d7bb4899f86417b8272"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["sample", "full"], default="full")
    parser.add_argument(
        "--task", choices=["missingness", "counts", "temporal"], default="missingness"
    )
    args = parser.parse_args()
    notebook_path = REPO_ROOT / "notebooks/01_storm_events_eda.ipynb"
    notebook = nbformat.read(notebook_path, as_version=4)  # type: ignore[no-untyped-call]
    stop = next(
        i
        for i, cell in enumerate(notebook.cells)
        if cell.cell_type == "markdown" and cell.source.startswith("## 4.")
    )
    original_cells = notebook.cells
    notebook.cells = original_cells[:stop]
    if args.task in ("counts", "temporal"):
        # Execute the cleaner dependency and count subsection only. In particular,
        # do not regenerate the human spot-check sheet in section 4.
        cleaner = next(c for c in original_cells if c.source.startswith("events, report ="))
        start = next(i for i, c in enumerate(original_cells) if c.source.startswith("## 6."))
        end = next(
            i
            for i, c in enumerate(original_cells)
            if c.source.startswith(
                "## 7." if args.task == "temporal" else "### Reported event duration"
            )
        )
        notebook.cells.extend([cleaner, *original_cells[start:end]])
    notebook.cells.insert(
        0,
        nbformat.v4.new_code_cell(  # type: ignore[no-untyped-call]
            "import os\nos.environ['PYTHONUTF8'] = '1'\n"
            f"os.environ['STORMROUTE_DATA_MODE'] = {args.mode!r}"
        ),
    )
    with TemporaryDirectory(prefix="noaa_missingness_") as temp:
        if args.mode == "full":
            archive_path = REPO_ROOT / "data/raw/release_2026_09_26/noaa_storm_events.zip"
            if sha256_of(archive_path) != ARCHIVE_SHA256:
                raise ValueError("Release checksum differs from inspected source")
            inventory = {}
            active = {}
            with ZipFile(archive_path) as archive:
                for member in archive.namelist():
                    name = Path(member).name
                    match = DETAILS_FILENAME.fullmatch(name)
                    if not match:
                        continue
                    year = match["year"]
                    if year in active:
                        raise ValueError(f"Multiple detail files for {year}")
                    target = Path(temp) / name
                    target.write_bytes(archive.read(member))
                    active[year] = name
                    inventory[name] = {
                        "year": int(year),
                        "sha256": sha256_of(target),
                        "recorded_at_utc": datetime.now(UTC).isoformat(),
                    }
            period = load_config("data")["period"]
            if set(map(int, active)) != set(range(period["start_year"], period["end_year"] + 1)):
                raise ValueError("Release years do not match configured scope")
            (Path(temp) / "download_record.json").write_text(
                json.dumps({"files": inventory, "active": active}), encoding="utf-8"
            )
            # Only the executed copy uses temporary extracted inputs. No canonical
            # download record or tracked notebook source is replaced.
            for cell in notebook.cells:
                if cell.cell_type == "code" and 'data_path("noaa_raw")' in cell.source:
                    cell.source = "from pathlib import Path\n" + cell.source.replace(
                        'data_path("noaa_raw")', f"Path({temp!r})"
                    )
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        os.environ["IPYTHONDIR"] = str(REPO_ROOT / "outputs/executed/ipython")
        os.environ["PYTHONUTF8"] = "1"
        NotebookClient(notebook, timeout=180, kernel_name="python3").execute(cwd=str(REPO_ROOT))
    output = REPO_ROOT / "outputs/executed"
    output.mkdir(parents=True, exist_ok=True)
    nbformat.write(notebook, output / f"{args.task}_{args.mode}.ipynb")  # type: ignore[no-untyped-call]
    print(f"Executed {args.task} review in {args.mode} mode; no full-gate approval implied.")


if __name__ == "__main__":
    main()
