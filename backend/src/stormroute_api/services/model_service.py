"""Load the model artifact and produce county-window probabilities.

Loads `stormroute_model.joblib` once at startup, verifies it against
`model_manifest.json` (checksum and feature list), and refuses to serve a
mismatch rather than returning quietly wrong probabilities.

Only artifacts this repository produced are ever loaded: joblib
deserialization executes code from the file. See SECURITY.md.
"""

# TODO(milestone-6): implement. See docs/build_guide.md.
