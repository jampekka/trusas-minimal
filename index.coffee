trusas = require 'trusas-server'
Path = require 'path'
subprocess = require 'child_process'

spec =
	label: "Car"
	services:
		sensors:
			label: "Sensors"
			command: require.resolve 'trusas-android/sensors.py'
		location:
			label: "Location"
			command: require.resolve 'trusas-android/location.py'
		test:
			label: "Test"
			command: require.resolve 'trusas0-pycore/timestamper.py'
		front_video:
			label: "Front video"
			command: [
				require.resolve('trusas-gstreamer/record_h264.coffee'),
				'-v', '/dev/v4l/by-id/usb-046d_HD_Pro_Webcam_C920_8C12D2EF-video-index0',
				'-a', 'alsa_input.usb-046d_HD_Pro_Webcam_C920_8C12D2EF-02.analog-stereo'
			]
			outfile: "${basepath}.ts"
trusas.serve
	spec: spec
	directory: "./test_sessions"
	ui: Path.join __dirname, './ui'
	api: (api) ->
		api = api()
		api.janus_stream = (path) ->
				console.log "Launching janus with #{path}"
				subprocess.spawn './janus-cat-tail.sh', [path],
					stdio: ['inherit', 'inherit', 'inherit']
				return

		api.forEachNotPending = (f) ->
			isPending = false
			clearPending = -> isPending = false
			(v) ->
				return if isPending
				isPending = true
				f(v).then clearPending, clearPending
		return api
				
			

