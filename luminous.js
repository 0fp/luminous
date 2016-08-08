
commands = {
	'inc': {
		'red':   '%2B.2',
		'green': '%2B.2',
		'blue':  '%2B.2',
	},
	'dec': {
		'red':   '-.2',
		'green': '-.2',
		'blue':  '-.2',
	},
	'play': {'play': 'toggle'},
	'power': {'power': 'toggle'},

	'red': {'red': 'toggle'},
	'green': {'green': 'toggle'},
	'blue': {'blue': 'toggle'},
	'white': {
		'red': 'toggle',
		'green': 'toggle',
		'blue': 'toggle',
	},

	'redInc':   {'red':   '%2B0.05'},
	'redDec':   {'red':   '-.05'},
	'greenInc': {'green': '%2B0.05'},
	'greenDec': {'green': '-.05'},
	'blueInc':  {'blue':  '%2B0.05'},
	'blueDec':  {'blue':  '-.05'},

	'sine': {
		'red': 'sine',
		'green': 'sine',
		'blue': 'sine'
	},

	'freqInc' : {
		'red': 'mF%2B1',
		'green': 'mF%2B1',
		'blue': 'mF%2B1',
	},

	'freqDec' : {
		'red': 'mF-1',
		'green': 'mF-1',
		'blue': 'mF-1',
	},

	'ampInc' : {
		'mod': 'A%2B0.05'
	},

	'ampDec' : {
		'mod': 'A-0.05'
	},

	'sequence': {
		'sequence': 'start'
	}
}

setColor = function(e) {
	var m = e.value
	var data = 'cmd=' + JSON.stringify({
		'red'  : parseInt(m.substr(1,2),16)/255,
		'green': parseInt(m.substr(3,2),16)/255,
		'blue' : parseInt(m.substr(5,2),16)/255
	})
	$.ajax({
		type: 'POST',
		url: "http://192.168.178.15:8007/cgi-bin/luminousd.cgi",
		data: data,
		success: function (data) {}
	});
}

send = function(e) {
	var data = 'cmd=' + JSON.stringify( commands[e.name] )
	$.ajax({
		type: 'POST',
		url: "http://192.168.178.8:8007/cgi-bin/luminousd.cgi",
		data: data,
		success: function (data) {}
	});
}
/*
$(function(){
	$('button').click(alert(this));
})*/
