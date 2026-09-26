"""Fetch forecasts and official NWS alerts.

Calls api.weather.gov with the required descriptive User-Agent, validates every
response, and maps alert severity onto the policy floors in
`configs/scoring.yaml`.

When alerts cannot be retrieved, the response says so explicitly. Silently
treating an unreachable alert service as "no alerts" would understate risk,
which is the one direction of error this project must not make.
"""

# TODO(milestone-6): implement. See docs/build_guide.md.
