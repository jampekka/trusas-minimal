trusas = require 'trusas-server'
Path = require 'path'
subprocess = require 'child_process'
Readline = require 'readline'
Most = require 'most'
unix = require 'unix-dgram'

CAMERA_ID = "8C12D2EF"
#CAMERA_ID = "CBFB41EF"

spec =
	label: "Minimal"
	services:
		sensors:
			label: "Sensors"
			command: require.resolve 'trusas-android/sensors.py'
		location:
			label: "Location"
			command: require.resolve 'trusas-android/location.py'

startup = trusas.serve
	spec: spec
	directory: "./test_sessions"
	ui: Path.join __dirname, './ui'
	api: (api) ->
		api = api()
		return api
				
			
startup.then ->
	console.log "Listening"
