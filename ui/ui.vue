<template lang="pug">
.viz-grid
	.tile.double-width
		v-subheader Speed
		trusas-timeseries(:stream="speed()" :labels="{'mSpeed': 'Speed'}",:api="api")
	.tile.double-width
		v-subheader Rotation rate
		trusas-timeseries(:stream="rotation_speeds()" :labels="{0: 'x', 1: 'y', 2: 'z'}",:api="api")
	.tile.double-width
		v-subheader Acceleration
		trusas-timeseries(:stream="accelerations()" :labels="{0: 'x', 1: 'y', 2: 'z'}",:api="api")
	.tile Stuff
	.tile Stuff
	.filler
</template>

<script lang="coffee">
R = require 'lazyremote'
_ = require 'lodash'
JanusCat = require 'janus-cat'

module.exports =
	props:
		remote: required: true
		api: required: true
	
	mounted: ->
		vm = document.querySelector "#front-video"
		frontvid = await R.resolve @remote.services.front_video.outfile
		#R.resolve @api.janus_stream frontvid
		#vm.srcObject = await JanusCat.stream_from_janus "ws://localhost:8188", frontvid

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
