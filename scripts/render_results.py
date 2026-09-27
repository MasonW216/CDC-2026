"""Render the MVP replay result as one self-contained HTML page. No Node, no network.

Makefile target : none (MVP fallback screen)
Reads           : artifacts/demo/prototype_result.json
Writes          : artifacts/demo/results.html

Insurance for the demo: open the file in any browser. It shows the same contract the
React screen should: route as an ordered sequence of county stretches, arrival times, the
indicator with its source and status, the highest-concern segment, official alerts
above the advisory, and the replay caveat. Levels are conveyed by text and a pattern
as well as color.
"""

# ruff: noqa: E501  (HTML template lines)

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
from typing import Any

from stormroute.config import REPO_ROOT

DEMO = REPO_ROOT / "artifacts" / "demo"
EDT = timezone(timedelta(hours=-4), "EDT")
CLASSES = {0: "l0", 1: "l1", 2: "l2", 3: "l3", None: "ln"}

CSS = """
:root{--bg:#fcfcfb;--ink:#1f1f1d;--mute:#5f5e5a;--line:#d8d6d0;--card:#fff;
--l0:#e6f0e6;--l1:#fff2c2;--l2:#ffd9a8;--l3:#f7b4b0;--ln:#e6e6e6;--acc:#2a78d6}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--ink:#efefec;--mute:#a9a8a2;
--line:#3a3a37;--card:#1e1e1c;--l0:#243524;--l1:#4a4020;--l2:#553a1c;--l3:#5c2624;--ln:#333}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:16px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:920px;margin:0 auto;padding:16px}
h1{font-size:1.4rem;margin:.2rem 0}h2{font-size:1.1rem;margin:1.4rem 0 .4rem}
.tag{display:inline-block;border:1px solid var(--line);border-radius:4px;padding:1px 8px;
font-size:.8rem;color:var(--mute)}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px 14px;
margin:.6rem 0}
.alerts{border-left:6px solid #b3261e}.banner{font-weight:600}
.level{display:inline-block;padding:2px 10px;border-radius:4px;font-weight:700;border:1px solid var(--line)}
.l0{background:var(--l0)}.l1{background:var(--l1)}.l2{background:var(--l2)}
.l3{background:var(--l3)}.ln{background:var(--ln)}
.l3.level{background-image:repeating-linear-gradient(45deg,transparent 0 6px,rgba(0,0,0,.12) 6px 9px)}
.bar{display:flex;gap:2px;margin:.4rem 0}.bar div{flex:1;min-width:0;height:34px;border:1px solid var(--line);
border-radius:3px;font-size:.7rem;padding:2px 3px;overflow:hidden;white-space:nowrap}
table{width:100%;border-collapse:collapse;font-size:.9rem}th,td{text-align:left;
padding:5px 6px;border-bottom:1px solid var(--line);vertical-align:top}
.mute{color:var(--mute);font-size:.85rem}.tabs{display:flex;gap:6px;flex-wrap:wrap}
details summary{cursor:pointer}
"""


def _local(text: str) -> str:
    stamp = datetime.fromisoformat(text).astimezone(EDT)
    return stamp.strftime("%H:%M EDT")


def _level(label: str, level: int | None) -> str:
    return f'<span class="level {CLASSES[level]}">{escape(label)}</span>'


def _route(rid: str, route: dict[str, Any]) -> str:
    worst = route["highest_concern_segment"]
    segments = route["segments"]
    bars = "".join(
        f'<div class="{CLASSES[s["level"]]}" title="{escape(s["county_name"])}: {escape(s["label"])}">'
        f"{escape(s['county_name'])}</div>"
        for s in segments
    )
    rows = "".join(
        f"<tr><td>{escape(s['county_name'])}</td><td>{_local(s['arrival_utc'])}<br>"
        f'<span class="mute">{s["arrival_utc"][11:16]} UTC, window from '
        f"{s['window_start_utc'][11:16]} UTC</span></td>"
        f"<td>{_level(s['label'], s['level'])}</td><td>{escape(s['reason'])}"
        f'<br><span class="mute">Source: {escape(", ".join(s["sources"]) or "none")}. '
        f"Rainfall status: {escape(s['data_status'])}.</span></td></tr>"
        for s in segments
    )
    alerts = sorted({a for s in segments for a in s["alerts_used"]})
    alert_html = (
        '<div class="card alerts"><div class="banner">Official NWS flood products '
        "(county-coded in this replay) active at a displayed stretch's arrival</div><ul>"
        + "".join(f"<li>{escape(a)}</li>" for a in alerts)
        + "</ul></div>"
        if alerts
        else '<div class="card">No county-coded flood products active for these stretches '
        "in the cached data.</div>"
    )
    return f"""<section id="{escape(rid)}"><h2>{escape(rid.replace("_", " ").title())}: {route["duration_minutes"]:.0f} min, {route["distance_km"]:.0f} km</h2>
<div class="card"><p>{escape(route["indicator_name"])}: {_level(route["trip_label"], route["trip_level"])}</p>
<div class="bar" role="img" aria-label="Route by county, in travel order">{bars}</div></div>
{alert_html}
<div class="card"><strong>Highest-concern segment:</strong> {escape(worst["county_name"]) if worst else "none"}
{f"(arrive {_local(worst['arrival_utc'])}): " + escape(worst["reason"]) if worst else ""}</div>
<div class="card"><strong>Advisory.</strong> {escape(route["advisory"])}</div>
<details><summary>Every stretch, with source and rainfall coverage</summary><table><thead><tr>
<th>County</th><th>Arrival</th><th>Level</th><th>Reason</th></tr></thead><tbody>{rows}</tbody></table></details>
<p class="mute">{escape(route["replay_caveat"])}</p></section>"""


def render(result: dict[str, Any]) -> str:
    """Build the page from the result JSON."""
    prov = result["inputs_provenance"]
    comp = result["comparison"]
    comp_html = (
        '<div class="card"><strong>Two routes compared.</strong> '
        + "; ".join(
            f"{escape(k.replace('_', ' ').title())}: {escape(result['routes'][k]['trip_label'])}"
            for k in comp["levels"]
        )
        + f". {escape(comp['note'])}</div>"
        if comp
        else ""
    )
    sections = "".join(_route(rid, r) for rid, r in result["routes"].items())
    dep = _local(datetime.fromisoformat(result["departure_time"]).isoformat())
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>StormRoute MVP replay</title>
<style>{CSS}</style></head><body><main>
<p><span class="tag">Prototype</span> <span class="tag">Replay of a past storm</span></p>
<h1>{escape(result["origin"]["label"])} to {escape(result["destination"]["label"])}</h1>
<p>Departing {dep} on {result["departure_time"][:10]}. Hurricane Helene replay.</p>
<div class="card"><strong>What this is.</strong> A prototype hazard indicator: a rule over
rainfall and official NWS flood products. It is not a trained model, not a probability, and
not a validated score. It does not say a road is open or safe. Official warnings and road
closures take priority.</div>
{comp_html}{sections}
<h2>Where the inputs come from</h2>
<div class="card mute">Rainfall: {escape(prov["sources"]["precipitation"])}<br>
Alerts: {escape(prov["sources"]["alerts"])}<br>Retrieved {escape(prov["retrieved_utc"])}.
{prov["zone_coded_alert_rows_excluded"]} zone-coded alert rows are not mapped to counties;
county alert coverage may be incomplete.<br>Route: {escape(result["route_fixture_provenance"])}</div>
</main></body></html>
"""


def main() -> None:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", type=Path, default=DEMO / "prototype_result.json")
    parser.add_argument("--out", type=Path, default=DEMO / "results.html")
    args = parser.parse_args()
    result = json.loads(args.result.read_text(encoding="utf-8"))
    args.out.write_text(render(result), encoding="utf-8")
    print("wrote", args.out)


if __name__ == "__main__":
    main()
