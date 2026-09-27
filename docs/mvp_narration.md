# MVP narration draft (about 75 seconds)

Draft for Mason to say. Every sentence matches what the code computes; Cameron reviews the
wording.

"StormRoute helps a traveler compare a route and a departure time by the flood hazard along
it. This is a replay of Hurricane Helene: Asheville to Charlotte, leaving at noon on 27
September 2024.

We split the route into county stretches and work out when the traveler reaches each one.
For each stretch our prototype hazard indicator looks at two things: the rainfall in the
previous 24 and 72 hours, and any official National Weather Service flood warnings or
watches that had already been issued at departure. The higher of the two sets the level, from
lower concern to severe concern. A warning can raise the level. It can never lower it.

Here, both routes come out at severe concern. The highest-concern stretch is Buncombe County,
with 233 millimeters of rain in the prior day and active flash flood warnings. So the
advisory is to consider delaying travel and to check official warnings and road closures.

What this is not: it is not a trained model, not a probability, and not a validated score.
The rainfall is reanalysis data that a real traveler would not have had at departure, and the
thresholds are our own round numbers. It does not say a road is open or safe.

The next scientific step is the part we have already started: a reviewed exploration of ten
years of North Carolina flood reports, then a historical weather table, baseline models,
calibration, and a held-out 2024 test, before any number is called a risk."
