"""File-based response and upstream cache.

Caches upstream responses and scored trips on disk, and serves the frozen demo
artifacts. Keys include the model and data version, so a new model never reads
a previous model's cached scores.
"""

# TODO(milestone-6): implement. See docs/build_guide.md.
