"""Derive static terrain features per county.

Mean elevation and mean slope from the elevation source. Static in time, so
these are joined once and carry no leakage risk -- they are known long before
any departure.

Terrain is why a mountain county and a coastal county with identical rainfall
do not carry identical flood hazard, so these features matter more than their
simplicity suggests.
"""

# TODO(milestone-3): implement. See docs/build_guide.md.
