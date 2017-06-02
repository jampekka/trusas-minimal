<template lang="pug">
	.trusas-protocol
		h4.status Unknown status
		h4.block Unknown block
		v-btn(@click.native="cmd('start')") Start
		v-btn(@click.native="cmd('end')") End
		//v-btn(@click.native="cmd('lift')") Lift
		//v-btn(@click.native="cmd('blind')") Blind
		v-btn(@click.native="cmd('unblind')") Unblind
		v-btn(@click.native="cmd('control')") Control
		audio(src="bell.ogg" class="bell" style="display: none")
</template>

<style scoped>

</style>

<script lang="coffee">
R = require 'lazyremote'
module.exports =
	props:
		remote: required: true
		api: required: true
	
	mounted: ->
		@socketpath = (await R.resolve @remote.directory) + "/protocol.control"
		status_el = @$el.querySelector ".status"
		block_el = @$el.querySelector ".block"
		audio_el = @$el.querySelector ".bell"
		R.resolve @remote.services.protocol.dataStream('start').forEach (msg) ->
			[hdr, msg] = msg
			if 'message' of msg
				status_el.innerHTML = msg.message
				audio_el.play()
			if 'block_init' of msg
				block_el.innerHTML = "#{msg.block_type[0]} (#{msg.block_init})"

	
	methods:
		cmd: (cmd) ->
			R.resolve @api.socket_command @socketpath, command: cmd
</script>
