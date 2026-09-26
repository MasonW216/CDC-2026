"""Run the full repository verification suite.

Makefile target : make verify
Milestone       : 0 (extended at every later milestone)

One command a judge or teammate can trust. Checks:
  * required files and directories exist;
  * every config and manifest parses and satisfies its schema;
  * no secret, raw dataset, or absolute local path is tracked;
  * notebooks carry no stored outputs and no out-of-order execution counts;
  * declared artifacts exist and match their recorded checksums;
  * the model manifest agrees with docs/model_card.md.

Exits non-zero on the first failure with an actionable message.
"""

# TODO(milestone-0): implement. See docs/build_guide.md.
