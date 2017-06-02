trusas = require 'trusas-server'
Path = require 'path'
subprocess = require 'child_process'
Readline = require 'readline'
Most = require 'most'
unix = require 'unix-dgram'

CAMERA_ID = "8C12D2EF"
#CAMERA_ID = "CBFB41EF"

spec =
	label: "Car"
	services:
		sensors:
			label: "Sensors"
			command: require.resolve 'trusas-android/sensors.py'
		location:
			label: "Location"
			command: require.resolve 'trusas-android/location.py'
		#test:
		#	label: "Test"
		#	command: require.resolve 'trusas0-pycore/timestamper.py'
		front_video:
			label: "Front video"
			command: [
				require.resolve('trusas-gstreamer/record_h264.coffee'),
				'-v', "/dev/v4l/by-id/usb-046d_HD_Pro_Webcam_C920_#{CAMERA_ID}-video-index0",
				'-a', "alsa_input.usb-046d_HD_Pro_Webcam_C920_#{CAMERA_ID}-02.analog-stereo"
			]
			outfile: "${basepath}.ts"
		ibeo:
			label: "Laser scanner"
			command: [
				require.resolve('trusas-ibeo/idc_recorder'),
				"10.152.36.100"
			]
			outfile: "${basepath}.idc"
		blinder:
			label: "Blinder"
			command: [
				require.resolve('./blinder/blinder.py'),
				"-c", "${directory}/blinder.control"
			]
			outfile: "${directory}/blinder.jsons"
		protocol:
			label: "Protocol"
			command: [
				require.resolve("./protocol.py"),
				"${directory}/blinder.control", "${directory}/blinder.jsons", "${directory}/protocol.control", "${basepath}.jsons"
			]
			outfile: "${basepath}.jsons"
startup = trusas.serve
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

		api.socket_command = (path, command) ->
			buf = new Buffer JSON.stringify command
			socket = unix.createSocket('unix_dgram')
			socket.send buf, 0, buf.length, path
			socket.close()


		api.forEachNotPending = (f) ->
			isPending = false
			clearPending = -> isPending = false
			(v) ->
				return if isPending
				isPending = true
				f(v).then clearPending, clearPending

		api.video_preview = (path) ->
			subprocess.spawn require.resolve('trusas-gstreamer/live_view.sh'), [path]
			return

		api.ibeo_stream = (session, callback) ->
			fpath = session.services.ibeo.outfile
			to_obj = require.resolve('trusas-ibeo/objects_to_json')
			cmd = "tail -F #{fpath} | #{to_obj}"
			proc = subprocess.spawn cmd, [],
				shell: true
			lines = Readline.createInterface input: proc.stdout, terminal: false
			msgs = Most.fromEvent("line", lines).map (line) ->
				JSON.parse line
			msgs.forEach api.forEachNotPending callback
		api.unix

		return api
				
			
startup.then ->
	console.log "Listening"
