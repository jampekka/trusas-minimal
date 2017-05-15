#!/bin/sh

tail -f $1 | ./node_modules/janus-cat/janus_ts_video.coffee -n $1
