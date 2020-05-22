import json
import arpcp
from flask import Flask, render_template, jsonify, request

webapp = Flask(
	__name__,
	template_folder = "templates",
	static_folder = "static"
)

@webapp.route('/', methods = ['GET'])
def index():
	# with open('/srv/arpcp/static/index.html') as index:
		# return str(index.read())
	return webapp.send_static_file('index.html')

@webapp.route('/agent_info', methods = ['GET'])
def agent_info():
	_agent = request.args.get('agent')
	if _agent:
		_agent_info = arpcp.Controller.agent_info(_agent)
		if _agent_info:
			return jsonify(_agent_info)
	return '',400

@webapp.route('/agents_info', methods = ['GET'])
def agents_info():
	return jsonify(arpcp.Controller.agents_info())

@webapp.route('/task_info', methods = ['GET'])
def task_info():
	_task = request.args.get('task')
	if _task:
		_task_info = arpcp.Controller.task_info(_task)
		if _task_info:
			return jsonify(_task_info)
	return '',400

@webapp.route('/tasks_info', methods = ['GET'])
def tasks_info():
	return jsonify(arpcp.Controller.tasks_info())

@webapp.route('/delete_task', methods = ['GET'])
def delete_task():
	_task = request.args.get('task')
	if _task:
		arpcp.Controller.delete_task(_task)
		return '',200
	return '',400

@webapp.route('/status_statistics', methods = ['GET'])
def status_statistics():
	_redis = arpcp.ARPCP.redis()
	return jsonify(json.loads(_redis.get("ARPCP:statistic:status")))

@webapp.route('/blacklist', methods = ['GET'])
def blacklist():
	return jsonify(arpcp.Controller.blacklist())

@webapp.route('/procedures', methods = ['GET'])
def procedures():
	return jsonify(arpcp.Controller.procedures())

@webapp.route('/callbacks', methods = ['GET'])
def callbacks():
	return jsonify(arpcp.Controller.callbacks())

@webapp.route('/add_to_blacklist', methods = ['GET'])
def add_to_blacklist():
	_agent = request.args.get('agent')
	if _agent:
		arpcp.Controller.add_to_blacklist(_agent)
		return '',200
	return '',400

@webapp.route('/remove_from_blacklist', methods = ['GET'])
def remove_from_blacklist():
	_agent = request.args.get('agent')
	if _agent:
		arpcp.Controller.remove_from_blacklist(_agent)
		return '',200
	return '',400

@webapp.route('/is_in_blacklist', methods = ['GET'])
def is_in_blacklist():
	_agent = request.args.get('agent')
	if _agent and (_agent in arpcp.Controller.blacklist()):
		return str(True)
	return str(False)

@webapp.route('/rpc', methods = ['POST'])
def rpc():
	pass


if __name__ == '__main__':
	webapp.debug = True
	webapp.run()