function choose_node(d){
	console.log(d);
	let content = "mac: " + d.mac + "\nip: " + d.ip + "\n";
	if(d.controller){
		content += "CONTROLLER"
	}
	else{
		content += "AGENT"
	}
	let node_control = document.querySelector("#node-controls");
	node_control.innerText = content;
}

function render_topology_graph(){
	drag = simulation => {
	function dragstarted(d) {
		if (!d3.event.active) simulation.alphaTarget(0.3).restart();
		d.fx = d.x;
		d.fy = d.y;
	}
	function dragged(d) {
		d.fx = d3.event.x;
		d.fy = d3.event.y;
	}
	function dragended(d) {
		if (!d3.event.active) simulation.alphaTarget(0);
		d.fx = null;
		d.fy = null;
	}
	return d3.drag()
		.on("start", dragstarted)
		.on("drag", dragged)
		.on("end", dragended);
	}

	viewBoxWidth = '1200';
	viewBoxHeight = '750';
	nodeWidth = 120;
	nodeHeight = 1.3 * nodeWidth;
	nodeRadius = nodeWidth / 5;
	distance = 10000;

	const links = [
		{source: '8c:16:45:4d:23:bc', target: '8c:00:00:00:00:01'},
		{source: '8c:16:45:4d:23:bc', target: '8c:00:00:00:00:02'},
		{source: '8c:16:45:4d:23:bc', target: '8c:00:00:00:00:03'},
		{source: '8c:16:45:4d:23:bc', target: '8c:00:00:00:00:04'},
		{source: '8c:16:45:4d:23:bc', target: '8c:00:00:00:00:05'},
		{source: '8c:16:45:4d:23:bc', target: '8c:00:00:00:00:06'},
		{source: '8c:16:45:4d:23:bc', target: '8c:00:00:00:00:07'}
	];
	const nodes = [
		{mac: '8c:16:45:4d:23:bc', ip: '192.168.1.10', on: true, controller: true},
		{mac: '8c:00:00:00:00:01', ip: '192.168.1.101', on: true, controller: false},
		{mac: '8c:00:00:00:00:02', ip: '192.168.1.102', on: true, controller: false},
		{mac: '8c:00:00:00:00:03', ip: '192.168.1.103', on: false, controller: false},
		{mac: '8c:00:00:00:00:04', ip: '192.168.1.104', on: true, controller: false},
		{mac: '8c:00:00:00:00:05', ip: '192.168.1.104', on: false, controller: false},
		{mac: '8c:00:00:00:00:06', ip: '192.168.1.104', on: true, controller: false},
		{mac: '8c:00:00:00:00:07', ip: '192.168.1.104', on: false, controller: false}
	];

	const simulation = d3.forceSimulation(nodes)
		.force("link", d3.forceLink(links).id(d => d.mac))
		.force("charge", d3.forceManyBody().strength(-distance))
		.force("center", d3.forceCenter(viewBoxWidth / 2, viewBoxHeight / 2));

	const graph = d3.select('#topology-graph');

	const svg = graph.append("svg")
		.attr("viewBox", [0, 0, viewBoxWidth, viewBoxHeight]);

	const link = svg.append("g")
		.attr("stroke", "rgb(30, 30, 180)")
		.attr("stroke-opacity", 0.3)
		.attr("stroke-dasharray", "10 10")
		.attr("stroke-width", "2")
	.selectAll("line")
	.data(links)
	.join("line");

	const node = svg.append("g")
	.selectAll("g")
	.data(nodes)
	.join("svg")
		.attr("width", nodeWidth)
		.attr("height", nodeHeight)
		.on("click", d => choose_node(d))
		.call(drag(simulation));

	node.append("svg:image")
		.attr("xlink:href", function(d){
			if(d.controller){return "images/controller.svg"}
			else{
				if(d.on){return "images/agent_on.svg"}
				else{return "images/agent_off.svg"}
			}
		})
		.attr("x", 0)
		.attr("y", d=> {
			if (d.controller) return -0.1*nodeHeight;
			else return -0.2*nodeHeight;
		})
		.attr("width", nodeWidth)
		.attr("height", nodeHeight);

	node.append("text")
		.text(d => d.ip)
		.attr("x", 0)
		.attr("y", d => {
			if(d.controller) return nodeWidth + 20
			else return nodeWidth
		})
		.attr("font-size", "9pt")
		.attr("font-family", "monospace");

	node.append("text")
		.text(d => {
			if(!d.controller) return d.mac
		})
		.attr("x", 0)
		.attr("y", nodeWidth + 14)
		.attr("font-size", "9pt")
		.attr("font-family", "monospace");

	node.append("title")
		.attr("x", 0)
		.attr("y", 0)
		.text(d => {
			return "mac: " + d.mac + "\nip: " + d.ip
		})
		.attr("fill", "black")
		.attr("stroke", "black")
		.attr("stroke-width", 3);

	simulation.on("tick", () => {
	link
		.attr("x1", d => d.source.x)
		.attr("y1", d => d.source.y)
		.attr("x2", d => d.target.x)
		.attr("y2", d => d.target.y);

	node
		.attr("x", d => d.x - nodeWidth / 2)
		.attr("y", d => d.y - nodeHeight / 2);
	});

	// simulation.stop();

	// return svg.node();
}

function create_viewBox(p_data){

	width = 600;
	height = 400;
	margin = ({top: 20, right: 20, bottom: 30, left: 30});

	line = d3.line()
		.defined(d => !isNaN(d.value))
		.x(d => x(d.step))
		.y(d => y(d.value));


	x = d3.scaleLinear()
		.domain([0, 100])
		.range([margin.left, width - margin.right]);

	y = d3.scaleLinear()
		.domain([0, 300])
		.range([height - margin.bottom, margin.top]);

	xAxis = g => g
		.attr("transform", `translate(0,${height - margin.bottom})`)
		.call(d3.axisBottom(x).ticks(width / 80).tickSizeOuter(0));

	yAxis = g => g
		.attr("transform", `translate(${margin.left},0)`)
		.call(d3.axisLeft(y))
		.call(g => g.select(".domain").remove())
		.call(g => g.select(".tick:last-of-type text").clone()
			.attr("x", 3)
			.attr("text-anchor", "start")
			.attr("font-weight", "bold")
			.text(p_data.y));



	const svg = d3.select('#statistic-chart').append("svg")
		  .attr("viewBox", [0, 0, width, height]);

	  svg.append("g")
		  .call(xAxis);

	  svg.append("g")
		  .call(yAxis);

		 return svg
}

function render_statistic_chart1(p_svg, p_data){

  var u = p_svg.selectAll(".lineTest1")
    .data([p_data], function(d){ return d.value });

  // Updata the line
  u
    .enter()
    .append("path")
    .attr("class","lineTest1")
    .merge(u)
    .transition()
    .duration(1)
    .attr("d", d3.line()
      .x(function(d) { return x(d.step); })
      .y(function(d) { return y(d.value); }))
      .attr("fill", "none")
      .attr("stroke", "steelblue")
      .attr("stroke-width", 2.5)
}

function render_statistic_chart2(p_svg, p_data){

  var u = p_svg.selectAll(".lineTest2")
    .data([p_data], function(d){ return d.value });

  // Updata the line
  u
    .enter()
    .append("path")
    .attr("class","lineTest2")
    .merge(u)
    .transition()
    .duration(1)
    .attr("d", d3.line()
      .x(function(d) { return x(d.step); })
      .y(function(d) { return y(d.value); }))
      .attr("fill", "none")
      .attr("stroke", "red")
      .attr("stroke-width", 2.5)
}

function render_statistic_chart3(p_svg, p_data){

  var u = p_svg.selectAll(".lineTest3")
    .data([p_data], function(d){ return d.value });

  // Updata the line
  u
    .enter()
    .append("path")
    .attr("class","lineTest3")
    .merge(u)
    .transition()
    .duration(1)
    .attr("d", d3.line()
      .x(function(d) { return x(d.step); })
      .y(function(d) { return y(d.value); }))
      .attr("fill", "none")
      .attr("stroke", "green")
      .attr("stroke-width", 2.5)
}

function generate_data1(){
	N = 100;
	data = []
	for(let i = 0; i < N; i++){
		data.push({
			step: i,
			value: 120
		})
	}
	return data;
}

function generate_data2(){
	N = 100;
	data = []
	for(let i = 0; i < N; i++){
		data.push({
			step: i,
			value: 150
		})
	}
	return data;
}

function generate_data3(){
	N = 100;
	data = []
	for(let i = 0; i < N; i++){
		data.push({
			step: i,
			value: 180
		})
	}
	return data;
}

function update_data(p_data){
	N = 100;
	for(let i = 0; i < (N-1); i++){
		p_data[i] = {
			step: i,
			value: p_data[i+1]['value']
		};
	}
	p_data[N-1] = {
		step: (N-1),
		value: p_data[N-1]['value'] + (Math.floor(Math.random() * Math.floor(20)) - 10)
	}
	return p_data;
}


window.onload = function(){
	render_topology_graph();
	exmp1 = generate_data1();
	exmp2 = generate_data2();
	exmp3 = generate_data3();
	v_svg = create_viewBox(exmp1);
	// render_statistic_chart(v_svg, update_data(exmp));

	setInterval(function(){
		render_statistic_chart1(v_svg, update_data(exmp1));
		render_statistic_chart2(v_svg, update_data(exmp2));
		render_statistic_chart3(v_svg, update_data(exmp3));
	}, 2000);
}