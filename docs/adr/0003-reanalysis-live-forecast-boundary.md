# ADR 0003 — Reanalysis for training, forecasts for live use

- **Status:** Accepted as a known limitation
- **Date:** 2026-09-26

## Context

Training needs ten years of consistent hourly weather for every county. The planned
source is **reanalysis** (ERA5-Land): a retrospective, gridded
reconstruction of what the weather *was*.

A live traveler departing tomorrow has no reanalysis. They have a **forecast** —
noisier, differently biased, and with a different error structure.

## Decision

- Train and evaluate on reanalysis.
- The planned judged demo is a **cached historical replay** (Helene), using
  retrospective weather inputs. It does not recreate the forecasts actually
  available to a traveler at that time.
- Live forecast mode is **stretch scope** and, if built, is labeled in the UI as
  using forecast inputs the model was not trained on.

## Consequences

- Future metrics describe performance on retrospective reanalysis inputs.
  They do not establish live accuracy or a numerical upper bound on it. This
  limitation must accompany any reported result. This claim correction does
  not change the decision to use reanalysis for the historical experiment.
- This train-serve skew is stated in the model card, the methodology page, the
  README limitations section, and the presentation.
- Official NWS alerts, which *are* live and forward-looking, act as a floor that
  can only raise risk — partial protection against the model under-reading a
  forecast.
- A future version should evaluate on archived forecasts before any claim about
  live accuracy is made.
