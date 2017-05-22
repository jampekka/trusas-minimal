baseapp = require 'trusas-server/ui/ui.coffee'

do ->
	# Very bad hackery
	Vue = baseapp.Vue
	app = await baseapp()
	Vue.component 'trusas-visualizations', require('./ui.vue')
	Vue.component 'trusas-laserview', require './laserview.vue'
	app = new Vue app
	app.$mount "#container"
