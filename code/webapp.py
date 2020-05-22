import json
import arpcp
from flask import Flask, render_template, jsonify

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

# @webapp.route('/agent_info', methods = ['GET'])
# def agent_info():
# 	return jsonify(arpcp.Controller.agent_info())

@webapp.route('/agents_info', methods = ['GET'])
def agents_info():
	return jsonify(arpcp.Controller.agents_info())

# @webapp.route('/task_info', methods = ['GET'])
# def task_info():
# 	return jsonify(arpcp.Controller.task_info())

@webapp.route('/tasks_info', methods = ['GET'])
def tasks_info():
	return jsonify(arpcp.Controller.tasks_info())

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

if __name__ == '__main__':
	webapp.debug = True
	webapp.run()