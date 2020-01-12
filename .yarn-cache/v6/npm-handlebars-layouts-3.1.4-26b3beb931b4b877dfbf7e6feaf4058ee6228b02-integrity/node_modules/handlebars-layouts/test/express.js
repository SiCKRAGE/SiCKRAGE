'use strict';

var handlebarsLayouts = require('../index'),
	consolidate = require('consolidate'),
	express = require('express'),
	handlebars = require('handlebars'),
	fs = require('fs'),
	path = require('path'),
	data = require('./fixtures/data/users.json'),
	fixtures = path.join(process.cwd(), 'fixtures'),
	views = path.join(fixtures, 'templates'),
	partials = path.join(fixtures, 'partials');

function read(file) {
	return fs.readFileSync(path.join(partials, file), 'utf8');
}

// Register helpers
handlebarsLayouts.register(handlebars);

// Register partials
handlebars.registerPartial({
	layout: read('layout.hbs'),
	layout2col: read('layout2col.hbs'),
	media: read('media.hbs'),
	user: read('user.hbs')
});

// Server
express()
	// Settings
	.set('views', views)
	.set('view engine', 'html')

	// Engines
	.engine('html', consolidate.handlebars)

	// Routes
	.get('/:id', function (req, res) {
		res.render(req.params.id, data);
	})

	// Start
	.listen(3000);

console.log('Express server listening on port 3000');
