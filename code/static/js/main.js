let old_nodes = [];

let proc_desrcs = {
	'add': 'сложение двух чисел',
	'sub': 'вычитание двух чисел',
	'multiple': 'умножение двух чисел',
	'divide': 'деление двух чисел',
	'bash': 'выполнение команды интерпретатора bash',
	'reboot': 'перезагрузить компьютер',
	'get_time': 'получить локальное время компьютера',
	'set_time': 'установить локальное время компьютера (ЧЧ:ММ:СС)',
	'long_task': 'долговыполняющаяся задача (15 секунд)',
	'memory_usage': 'информация о состоянии памяти',
	'running_processes': 'количество запущенных процессов'
}

let old_agents_for_rpc = [];

// =============================================================================

function rpc_controls_table_agents_update(){
	axios.get('/agents_info')
	.then(function (response) {
		let agents_for_rpc = response['data'];
		if(JSON.stringify(agents_for_rpc) == JSON.stringify(old_agents_for_rpc)){
			return;
		}
		old_agents_for_rpc = agents_for_rpc;
		let agents_select = document.querySelector('#rpc-controls-table_agents');
		agents_select.innerHTML = '';
		for(let i = 0; i < agents_for_rpc.length; i++){
			if(agents_for_rpc[i]['disable_counter'] == 0){
				let tmpOption = new Option(agents_for_rpc[i]['mac'], agents_for_rpc[i]['mac']);
				agents_select.options.add(tmpOption);
			}
		}
	})
	.catch(function (error) {
		// handle error
		console.log(error);
	});
}

function rpc_controls_table_procedures_update(){
	axios.get('/procedures')
	.then(function (response) {
		let procedures_select = document.querySelector('#rpc-controls-table_procedures');
		let procedures = response['data'];
		for(let i = 0; i < procedures.length; i++){
			let tmpOption = '<option value="' + procedures[i] + '" ';
			if(procedures[i] in proc_desrcs){
				tmpOption += 'title="' + proc_desrcs[procedures[i]] + '"'
			}
			tmpOption += '>' + procedures[i] + '</option>'
			// let tmpOption = new Option(procedures[i], procedures[i]);
			// procedures_select.options.add(tmpOption);
			procedures_select.innerHTML += tmpOption;
		}
	})
	.catch(function (error) {
		// handle error
		console.log(error);
	});
}

function rpc_controls_table_callbacks_update(){
	axios.get('/callbacks')
	.then(function (response) {
		let callbacks_select = document.querySelector('#rpc-controls-table_callbacks');
		let callbacks = response['data'];
		for(let i = 0; i < callbacks.length; i++){
			let tmpOption = new Option(callbacks[i], callbacks[i]);
			callbacks_select.options.add(tmpOption);
		}
	})
	.catch(function (error) {
		// handle error
		console.log(error);
	});
}

function rpc_controls_table_update(){
	rpc_controls_table_agents_update();
	setInterval(function(){
		rpc_controls_table_agents_update();
	}, 3000);
	rpc_controls_table_procedures_update();
	rpc_controls_table_callbacks_update();
}

function submit_task(){
	let selected_agents = document.querySelector('#rpc-controls-table_agents').getElementsByTagName('option');
	selected_agents_list = [];
	for (var i = 0; i < selected_agents.length; i++) {
		if(selected_agents[i].selected == true){
			selected_agents_list.push(selected_agents[i].value);
		}
	}

	let selected_procedure = document.querySelector('#rpc-controls-table_procedures').value;
	let selected_procedure_args = document.querySelector('#rpc-controls-table_procedure-args').value;
	let selected_callback = document.querySelector('#rpc-controls-table_callbacks').value;
	let is_async = document.querySelector('#rpc-controls-table_async').checked;

	axios.post('/rpc', {
		agents: selected_agents_list,
		procedure: selected_procedure,
		args: selected_procedure_args,
		callback: selected_callback,
		is_async: is_async
	})
	.then(function (response) {
		//
	})
	.catch(function (error) {
		// handle error
		console.log(error);
	})
}

// =============================================================================
function add_to_blacklist(agent){
	axios.get('/add_to_blacklist?agent=' + agent)
	.then(function (response) {
		let button = document.querySelector("#add_to_blacklist_button");
		button.disabled = true;
	})
	.catch(function (error) {
		// handle error
		console.log(error);
	})
}

function choose_node(d){
	if(d.mac == "00:00:00:00:00:00"){
		type = "Контроллер"
	}
	else{
		type = "Агент"
	}

	let content = '<table class="table table-striped" border=1 style="">' +
		'<tr><td>Тип</td><td><b>' + type + '</b></td></tr>' +
		'<tr><td>mac</td><td><b>' + d.mac + '</b></td></tr>' +
		'<tr><td>ip</td><td><b>' + d.ip + '</b></td></tr>' +
		'<tr><td>Тики сбоя</td><td><b>' + d.disable_counter + ' из 3</b></td></tr></table>';


	if(d.mac != "00:00:00:00:00:00"){
		axios.get('/agent_info?agent=' + d.mac)
		.then(function (response) {
			let tasks = response['data']['tasks'];

			axios.get('/is_in_blacklist?agent=' + d.mac)
			.then(function (response) {
				_is_in_blacklist = response['data']
				if(_is_in_blacklist != 'True'){
					content += '<button class="btn btn-danger" id="add_to_blacklist_button" onclick="add_to_blacklist(\'' + d.mac + '\')">Исключить из кластера</button>'
				}

				content += '<table class="table table-striped" border=1 style="margin-top:8px;">'
				content += '<tr class="thead-dark"><th>Задачи (' + tasks.length + ')</th></tr>'
				for(let i = 0; i < tasks.length; i++){
					content += '<tr onclick="render_task_table(\'' + tasks[i] + 
					'\')"><td><p class="task_id">' + tasks[i] + '</p></td></tr>';
				}
				content += '</table>';

				let node_control = document.querySelector("#agent-info");
				node_control.innerHTML = content;
			})
			.catch(function (error) {
				// handle error
				console.log(error);
			})
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

function nodes_lists_comparator(nodes1, nodes2){
	if(nodes1.length == nodes2.length){
		for(let i = 0; i < nodes1.length; i++){
			if(nodes1[i]['mac'] != nodes2[i]['mac']) return false;
			if(nodes1[i]['disable_counter'] != nodes2[i]['disable_counter']) return false;
			if(nodes1[i]['ip'] != nodes2[i]['ip']) return false;
		}
		return true;
	}
	else{
		return false;
	}
}

function render_topology_graph(){
	axios.get('/agents_info')
	.then(function (response) {
		let nodes = response['data'];
		if(nodes_lists_comparator(nodes, old_nodes)){
			return;
		}
		document.querySelector('#topology-graph').innerHTML = '';
		old_nodes = nodes.slice();
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

		viewBoxWidth = '800';
		viewBoxHeight = '500';
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
			.attr("width", nodeWidth + 50)
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
			.attr("font-size", "14px")
			.attr("font-family", "monospace");

		// mac
		node.append("text")
			.text(d => {
				if(d.mac != "00:00:00:00:00:00") return d.mac
				else return 'controller'
			})
			.attr("x", 0)
			.attr("y", nodeWidth + 20)
			.attr("font-size", "14px")
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
		_tmp_table = "<table class='table' border=1>";
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
		_tmp_task_info = '<table class="table table-striped" border=1>';
		_tmp_task_info += '<tr><td>Идентификатор</td><td><span style="font-family:monospace; font-size:12px;"><b>' + task + '</b></span></td></tr>';
		_tmp_task_info += '<tr><td>Назначена агенту</td><td><span style="font-family:monospace; font-size:16px;"><b>' + _task_info['agent'] + '</b></span></td></tr>';
		_tmp_task_info += '<tr><td>Статус</td><td><span style="font-family:monospace; font-size:16px;"><b>' + _task_info['status'] + '</b></span></td></tr>';
		_tmp_task_info += '</table>'
		_tmp_task_info += '<div>Инструкция:</div>';
		_tmp_task_info += '<div class="green_on_black_cmd">>>> ' 
		if(_task_info['callback']){
			_tmp_task_info += _task_info['callback'] + '(';
		}
		_tmp_task_info += _task_info['procedure'] + '(' + _task_info['args'] + ')';
		if(_task_info['callback']){
			_tmp_task_info += ')';
		}
		_tmp_task_info += '</div>';
		_tmp_task_info += '<div>Результат:</div>';
		_tmp_task_info += '<div><pre class="green_on_black_result">' + _task_info['result'] + '</pre></div>'
		task_info.innerHTML = _tmp_task_info;
		//
	})
	.catch(function (error) {
		// handle error
		console.log(error);
	})
	// 
}

function delete_all_tasks(){
	axios.get('/delete_all_tasks')
	.then(function (response) {
		clear_task_table(task);
	})
	.catch(function (error) {
		// handle error
		console.log(error);
	});
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
		_tmp_tasks_table = '<table class="table table-striped" border=1 style="position: relative; font-size: 14px">' +
		'<tr class="thead-dark"><th>Task ID</th><th>Агент</th><th>Процедура</th><th>Параметры</th><th>Обр.вызов</th><th>Статус</th><th>Результат</th>' +
		'<th><button class="btn" style="color:white;" onclick="delete_all_tasks()">Удалить всё</button></th></tr>'
		for(let i = 0; i < _tasks_info.length; i++){
			_tmp_tasks_table += '<tr onclick="render_task_table(\'' + _tasks_info[i]['task_id'] + '\')"' +
			'id="task-' + _tasks_info[i]['task_id'] + '">' +
			'<td><p class="task_id">' + _tasks_info[i]['task_id'] + '</p></td>' +
			'<td><p class="task_mac">' + _tasks_info[i]['agent'] + '</p></td>' +
			'<td><p class="task_option">' + _tasks_info[i]['procedure'] + '</p></td>' +
			'<td><p class="task_option">' + String(_tasks_info[i]['args']) + '</p></td>' +
			'<td><p class="task_option">' + _tasks_info[i]['callback'] + '</p></td>' +
			'<td><p class="task_option">' + _tasks_info[i]['status'] + '</p></td>' +
			'<td><p class="task_option">' + _tasks_info[i]['result'] + '</p></td>' +
			'<td>' + '<button class="btn" onclick="delete_task(\''+ _tasks_info[i]['task_id'] + '\')">Удалить</button>' + '</td>' +
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
		let _statistic_table = response['data'];
		let statistic_table = document.querySelector('#statistic-table');
		statistic_table.innerHTML = 
		'<table class="table" border=1 style="margin: 0 auto; position: relative; font-size: 14px">' +
		'<tr class="thead-dark"><th>Отправлено</th><th>Выполнено</th><th>Ошибка</th></tr>' +
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


function render_statistics_chart(p_chart){
	axios.get('/status_statistics')
	.then(function (response) {
		let statistics = response['data'];

		let sent_to_agent_statistics = [];
		for(let i = 0; i < statistics['sent_to_agent'].length; i++){
			sent_to_agent_statistics.push({
				step: i,
				value: statistics['sent_to_agent'][i]
			});
		};

		let done_statistics = [];
		for(let i = 0; i < statistics['done'].length; i++){
			done_statistics.push({
				step: i,
				value: statistics['done'][i]
			});
		};

		let error_statistics = [];
		for(let i = 0; i < statistics['error'].length; i++){
			error_statistics.push({
				step: i,
				value: statistics['error'][i]
			});
		};

		render_statistic_chart_for_array(p_chart, sent_to_agent_statistics, "blue");
		render_statistic_chart_for_array(p_chart, done_statistics, "green");
		render_statistic_chart_for_array(p_chart, error_statistics, "red");
	})
	.catch(function (error) {
		// handle error
		console.log(error);
	})
};

function create_viewBox(){
	width = 550;
	height = 400;
	margin = ({top: 20, right: 20, bottom: 30, left: 30});

	line = d3.line()
		.defined(d => !isNaN(d.value))
		.x(d => x(d.step))
		.y(d => y(d.value));


	x = d3.scaleLinear()
		.domain([0, 10])
		.range([margin.left, width - margin.right]);

	y = d3.scaleLinear()
		.domain([0, 30])
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
			.attr("font-weight", "bold"));
			// .text(p_data.y));

	const svg = d3.select('#statistic-chart').append("svg")
		  .attr("viewBox", [0, 0, width, height]);

	  svg.append("g")
		  .call(xAxis);

	  svg.append("g")
		  .call(yAxis);

		 return svg
}

function render_statistic_chart_for_array(p_svg, p_data, p_color){

  var u = p_svg.selectAll("." + p_color)
    .data([p_data], function(d){ return d.value });

  // Updata the line
  u
    .enter()
    .append("path")
    .attr("class", p_color)
    .merge(u)
    .transition()
    .duration(1)
    .attr("d", d3.line()
      .x(function(d) { return x(d.step); })
      .y(function(d) { return y(d.value); }))
      .attr("fill", "none")
      .attr("stroke", p_color)
      .attr("stroke-width", 2.5)
}

function update_data(p_data){
	N = 11;
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
	setInterval(function(){
		render_topology_graph();
	}, 3000);

	render_blacklist();
	setInterval(render_blacklist, 1500);

	render_statistic_table();
	setInterval(render_statistic_table, 1500);

	render_tasks_table();
	setInterval(render_tasks_table, 1500);

	rpc_controls_table_update();

	let statistic_chart = create_viewBox();
	render_statistics_chart(statistic_chart);
	setInterval(function(){
		render_statistics_chart(statistic_chart);
	}, 4000);
}