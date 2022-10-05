#!/bin/bash

export PDAL_ALLOW_SHELL=1


DEBUG="--debug --verbose 7"
CLEANUP=
# copies down data from EPT
pdal pipeline before.json $DEBUG
pdal pipeline after.json $DEBUG


pdal translate -i before.copc.laz -o before-filtered.copc.laz --reader "readers.las" --json filter.json $DEBUG
pdal translate -i after.copc.laz -o after-filtered.copc.laz --reader "readers.las" --json filter.json $DEBUG


# select ground, building, and vegetation (gbv)
pdal translate -i before-filtered.copc.laz -o before-gbv.copc.laz --reader "readers.las"  --filter assign --filters.assign.value="Classification=2" $DEBUG
pdal translate -i after-filtered.copc.laz -o after-gbv.copc.laz --reader "readers.las" --filter range --filters.range.limits="Classification[2:6]" --filter assign --filters.assign.value="Classification=0" $DEBUG


# merge up data
read -r -d '' pipeline << EOM
[
    "before-gbv.copc.laz",
    "after-gbv.copc.laz",
    {
        "type": "filters.merge"
    },
    "merged.copc.laz"
]
EOM
echo $pipeline | pdal pipeline $DEBUG --stdin

# cluster data
read -r -d '' pipeline << EOM
[
    {
        "type": "readers.las",
        "filename":"merged.copc.laz"
    },
    {
        "type": "filters.hag_delaunay"
    },
    {
        "type":"filters.dbscan",
        "min_points":125,
        "eps":2.0,
        "dimensions":"X,Y,Z,HeightAboveGround"
    },
    {
        "type": "filters.ferry",
        "dimensions":"ClusterID => DBScan"
    },
    {
        "type":"filters.cluster",
        "min_points":125,
        "tolerance":2.0
    },
    {
        "type": "writers.las",
        "filename":"clustered.laz",
        "forward":"all",
        "extra_dims":"all",
        "minor_version":4,
        "where": "Classification == 2",
        "where":"HeightAboveGround > 1.0"

    }
]
EOM
echo $pipeline | pdal pipeline $DEBUG --stdin


if [ -z ${CLEANUP+x} ]; then
    echo "CLEANUP environment variable not set. Not erasing intermediate output";
else
    echo "CLEANUP environment variable set. Erasing intermediate output";
    rm before-gbv.copc.laz
    rm after-gbv.copc.laz
    rm merged.copc.laz
    rm before.copc.laz
    rm after.copc.laz
    rm before-filtered.copc.laz
    rm after-filtered.copc.laz
fi


