// =============================================================================
function add_to_blacklist(agent){
	axios.get('/add_to_blacklist?agent=' + agent)
	.then(function (response) {
		//
	})
	.catch(function (error) {
		// handle error
		console.log(error);
	})
}

function choose_node(d){
	// console.log(d);
	if(d.mac == "00:00:00:00:00:00"){
		type = "Контроллер"
	}
	else{
		type = "Агент"
	}

	let content = '<table border=1 style="">' +
		'<tr><td>Тип</td><td>' + type + '</td></tr>' +
		'<tr><td>mac</td><td>' + d.mac + '</td></tr>' +
		'<tr><td>ip</td><td>' + d.ip + '</td></tr>' +
		'<tr><td>Тики сбоя</td><td>' + d.disable_counter + '/3</td></tr></table>'

	if(d.mac != "00:00:00:00:00:00"){
		axios.get('/is_in_blacklist?agent=' + d.mac)
		.then(function (response) {
			_is_in_blacklist = response['data']
			if(_is_in_blacklist != 'True'){
				content += '<button onclick="add_to_blacklist(\'' + d.mac + '\')">Исключить из кластера</button>'
			}
			let node_control = document.querySelector("#agent-info");
			node_control.innerHTML = content;
		})
		.catch(function (error) {
			// handle error
			console.log(error);
		})
	}
	else{
		let node_control = document.querySelector("#agent-info");
		node_control.innerHTML = content;
	}
}

function render_topology_graph(){
	axios.get('/agents_info')
	.then(function (response) {
		let nodes = response['data'];
		nodes.push({mac: '00:00:00:00:00:00', ip: '0.0.0.0', disable_counter: 0})

		let links = []
		for(let i = 0; i < nodes.length; i++){
			links.push({source: '00:00:00:00:00:00', target: nodes[i]['mac']})
		}

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
		viewBoxHeight = '700';
		nodeWidth = 120;
		nodeHeight = 1.3 * nodeWidth;
		nodeRadius = nodeWidth / 5;
		distance = 10000;

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
				if(d.mac == "00:00:00:00:00:00"){return "/static/images/controller.svg"}
				else{
					if(d.disable_counter < 1){return "/static/images/agent_on.svg"}
					else{return "/static/images/agent_off.svg"}
				}
			})
			.attr("x", 0)
			.attr("y", d=> {
				if (d.mac == "00:00:00:00:00:00") return -0.1*nodeHeight;
				else return -0.2*nodeHeight;
			})
			.attr("width", nodeWidth)
			.attr("height", nodeHeight);

		// ip
		node.append("text")
			.text(d => {
				if(d.mac != "00:00:00:00:00:00") return d.ip
			})
			.attr("x", 0)
			.attr("y", d => {
				if(d.mac == "00:00:00:00:00:00") return nodeWidth + 20
				else return nodeWidth
			})
			.attr("font-size", "9pt")
			.attr("font-family", "monospace");

		// mac
		node.append("text")
			.text(d => {
				if(d.mac != "00:00:00:00:00:00") return d.mac
				else return 'controller'
			})
			.attr("x", 0)
			.attr("y", nodeWidth + 14)
			.attr("font-size", "9pt")
			.attr("font-family", "monospace");

		node.append("title")
			.attr("x", 0)
			.attr("y", 0)
			.text(d => {
				return "ip: " + d.ip + "\nmac: " + d.mac + "\ndc: " + d.disable_counter
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
	})
	.catch(function (error) {
		console.log(error);
	})
	.then(function () {
		// always executed
	});
};

// =============================================================================
function remove_from_blacklist(agent){
	axios.get('/remove_from_blacklist?agent=' + agent)
	.then(function (response) {
		//
	})
	.catch(function (error) {
		// handle error
		console.log(error);
	})
}

function render_blacklist(){
	axios.get('/blacklist')
	.then(function (response) {
		// handle success
		let _blacklist = response['data'];
		let blacklist = document.querySelector('#blacklist');
		_tmp_table = ''
		_tmp_table = "<table border=1>";
		for(let i = 0; i < _blacklist.length; i++ ){
			_tmp_table += "<tr><td><div class='blocked_agent'>" + _blacklist[i] + "</div></td>" +
				"<td><button onclick=\"remove_from_blacklist('" + _blacklist[i] + "')\">Восстановить</button></td></tr>"
		}
		_tmp_table += "</table>"
		blacklist.innerHTML =_tmp_table
	})
	.catch(function (error) {
		// handle error
		console.log(error);
	})
}

// =============================================================================

function clear_task_table(task){
	let task_info = document.querySelector('#task-info');
	task_info.innerHTML = ''
}

function render_task_table(task){
	axios.get('/task_info?task='+task)
	.then(function (response) {
		let task_info = document.querySelector('#task-info');
		_task_info = response['data'];
		_tmp_task_info = '';
		_tmp_task_info += '<div>task: <b>' + task + '</b></div>';
		_tmp_task_info += '<br><div>agent: <b>' + _task_info['agent'] + '</b></div>';
		_tmp_task_info += '<br><div>command:</div>';
		_tmp_task_info += '<div class="green_on_black">>>> ' + _task_info['callback'] + '('+ _task_info['procedure'] + '(' + _task_info['args'] + '))</div>'
		_tmp_task_info += '<br><div>result:</div>';
		_tmp_task_info += '<div class="green_on_black">' + _task_info['result'] + '</div>'
		task_info.innerHTML = _tmp_task_info;
		//
	})
	.catch(function (error) {
		// handle error
		console.log(error);
	})
	// 
}

function delete_task(task){
	axios.get('/delete_task?task='+task)
	.then(function (response) {
		clear_task_table(task);
	})
	.catch(function (error) {
		// handle error
		console.log(error);
	})
	.then(function () {
		//
	});
};

function render_tasks_table(){
	axios.get('/tasks_info')
	.then(function (response) {
		// handle success
		let _tasks_info = response['data'];
		let _tasks_table = document.querySelector('#tasks-table');
		_tasks_table.innerHTML = ''
		_tmp_tasks_table = '<table border=1 style="position: relative; font-size: 14px">' +
		'<tr><th>Task ID</th><th>Agent</th><th>Procedure</th><th>Params</th><th>Callback</th><th>Status</th><th>Result</th><th></th></tr>'
		for(let i = 0; i < _tasks_info.length; i++){
			_tmp_tasks_table += '<tr onclick="render_task_table(\'' + _tasks_info[i]['task_id'] + '\')"' +
			'id="task-' + _tasks_info[i]['task_id'] + '">' +
			'<td>' + _tasks_info[i]['task_id'] + '</td>' +
			'<td>' + _tasks_info[i]['agent'] + '</td>' +
			'<td>' + _tasks_info[i]['procedure'] + '</td>' +
			'<td>' + String(_tasks_info[i]['args']) + '</td>' +
			'<td>' + _tasks_info[i]['callback'] + '</td>' +
			'<td>' + _tasks_info[i]['status'] + '</td>' +
			'<td>' + _tasks_info[i]['result'] + '</td>' +
			'<td>' + '<button onclick="delete_task(\''+ _tasks_info[i]['task_id'] + '\')">Удалить</button>' + '</td>' +
			'</tr>'
		}
		_tmp_tasks_table += '</table>';
		_tasks_table.innerHTML = _tmp_tasks_table;
	})
	.catch(function (error) {
		// handle error
		console.log(error);
	})
	.then(function () {
		//
	});
};

// =============================================================================

function render_statistic_table(){
	axios.get('/status_statistics')
	.then(function (response) {
		// handle success
		let _statistic_table = response['data'];
		let statistic_table = document.querySelector('#statistic-table');
		statistic_table.innerHTML = 
		'<table border=1 style="margin: 0 auto; position: relative; font-size: 14px">' +
		'<tr><th>Отправлено</th><th>Выполнено</th><th>Ошибка</th></tr>' +
		'<tr><td>' + _statistic_table['sent_to_agent'][10] + '</td>' +
		'<td>' + _statistic_table['done'][10] + '</td>' +
		'<td>' + _statistic_table['error'][10] + '</td></tr>';
	})
	.catch(function (error) {
		// handle error
		console.log(error);
	})
	.then(function () {
		//
	});
}

// =============================================================================



// =============================================================================




function create_viewBox(p_data){

	width = 550;
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

// =============================================================================
// =============================================================================

window.onload = function(){
	render_topology_graph();

	render_blacklist();
	setInterval(render_blacklist, 4000);

	render_statistic_table();
	setInterval(render_statistic_table, 4000);

	render_tasks_table();
	setInterval(render_tasks_table, 4000);

	exmp1 = generate_data1();
	exmp2 = generate_data2();
	exmp3 = generate_data3();
	v_svg = create_viewBox(exmp1);
	// render_statistic_chart(v_svg, update_data(exmp));

	render_statistic_chart1(v_svg, update_data(exmp1));
	render_statistic_chart2(v_svg, update_data(exmp2));
	render_statistic_chart3(v_svg, update_data(exmp3));
	setInterval(function(){
		render_statistic_chart1(v_svg, update_data(exmp1));
		render_statistic_chart2(v_svg, update_data(exmp2));
		render_statistic_chart3(v_svg, update_data(exmp3));
	}, 4000);
}