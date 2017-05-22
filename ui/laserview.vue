<template>
	<div class="trusas-laserview"></div>
</template>

<style scoped>
.trusas-laserview {
	width: 100%;
	height: 100%;
}

.trusas-laserview > canvas{
	width: 100%;
	height: 100%;
}
</style>

<script lang="coffee">
THREE = require 'three'
module.exports =
	props:
		stream: required: true
		#api: required: true
	
	mounted: ->
		scene = new THREE.Scene()
		camera = new THREE.PerspectiveCamera 75, 1, 0.1, 1000
		camera.position.y = 2.0
		renderer = new THREE.WebGLRenderer()
		setSize = =>
			w = @$el.clientWidth
			h = @$el.clientHeight
			renderer.setSize w, h
			camera.aspect = w/h
			camera.updateProjectionMatrix()
		setSize()
		
		window.addEventListener "resize", setSize
		@$el.appendChild renderer.domElement

		objects = [
			{id: 0, contour: [
				{x: -1, y: 11},
				{x: -1, y: 10},
				{x: 1, y: 10},
				{x: 1, y: 11},
			]}
		]

		grp = new THREE.Object3D()
		scene.add grp

		render_objects = (objects) ->
			scene.remove grp
			grp = new THREE.Object3D()
			scene.add grp
			for object in objects.objects
				geo = new THREE.Geometry()
				contour = object.contour
				shape = new THREE.Shape()
				for c in contour
					geo.vertices.push(new THREE.Vector3(-c.y, 0, -c.x))

				mesh = new THREE.Line(
					geo,
					(new THREE.LineBasicMaterial color: 0xff0000)
				)
				grp.add mesh
			#test = new THREE.Mesh(
			#	(new THREE.BoxGeometry 1, 1, 1),
			#	(new THREE.MeshBasicMaterial color: 0xff0000)
			#	)
			#test.position.z = -10
			#grp.add test
		#render_objects objects
		console.log "Hooking stream"
		@stream (objs) ->
			render_objects objs[1]
		render = ->
			renderer.render scene, camera
			requestAnimationFrame render
		render()



</script>
