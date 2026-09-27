# MVP narration draft (about 75 seconds)

Draft for Mason to say. Every sentence matches what the code computes; Cameron reviews the
wording.

"StormRoute helps a traveler compare a route and a departure time by the flood hazard along
it. This is a replay of Hurricane Helene: Asheville to Charlotte, leaving at noon on 27
September 2024.

We split the route into county stretches and work out when the traveler reaches each one.
For each stretch our prototype hazard indicator looks at rainfall totals ending at the
start of its six-hour UTC arrival window and county-coded National Weather Service flood
products issued by departure. The higher rainfall or alert tier sets the level, from lower
concern to severe concern. An alert can raise the level; it cannot lower it.

Here, both routes come out at severe concern. Buncombe County is the first of several
stretches at that level, with about 233 millimeters in the 24-hour window ending at
12:00 UTC and active flash flood warnings. The shorter route is not a lower-concern
alternative. The advisory is to consider delaying travel and check official warnings and
road closures.

What this is not: it is not a trained model, not a probability, and not a validated score.
The rainfall is retrospective reanalysis that a traveler would not have had at departure;
some later stretches even use hours after departure. The thresholds are our own round
numbers. One point stands for a whole county, some zone-coded alerts are missing, and
this does not say a road is open or safe.

The next scientific step is the part we have already started: a reviewed exploration of ten
years of North Carolina flood reports, then a historical weather table, baseline models,
calibration, and a held-out 2024 test, before any number is called a risk."
