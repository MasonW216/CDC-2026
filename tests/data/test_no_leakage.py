"""No feature may use information unavailable before departure.

The project's most important test file. Must assert:
  * the feature matrix contains no post-event column -- injuries, deaths,
    property damage, narratives, episode id, or event end time;
  * a rolling feature for a window starting at T reads no observation after T,
    verified by perturbing future hours and asserting the feature is unchanged;
  * climatology and historical-rate features are fit on training years only;
  * no 2024 row participates in any fitting operation;
  * Social Vulnerability Index data never enters the feature matrix.

A failure here invalidates every reported metric, so these tests must be
readable enough that a reviewer can confirm they check what they claim.
"""

# TODO(milestone-3): implement. See docs/build_guide.md.
