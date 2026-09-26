"""Weather Safety Score invariants.

Near-total coverage required. Asserts:
  * zero risk on every segment produces exactly 100;
  * the score is always an integer within [0, 100];
  * raising any segment probability never raises the score;
  * increasing time spent in a risky interval never raises the score;
  * splitting one interval into smaller identical pieces changes nothing
    (the additivity property the hazard formulation exists to provide);
  * a short high-risk segment is not hidden inside a long low-risk route;
  * the same versioned inputs always produce the same score;
  * component values are exposed so any displayed score can be reconstructed.
"""

# TODO(milestone-5): implement. See docs/build_guide.md.
