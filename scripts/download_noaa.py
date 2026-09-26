"""Download NOAA Storm Events detail files for 2015-2024.

Makefile target : make download
Milestone       : 1
Reads           : data/data_manifest.yaml
Writes          : data/raw/noaa_storm_events/, and the resolved filenames and
                  access time back into the manifest

Behavior required by the build guide:
  * identify the annual detail file for each year 2015-2024;
  * record the resolved filename (the c-date suffix changes on republication)
    and the access timestamp, so a run is reproducible;
  * never silently overwrite a file whose content differs -- stop and report;
  * support --sample for CI and notebook smoke tests;
  * do NOT filter here. The raw layer stays a faithful copy of the source;
    North Carolina and hazard filtering happen in stormroute.data.noaa.
"""

# TODO(milestone-1): implement. See docs/build_guide.md.
