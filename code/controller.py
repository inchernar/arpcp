import json
from arpcp import ARPCP, CONFIG

class Controller:
	@staticmethod
	def _preset():
		ARPCP.redis().flushall()

	@staticmethod
	def find_agents():
		return {
			'agent001': 'IP_agent001',
			'agent002': 'IP_agent002',
			'agent003': 'IP_agent003'
		}

	@staticmethod
	def register_agents(agents):
		_redis = ARPCP.redis()
		for agent, ip in agents.items():
			_redis.set(f'ARPCP:agent:{agent}:ip', ip)
			_redis.set(f'ARPCP:agent:{agent}:disable_counter', json.dumps(0))

	@staticmethod
	def check_for_deletion(agents):
		_redis = ARPCP.redis()
		remaining_agents = agents.copy()
		agents_for_deletion = []
		for agent in agents:
			dc = json.loads(_redis.get(f'ARPCP:agent:{agent}:disable_counter'))
			if dc >= CONFIG['controller']['max_dc']:
				remaining_agents.remove(agent)
				agents_for_deletion.append(agent)
			else:
				_redis.set(f'ARPCP:agent:{agent}:disable_counter', json.dumps(dc + 1))
		Controller.delete_agents(agents_for_deletion)
		return remaining_agents

	@staticmethod
	def delete_agents(agents):
		_redis = ARPCP.redis()
		for agent in agents:
			_redis.delete(f'ARPCP:agent:{agent}:ip')
			_redis.delete(f'ARPCP:agent:{agent}:disable_counter')

	@staticmethod
	def echo():
		_redis = ARPCP.redis()

		# get agents found on the network
		found_agents = Controller.find_agents()
		fa = set(found_agents.keys())

		# get already known agents
		if _redis.exists('ARPCP:agents'):
			old_agents = json.loads(_redis.get('ARPCP:agents'))
		else:
			old_agents = []
		oa = set(old_agents)

		# get blacklist
		if _redis.exists('ARPCP:agents:blacklist'):
			blacklist = json.loads(_redis.get('ARPCP:agents:blacklist'))
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
		_redis.set('ARPCP:agents', json.dumps(agents))

	@staticmethod
	def add_to_blacklist(agent):
		_redis = ARPCP.redis()
		if _redis.exists('ARPCP:agents:blacklist'):
			blacklist = json.loads(_redis.get('ARPCP:agents:blacklist'))
			if not agent in blacklist:
				blacklist.append(agent)
				_redis.set('ARPCP:agents:blacklist', json.dumps(blacklist))
		else:
			_redis.set('ARPCP:agents:blacklist', json.dumps([agent]))

	@staticmethod
	def remove_from_blacklist(agent):
		_redis = ARPCP.redis()
		if _redis.exists('ARPCP:agents:blacklist'):
			blacklist = json.loads(_redis.get('ARPCP:agents:blacklist'))
			if agent in blacklist:
				blacklist.remove(agent)
				_redis.set('ARPCP:agents:blacklist', json.dumps(blacklist))

	@staticmethod
	def agents_info():
		_agents_info = []
		_redis = ARPCP.redis()
		if _redis.exists('ARPCP:agents'):
			agents = json.loads(_redis.get('ARPCP:agents'))
			for agent in agents:
				_agent_info = {}
				_agent_info['mac'] = agent
				_agent_info['ip'] = _redis.get(f'ARPCP:agent:{agent}:ip')
				_agent_info['disable_counter'] = json.loads(_redis.get(f'ARPCP:agent:{agent}:disable_counter'))
				_agents_info.append(_agent_info)
		return _agents_info

	@staticmethod
	def status_statistics():
		_status_statistics = []
		_redis = ARPCP.redis()
		# action

if __name__ == '__main__':
	Controller._preset()

	print(Controller.agents_info())
	Controller.echo()
	print(Controller.agents_info())
	Controller.add_to_blacklist('agent002')
	Controller.echo()
	print(Controller.agents_info())
	Controller.echo()
	print(Controller.agents_info())
