import uuid
import json
from arpcp import ARPCP, CONFIG

# task_id:
# _<agent_mac>_<uuid.uuid4()>
#
# for example
# _ff:ff:ff:ff:ff:ff_e3c478ac-1613-40a9-a5b3-004a6d7229cf

class Controller:
	@staticmethod
	def _preset():
		ARPCP.redis().flushall()

	@staticmethod
	def find_agents():
		return {
		}

	@staticmethod
	def register_agents(agents):
		_redis = ARPCP.redis()
		for agent, ip in agents.items():
			_redis.set(f"ARPCP:agent:{agent}:ip", ip)
			_redis.set(f"ARPCP:agent:{agent}:disable_counter", json.dumps(0))

	@staticmethod
	def check_for_deletion(agents):
		_redis = ARPCP.redis()
		remaining_agents = agents.copy()
		agents_for_deletion = []
		for agent in agents:
			if _redis.exists(f"ARPCP:agent:{agent}:disable_counter"):
				dc = json.loads(_redis.get(f"ARPCP:agent:{agent}:disable_counter"))
				if dc >= CONFIG["controller"]["max_dc"]:
					remaining_agents.remove(agent)
					agents_for_deletion.append(agent)
				else:
					_redis.set(f"ARPCP:agent:{agent}:disable_counter", json.dumps(dc + 1))
			else:
				remaining_agents.remove(agent)
				agents_for_deletion.append(agent)
		Controller.delete_agents(agents_for_deletion)
		return remaining_agents

	@staticmethod
	def delete_agents(agents):
		_redis = ARPCP.redis()
		for agent in agents:
			if _redis.exists(f"ARPCP:agent:{agent}:ip"):
				_redis.delete(f"ARPCP:agent:{agent}:ip")
			if _redis.exists(f"ARPCP:agent:{agent}:disable_counter"):
				_redis.delete(f"ARPCP:agent:{agent}:disable_counter")

	@staticmethod
	def echo():
		_redis = ARPCP.redis()

		# get agents found on the network
		found_agents = Controller.find_agents()
		fa = set(found_agents.keys())

		# get already known agents
		if _redis.exists("ARPCP:agents"):
			old_agents = json.loads(_redis.get("ARPCP:agents"))
		else:
			old_agents = []
		oa = set(old_agents)

		# get blacklist
		if _redis.exists("ARPCP:agents:blacklist"):
			blacklist = json.loads(_redis.get("ARPCP:agents:blacklist"))
		else:
			blacklist = []
		b = set(blacklist)

		# calculate new agents for cluster (fa - oa - b)
		new_agents = list(fa.difference(oa).difference(b))
		ns = list(set(found_agents.keys()).difference(set(new_agents)))
		for n in ns:
			del found_agents[n]
		Controller.register_agents(found_agents)

		# calculate old active agents (fa*oa - b)
		old_active_agents = list(fa.intersection(oa).difference(b))

		# calculate old inactive agents (oa - fa - b)
		old_inactive_agents = list(oa.difference(fa).difference(b))
		old_inactive_agents = Controller.check_for_deletion(old_inactive_agents)

		# calculate excluded agents ( (fa + oa) * b)
		excluded_agents = list(fa.union(oa).intersection(b))
		excluded_agents = Controller.check_for_deletion(excluded_agents)

		agents = new_agents + old_active_agents + old_inactive_agents + excluded_agents
		_redis.set("ARPCP:agents", json.dumps(agents))

	@staticmethod
	def add_to_blacklist(agent):
		_redis = ARPCP.redis()
		if _redis.exists("ARPCP:agents:blacklist"):
			blacklist = json.loads(_redis.get("ARPCP:agents:blacklist"))
			if not agent in blacklist:
				blacklist.append(agent)
				_redis.set("ARPCP:agents:blacklist", json.dumps(blacklist))
		else:
			_redis.set("ARPCP:agents:blacklist", json.dumps([agent]))

	@staticmethod
	def remove_from_blacklist(agent):
		_redis = ARPCP.redis()
		if _redis.exists("ARPCP:agents:blacklist"):
			blacklist = json.loads(_redis.get("ARPCP:agents:blacklist"))
			if agent in blacklist:
				blacklist.remove(agent)
				_redis.set("ARPCP:agents:blacklist", json.dumps(blacklist))

	@staticmethod
	def agents():
		_redis = ARPCP.redis()
		if _redis.exists("ARPCP:agents"):
			return json.loads(_redis.get("ARPCP:agents"))
		else:
			return []

	@staticmethod
	def agent_info(agent):
		_agent_info = {}
		_redis = ARPCP.redis()
		_agent_info["mac"] = agent

		_agent_info["ip"] = None
		if _redis.exists(f"ARPCP:agent:{agent}:ip"):
			_agent_info["ip"] = _redis.get(f"ARPCP:agent:{agent}:ip")

		_agent_info["disable_counter"] = CONFIG["controller"]["max_dc"]
		if _redis.exists(f"ARPCP:agent:{agent}:disable_counter"):
			_agent_info["disable_counter"] = json.loads(_redis.get(f"ARPCP:agent:{agent}:disable_counter"))

		tasks = []
		if _redis.exists("ARPCP:tasks:assign"):
			tasks = json.loads(_redis.get("ARPCP:tasks:assign"))
		agent_tasks = [task for task in tasks if task.startswith(f"_{agent}_")]
		_agent_info["tasks"] = agent_tasks

		return _agent_info

	@staticmethod
	def agents_info():
		_agents_info = []
		_redis = ARPCP.redis()
		for agent in Controller.agents():
			_agent_info = Controller.agent_info(agent)
			del _agent_info["tasks"]
			_agents_info.append(_agent_info)
		return _agents_info

	@staticmethod
	def blacklist():
		_redis = ARPCP.redis()
		if _redis.exists("ARPCP:agents:blacklist"):
			return json.loads(_redis.get("ARPCP:agents:blacklist"))
		else:
			return []

	@staticmethod
	def procedures():
		try:
			import procedures
			return list(filter(lambda x: not x.startswith("_"), dir(procedures)))
		except:
			return []

	@staticmethod
	def callbacks():
		try:
			import callbacks
			return list(filter(lambda x: not x.startswith("_"), dir(callbacks)))
		except:
			return []

	@staticmethod
	def generate_task_id(agent):
		return f"_{agent}_{uuid.uuid4()}"

	@staticmethod
	def delete_task(task):
		_redis = ARPCP.redis()
		ARPCP.erase_task_from_redis(_redis, task)

	@staticmethod
	def tasks():
		_redis = ARPCP.redis()
		if _redis.exists("ARPCP:tasks:assign"):
			return json.loads(_redis.get("ARPCP:tasks:assign"))
		else:
			return []

	@staticmethod
	def task_info(task):
		_redis = ARPCP.redis()
		_task_info = {}
		_task_info["task_id"] = task
		_task_info["agent"] = task.split("_")[1]

		_task_info["status"] = None
		if _redis.exists(f"ARPCP:task:{task}:status"):
			_task_info["status"] = _redis.get(f"ARPCP:task:{task}:status")

		_task_info["procedure"] = None
		_task_info["args"] = None
		if _redis.exists(f"ARPCP:task:{task}:message"):
			# _message = _redis.get(f"ARPCP:task:{task}:message")
			# print(_message)
			_message = json.loads(_redis.get(f"ARPCP:task:{task}:message"))
			_task_info["procedure"] = _message["remote_procedure"]
			_task_info["args"] = _message["remote_procedure_args"]

		_task_info["callback"] = None
		if _redis.exists(f"ARPCP:task:{task}:callback"):
			_task_info["callback"] = _redis.get(f"ARPCP:task:{task}:callback")

		_task_info["result"] = None
		if _redis.exists(f"ARPCP:task:{task}:result"):
			_task_info["result"] = json.loads(_redis.get(f"ARPCP:task:{task}:result"))

		return _task_info

	@staticmethod
	def tasks_info():
		_tasks_info = []
		for task in Controller.tasks():
			_tasks_info.append(Controller.task_info(task))
		return _tasks_info

	@staticmethod
	def status_statistics():
		status_statistics = {
			"sent_to_agent": 0,
			"done": 0,
			"error": 0
		}
		_redis = ARPCP.redis()
		for task in Controller.tasks():
			_status = ""
			if _redis.exists(f"ARPCP:task:{task}:status"):
				_status = _redis.get(f"ARPCP:task:{task}:status")
				if _status == "sent_to_agent":
					status_statistics["sent_to_agent"] += 1
				elif _status == "done":
					status_statistics["done"] += 1
				elif _status.endswith("error"):
					status_statistics["error"] += 1
				else:
					pass
		return status_statistics

	@staticmethod
	def rpc(agents, procedure, params, callback=None, async_proc=True):
		_redis = ARPCP.redis()
		_responses = []
		for agent in agents:
			if json.loads(_redis.get(f"ARPCP:agent:{agent}:disable_counter")) == 0:
				_ip = _redis.get(f"ARPCP:agent:{agent}:ip")
				_method = "atask"
				if not async_proc:
					_method = "task"
				_task_id = Controller.generate_task_id(agent)
				_additions = {}
				if callback:
					_additions["callback"] = callback
				print(f"ip: {_ip}")
				print(f"method: {_method}")
				print(f"task_id: {_task_id}")
				print(f"additions: {_additions}")
				_response = ARPCP.call(_ip, CONFIG["server"]["port"], _method, {
					"remote_procedure": procedure,
					"remote_procedure_args": params,
					"task_id": _task_id
				}, _additions)
				_responses.append(_response)
		return _responses


if __name__ == "__main__":
	# Controller._preset()

	# Controller.echo()
	# print(Controller.agents_info())
	# Controller.add_to_blacklist("00:28:f8:20:5e:63")
	# Controller.echo()
	# print(Controller.agents_info())
	# result = Controller.rpc(Controller.agents(), "multiple", [2, 3], "double")
	# print(result)

	for task in Controller.tasks():
		Controller.delete_task(task)
	# print(Controller.tasks_info())
	# print(Controller.agents_info())