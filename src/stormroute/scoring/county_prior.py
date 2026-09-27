"""A real Bayesian hierarchical prior over county-level flood-report rates.

Answers a question the live rule alone cannot: does this county's own 10-year reporting
history suggest it runs hotter or colder than the state average, independent of tonight's
weather? Built from the same 2015-2024 NOAA Storm Events data the EDA already validated
(2,220 qualifying events, 1,499 positive county-six-hour-windows of 1,461,200 -- this
module's own count matches that headline number exactly, checked below).

This is honestly a **descriptive Bayesian summary**, not a forecast: it has no held-out
test, no calibration, and it is not what Milestone 4's planned gradient-boosted model is
for. It answers "how has this county behaved historically", not "what will happen". Never
call it validated or predictive in anything derived from it.

## The model

One Beta-Binomial per county, a textbook conjugate hierarchical model:

  * Population prior: Beta(alpha, beta), its two parameters set by the method of moments
    on the 100 counties' own observed rates -- a standard empirical-Bayes estimate of the
    hierarchy's shape, not an arbitrary guess.
  * County c has `positive_windows_c` positive six-hour windows (the onset rule, same
    definition as `docs/data_card.md` and the EDA) out of `total_windows_c` (every
    six-hour window 2015-2024, ~14,604 per county).
  * Posterior: Beta(alpha + positive_windows_c, beta + total_windows_c - positive_windows_c).
  * Posterior mean is the county's fitted rate. This is partial pooling by construction:
    Graham County's zero observed positives gets pulled up toward the state mean instead
    of being reported as a hard zero; Wake County's rich history (76 positives) stays close
    to its own observed rate, since the data dominates the weak population prior there.

## How it enters the score

`concern.py` adds a third term to its existing `max(rain_component, alert_component)`:
`county_prior_component`, scaled from the posterior mean *relative to the state average*,
capped well below what live rain or an active alert can reach, and -- like every other
term in that `max()` -- it can only ever raise a segment's index, never lower it. A county
with a below-average historical rate contributes 0, not a negative adjustment.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from stormroute.config import REPO_ROOT
from stormroute.data.geography import load_sample_counties
from stormroute.data.noaa import load_events

ARTIFACT = REPO_ROOT / "artifacts" / "models" / "county_prior.json"
START_YEAR = 2015
END_YEAR = 2024
WINDOW_HOURS = 6

# How far above the state average a posterior rate must be to reach the component's own
# full scale (100). A county at or below the state average contributes 0. This is a team
# policy choice, exactly like the live rule's 20 mm/h and 100 mm/24h scales -- stated
# plainly, not learned, and deliberately capped by `MAX_COMPONENT` so no county's history
# alone can ever reach "Severe" without real-time rain or an alert also present.
RATE_RATIO_FULL_SCALE = 4.0
MAX_COMPONENT = 45.0


@dataclass(frozen=True)
class CountyPrior:
    """One county's fitted Bayesian rate and the raw counts behind it."""

    county_fips: str
    positive_windows: int
    total_windows: int
    posterior_mean_rate: float
    credible_low: float
    credible_high: float
    component: float


def _county_window_counts() -> pd.DataFrame:
    """Real positive-window counts per county, 2015-2024, the exact EDA onset rule."""
    events, _ = load_events("full")
    events = events.assign(window_start_utc=events["begin_utc"].dt.floor(f"{WINDOW_HOURS}h"))
    positive = events[["county_fips", "window_start_utc"]].drop_duplicates()
    counts = positive.groupby("county_fips").size().rename("positive_windows")

    counties = load_sample_counties()[["county_fips"]]
    years = END_YEAR - START_YEAR + 1
    total_windows = years * 365 * 24 // WINDOW_HOURS + 4 * 24 // WINDOW_HOURS  # + leap days
    table = counties.merge(counts.reset_index(), on="county_fips", how="left").fillna(0)
    table["positive_windows"] = table["positive_windows"].astype(int)
    table["total_windows"] = total_windows
    return pd.DataFrame(table)


def _method_of_moments_beta(rates: pd.Series) -> tuple[float, float]:
    """Fit Beta(alpha, beta) to observed county rates by matching mean and variance.

    Standard empirical-Bayes estimate for a Beta-Binomial hierarchy (see e.g. Gelman et
    al., *Bayesian Data Analysis*, ch. 5). Falls back to a weak, symmetric prior if the
    observed variance is degenerate (e.g. all counties identical), which cannot happen
    with real data but keeps this defined for any input.
    """
    mean = float(rates.mean())
    variance = float(rates.var(ddof=1))
    if variance <= 0 or not (0 < mean < 1):
        return 1.0, 1.0
    common = mean * (1 - mean) / variance - 1
    alpha = max(mean * common, 1e-3)
    beta = max((1 - mean) * common, 1e-3)
    return alpha, beta


def fit_county_priors() -> tuple[list[CountyPrior], dict[str, Any]]:
    """Fit the hierarchical model fresh from the raw NOAA data. No network; local files only."""
    table = _county_window_counts()
    observed_rates = table["positive_windows"] / table["total_windows"]
    alpha, beta = _method_of_moments_beta(observed_rates)
    state_posterior_mean = (alpha + table["positive_windows"].sum()) / (
        alpha + beta + table["total_windows"].sum()
    )

    priors = []
    rows = zip(
        table["county_fips"].tolist(),
        table["positive_windows"].tolist(),
        table["total_windows"].tolist(),
        strict=True,
    )
    for county_fips, raw_positive, raw_total in rows:
        positive_windows = int(raw_positive)
        total_windows = int(raw_total)
        post_alpha = alpha + positive_windows
        post_beta = beta + total_windows - positive_windows
        posterior_mean = float(post_alpha / (post_alpha + post_beta))
        # 95% credible interval from the Beta posterior's quantiles.
        low, high = _beta_quantiles(post_alpha, post_beta, (0.025, 0.975))
        ratio = posterior_mean / state_posterior_mean if state_posterior_mean > 0 else 0.0
        component = round(
            min(MAX_COMPONENT, MAX_COMPONENT * max(0.0, ratio - 1) / (RATE_RATIO_FULL_SCALE - 1)),
            2,
        )
        priors.append(
            CountyPrior(
                county_fips=str(county_fips),
                positive_windows=positive_windows,
                total_windows=total_windows,
                posterior_mean_rate=round(posterior_mean, 6),
                credible_low=round(low, 6),
                credible_high=round(high, 6),
                component=component,
            )
        )

    meta = {
        "method": "Beta-Binomial conjugate, empirical-Bayes hyperparameters (method of moments)",
        "population_alpha": round(alpha, 4),
        "population_beta": round(beta, 4),
        "state_posterior_mean_rate": round(state_posterior_mean, 6),
        "period": f"{START_YEAR}-{END_YEAR}",
        "window_hours": WINDOW_HOURS,
        "total_positive_windows": int(table["positive_windows"].sum()),
        "total_windows": int(table["total_windows"].sum()),
        "source": "NOAA Storm Events details, onset rule (same definition as the EDA gate)",
        "computed_utc": datetime.now(UTC).isoformat(),
        "not_a_forecast": (
            "Descriptive historical summary only. No held-out test, no calibration. Not the "
            "Milestone 4 trained model and must never be presented as validated or predictive."
        ),
    }
    return priors, meta


def _beta_quantiles(
    alpha: float, beta: float, quantiles: tuple[float, float]
) -> tuple[float, float]:
    """Beta distribution quantiles without a SciPy dependency (bisection on the CDF)."""
    from math import lgamma

    def log_beta(a: float, b: float) -> float:
        return lgamma(a) + lgamma(b) - lgamma(a + b)

    log_norm = log_beta(alpha, beta)

    def pdf(x: float) -> float:
        if x <= 0 or x >= 1:
            return 0.0
        import math

        return math.exp((alpha - 1) * math.log(x) + (beta - 1) * math.log(1 - x) - log_norm)

    def cdf(x: float, steps: int = 2000) -> float:
        # Fine enough for a reporting-only credible interval; not used in scoring.
        if x <= 0:
            return 0.0
        if x >= 1:
            return 1.0
        step = x / steps
        total = 0.0
        for i in range(steps):
            total += pdf((i + 0.5) * step) * step
        return min(1.0, total)

    results = []
    for q in quantiles:
        lo, hi = 0.0, 1.0
        for _ in range(40):
            mid = (lo + hi) / 2
            if cdf(mid) < q:
                lo = mid
            else:
                hi = mid
        results.append((lo + hi) / 2)
    return results[0], results[1]


def write_artifact() -> Path:
    """Fit and cache the priors, with provenance, so scoring never has to refit at request time."""
    priors, meta = fit_county_priors()
    payload = {
        "meta": meta,
        "counties": {
            p.county_fips: {
                "positive_windows": p.positive_windows,
                "total_windows": p.total_windows,
                "posterior_mean_rate": p.posterior_mean_rate,
                "credible_low": p.credible_low,
                "credible_high": p.credible_high,
                "component": p.component,
            }
            for p in priors
        },
    }
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return ARTIFACT


_cache: dict[str, dict[str, Any]] | None = None


def load_county_components() -> dict[str, float]:
    """`{county_fips: component}` from the cached artifact, read once per process."""
    global _cache
    if _cache is None:
        if not ARTIFACT.exists():
            write_artifact()
        _cache = json.loads(ARTIFACT.read_text(encoding="utf-8"))["counties"]
    assert _cache is not None
    return {fips: row["component"] for fips, row in _cache.items()}


if __name__ == "__main__":
    path = write_artifact()
    print(f"wrote {path}")
