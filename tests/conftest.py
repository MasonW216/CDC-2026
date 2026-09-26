"""Shared fixtures for the test suite.

Provides repository-root and sample-data path fixtures so no test depends on
the directory it was invoked from, loaders for the tracked fixtures in
`data/sample/`, and the frozen scoring configuration.

Tests must never reach the network. Anything that would is marked
`@pytest.mark.network` and excluded from CI.
"""

# TODO(milestone-0): implement. See docs/build_guide.md.
