<template lang="pug">
.viz-grid
	.tile.double-width
		trusas-protocol(:remote="remote", :api="api")
	.tile.double-width
		v-subheader Speed
		trusas-timeseries(:stream="speed()" :labels="{'mSpeed': 'Speed'}",:api="api")
	//.tile.double-width
	//	v-subheader Rotation rate
	//	trusas-timeseries(:stream="rotation_speeds()" :labels="{0: 'x', 1: 'y', 2: 'z'}",:api="api")
	.tile.double-width
		v-subheader Acceleration
		trusas-timeseries(:stream="accelerations()" :labels="{0: 'x', 1: 'y', 2: 'z'}",:api="api")
	.filler
</template>

<script lang="coffee">
R = require 'lazyremote'
_ = require 'lodash'

module.exports =
	props:
		remote: required: true
		api: required: true
	
	methods:
		speed: ->
			@remote.services.location.dataStream()
			.filter R.purejs (m) ->
				m[1].mProvider != 'network'
			.map R.purejs (m) ->
				[m[0], mSpeed: m[1].mSpeed]

		orientation: ->
			@remote.services.sensors.dataStream()
			.filter R.purejs (m) ->
				m[1].sensor_type == 3
			.throttle(100)
			.map R.purejs (m) ->
				[m[0], m[1].values]

		rotation_speeds: ->
			@remote.services.sensors.dataStream()
			.filter R.purejs (m) ->
				m[1].sensor_type == 4 # Gyroscope
			.throttle(100)
			.map R.purejs (m) ->
				[m[0], m[1].values]

		accelerations: ->
			@remote.services.sensors.dataStream()
			.filter R.purejs (m) ->
				m[1].sensor_type == 10 # Linear acceleration
			.throttle(100)
			.map R.purejs (m) ->
				[m[0], m[1].values]

</script>
