(function ($) {
	var jsav = new JSAV("av"),
		arr,
		g,
		lambda = String.fromCharCode(955),
		epsilon = String.fromCharCode(949);

	var initialize = function() {
		g = localStorage['graph'];
		if (!g) {
			jsav.umsg("Error!");
			return;
		}
		var traversal = localStorage['traversal'];
		var runFunction = initGraph({layout: "automatic"});
		$('.jsavcontrols').show();
		if (traversal != lambda && traversal != epsilon) {
			runFunction(traversal);
		}
		else {
			runFunction("")
		}
	};
	
	var initGraph = function(opts) {
		var gg = jQuery.parseJSON(g);
		var graph = jsav.ds.fa($.extend({width: '90%', height: 440}, opts));
		for (var i = 0; i < gg.nodes.length; i++) {
	    	var node = graph.addNode('q' + i),
	    		offset = $('.jsavgraph').offset(),
	    		offset2 = parseInt($('.jsavgraph').css('border-width'), 10);
	    	$(node.element).offset({top : parseInt(gg.nodes[i].top) + offset.top + offset2, left: parseInt(gg.nodes[i].left) + offset.left + offset2});
	    	if (gg.nodes[i].i) {
	    		graph.makeInitial(node);
	    	}
	    	if (gg.nodes[i].f) {
	    		node.addClass("final");
	    	}
	    	node.stateLabel(gg.nodes[i].stateLabel);
	    	node.stateLabelPositionUpdate();
	  	}
	  	for (var i = 0; i < gg.edges.length; i++) {
	    	if (gg.edges[i].weight !== undefined) {
	    		var w = delambdafy(gg.edges[i].weight);
	    		var edge = graph.addEdge(graph.nodes()[gg.edges[i].start], graph.nodes()[gg.edges[i].end], {weight: w});
        	}
	    	else {
	    		var edge = graph.addEdge(graph.nodes()[gg.edges[i].start], graph.nodes()[gg.edges[i].end]);
	    	}
	    	edge.layout();
	    }
	    g = graph;
	    if (gg.shorthand) {
	    	return runShorthand;
	    }
	    return run;
    };

    function delambdafy(weight) {
    	var weights = weight.split("<br>");
		for (var i = 0; i < weights.length; i++) {
			var symbols = weights[i].split(":");
			for (var j = 0; j < symbols.length; j++) {
				if (symbols[j] == "&lambda;") {
					symbols[j] = lambda;
				}
				else if (symbols[j] == "&epsilon;") {
					symbols[j] = epsilon;
				}
			}
			weights[i] = symbols.join(":");
		}
		return weights.join("<br>");
    };

	var run = function(inputString) {
		var textArray = [];
		g.initial.addClass('current');
		var currentStates = [g.initial];
		currentStates = addLambdaClosure(g, currentStates);
		var nextStates = currentStates;
		
		for (var i = 0; i < inputString.length; i++) {
			textArray.push(inputString[i]);
		}
		arr = jsav.ds.array(textArray, {element: $('.arrayPlace')});

		jsav.displayInit();

		var failingIndex = inputString.length - 1;
		var finalIndex = inputString.length - 1;
		if (!inputString) {
			finalIndex = 0;
		}

		for (var i = 0; i < inputString.length; i++) {
			for (var j = 0; j < currentStates.length; j++) {
		   		currentStates[j].removeClass('current');
		   	}
		   	nextStates = traverse(g, currentStates, inputString[i]);
		   	if (nextStates.length == 0) {
		   		for (var k = 0; k < currentStates.length; k++) {
		   			currentStates[k].addClass('rejected');
		   		}
		   		arr.css(i, {"background-color": "red"});
		   		failingIndex = i;
		   		jsav.step();
		   		break;
		   	}
			currentStates = nextStates;
			arr.css(i, {"background-color": "yellow"});
			jsav.step();
		}

		var rejected = true;
		for (var k = 0; k < currentStates.length; k++) {
			if (currentStates[k].hasClass('final') && nextStates.length > 0) {
				currentStates[k].addClass('accepted');
				arr.css(finalIndex, {"background-color": "green"});
				jsav.umsg("Accepted");
				rejected = false;
			}
		}
		if (rejected) {
			for (var l = failingIndex; l < inputString.length - 1; l++) {
				arr.css(l, {"background-color": "red"});
			}
			arr.css(finalIndex, {"background-color": "red"});
			jsav.umsg("Rejected");
		}
		var nodes = g.nodes();
		for (var next = nodes.next(); next; next = nodes.next()) {
			if (next.hasClass('current') && rejected) {
				next.addClass('rejected');
			}
			next.removeClass('current');
		}
		jsav.step();
		jsav.recorded();

		arr.click(arrayClickHandler);
	};

	var runShorthand = function(inputString) {
		var textArray = [];
		g.initial.addClass('current');
		var currentStates = [g.initial];
		currentStates = addLambdaClosure(g, currentStates);
		var currentEdges = [];
		var edgeWeight = [];
		var edgeProgress = [];
		var nextStates = currentStates;
		var nextEdges = currentEdges;
		
		for (var i = 0; i < inputString.length; i++) {
			textArray.push(inputString[i]);
		}
		arr = jsav.ds.array(textArray, {element: $('.arrayPlace')});

		jsav.displayInit();

		var failingIndex = inputString.length - 1;
		var finalIndex = inputString.length - 1;
		if (!inputString) {
			finalIndex = 0;
		}

		for (var i = 0; i < inputString.length; i++) {
			for (var j = 0; j < currentStates.length; j++) {
		   		currentStates[j].removeClass('current');
		   	}
		   	var traverseStep = traverseShorthand(g, currentStates, currentEdges, edgeWeight, edgeProgress, inputString[i]);
	   		nextStates = traverseStep[0];
	   		nextEdges = traverseStep[1];
		   	if (nextStates.length == 0 && nextEdges.length == 0) {
		   		for (var k = 0; k < currentStates.length; k++) {
		   			currentStates[k].addClass('rejected');
		   		}
		   		arr.css(i, {"background-color": "red"});
		   		failingIndex = i;
		   		jsav.step();
		   		break;
		   	}
			currentStates = nextStates;
			currentEdges = nextEdges;
			edgeWeight = traverseStep[2];
			edgeProgress = traverseStep[3];
			arr.css(i, {"background-color": "yellow"});
			jsav.step();
		}

		var rejected = true;
		for (var k = 0; k < currentStates.length; k++) {
			if (currentStates[k].hasClass('final') && nextStates.length > 0) {
				currentStates[k].addClass('accepted');
				arr.css(finalIndex, {"background-color": "green"});
				jsav.umsg("Accepted");
				rejected = false;
			}
		}
		if (rejected) {
			for (var l = failingIndex; l < inputString.length - 1; l++) {
				arr.css(l, {"background-color": "red"});
			}
			arr.css(finalIndex, {"background-color": "red"});
			jsav.umsg("Rejected");
		}
		var nodes = g.nodes();
		for (var next = nodes.next(); next; next = nodes.next()) {
			if (next.hasClass('current') && rejected) {
				next.addClass('rejected');
			}
			next.removeClass('current');
		}
		var edges = g.edges();
		for (var next = edges.next(); next; next = edges.next()) {
			next.removeClass('edgeSelect');
		   	var w = next.weight().split("<b>");
		   	var unbold = w.join("");
		   	w = unbold.split("</b>");
		   	unbold = w.join("");
		   	next.weight(unbold);
		}
		jsav.step();
		jsav.recorded();

		arr.click(arrayClickHandler);
	};

	function arrayClickHandler(index) {
		var oldFx = $.fx.off || false;
    	$.fx.off = true;
    	if (index > jsav.currentStep() - 1) {
    		while (index > jsav.currentStep() - 1 && jsav._redo.length) {
				jsav.forward();
			}
    	}
    	if (index < jsav.currentStep() - 1) {
    		while (index < jsav.currentStep() - 1 && jsav._undo.length) {
				jsav.backward();
			}
    	}
		$.fx.off = oldFx;
	};

	initialize();
}(jQuery));