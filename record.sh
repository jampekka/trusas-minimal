#!/bin/bash
set -o noclobber
trap 'kill $(jobs -p)' EXIT

DIR=$1
mkdir $DIR

./node_modules/trusas-android/sensors.py >$DIR/sensors.jsons &
./node_modules/trusas-android/location.py >$DIR/location.jsons &

echo "Logging data. Stop with ctrl-c" 1>&2
wait $(jobs -p)
