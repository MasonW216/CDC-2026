"""Pydantic request and response models.

The wire contract, versioned and tested. A score response must carry:

  * model and data version;
  * the safety score and its plain-language band;
  * modeled route risk both before and after alert policy;
  * the worst segment and its expected arrival time;
  * the primary contributing factors;
  * official alerts intersecting the route;
  * alternative routes and departure times;
  * the recommendation, with score delta and time cost;
  * a confidence/coverage indicator;
  * warnings and limitations.

A score is never serialized without the information needed to interpret it.
`frontend/src/types/trip.ts` mirrors these shapes and must change with them.
"""

# TODO(milestone-6): implement. See docs/build_guide.md.
