import uuid
import time
import json
import arpcp
import redis
import pytest

class TestARPCP:
	# def _clear_redis(self, task_id):
	# 	self.redis.delete(f'ARPCP:task:{task_id}:result')
	# 	self.redis.delete(f'ARPCP:task:{task_id}:status')
	# 	self.redis.delete(f'ARPCP:task:{task_id}:message')
	# 	self.redis.delete(f'ARPCP:task:{task_id}:caller_ip')
	# 	self.redis.delete(f'ARPCP:task:{task_id}:host_addr')
	# 	self.redis.delete(f'ARPCP:task:{task_id}:callback')

	# 	if self.redis.exists('ARPCP:tasks:assign'):
	# 		assigned_tasks = json.loads(self.redis.get('ARPCP:tasks:assign'))
	# 		if task_id in assigned_tasks:
	# 			assigned_tasks.remove(task_id)
	# 			self.redis.set('ARPCP:tasks:assign', json.dumps(assigned_tasks))

	# 	if self.redis.exists('ARPCP:tasks:execute'):
	# 		executed_tasks = json.loads(self.redis.get('ARPCP:tasks:execute'))
	# 		if task_id in executed_tasks:
	# 			executed_tasks.remove(task_id)
	# 			self.redis.set('ARPCP:tasks:execute', json.dumps(executed_tasks))

	# @pytest.fixture(autouse = True)
	def setup_class(self):
		self.host = '127.0.0.1'
		self.port = 7018
		self.redis = redis.Redis(host = '127.0.0.1', port = 6379, decode_responses = True)


	# def teardown_class(self):
	# 	time.sleep(0.5)
	# 	self.redis.flushall()


	def test_call_with_wrong_params(self):
		try:
			arpcp.ARPCP.call(int(), self.port, '')
			assert False
		except:
			assert True
		try:
			arpcp.ARPCP.call(self.host, str(), '')
			assert False
		except:
			assert True
		try:
			arpcp.ARPCP.call(self.host, self.port, int())
			assert False
		except:
			assert True
		try:
			arpcp.ARPCP.call(self.host, self.port, str(), headers = str())
			assert False
		except:
			assert True
		try:
			arpcp.ARPCP.call(self.host, self.port, str(), additions = str())
			assert False
		except:
			assert True


	def test_call_unspecified_method(self):
		method_name = 'unspecified_method'
		expected_response = {
			'code': 401,
			'description': f"method {method_name} is unsupported",
			'data': None
		}
		response = arpcp.ARPCP.call(self.host, self.port, method_name)
		assert response == expected_response


	def test_call_specified_method_wo_handler(self):
		method_name = 'test_method'
		expected_response = {
			'code': 300,
			'description': f"type object 'ARPCP' has no attribute 'handle_{method_name}'",
			'data': None
		}
		response = arpcp.ARPCP.call(self.host, self.port, method_name)
		assert response == expected_response


	def test_id_method(self):
		response = arpcp.ARPCP.call(self.host, self.port, 'id')
		assert response['code'] == 100
		assert response['description'] == 'OK'
		assert type(response['data']) == dict
		assert type(response['data']['agent_mac']) == str


	# def test_id_method_with_extra_headers(self):
	# 	response = arpcp.ARPCP.call(self.host, self.port, 'id', {
	# 		'key1': 'value1',
	# 		'key2': 'value2',
	# 		'callback': 'callback'
	# 	})
	# 	assert response['code'] == 100
	# 	assert response['description'] == 'OK'
	# 	assert type(response['data']) == dict
	# 	assert type(response['data']['agent_mac']) == str


	# def test_id_method_with_extra_additions(self):
	# 	response = arpcp.ARPCP.call(self.host, self.port, 'id', additions = {
	# 		'key1': 'value1',
	# 		'key2': 'value2',
	# 		'callback': 'callback'
	# 	})
	# 	assert response['code'] == 100
	# 	assert response['description'] == 'OK'
	# 	assert type(response['data']) == dict
	# 	assert type(response['data']['agent_mac']) == str


	# def test_procedures_method(self):
	# 	response = arpcp.ARPCP.call(self.host, self.port, 'procedures')
	# 	assert response['code'] == 100
	# 	assert response['description'] == 'OK'
	# 	assert type(response['data']) == list
	# 	assert set(['add','multiple','sub','divide']).issubset(set(response['data']))


	# def test_procedures_method_with_extra_headers(self):
	# 	response = arpcp.ARPCP.call(self.host, self.port, 'procedures', {
	# 		'key1': 'value1',
	# 		'key2': 'value2',
	# 		'callback': 'callback'
	# 	})
	# 	assert response['code'] == 100
	# 	assert response['description'] == 'OK'
	# 	assert set(['add','multiple','sub','divide']).issubset(set(response['data']))


	# def test_procedures_method_with_extra_additions(self):
	# 	response = arpcp.ARPCP.call(self.host, self.port, 'procedures', additions = {
	# 		'key1': 'value1',
	# 		'key2': 'value2',
	# 		'callback': 'callback'
	# 	})
	# 	assert response['code'] == 100
	# 	assert response['description'] == 'OK'
	# 	assert set(['add','multiple','sub','divide']).issubset(set(response['data']))


	# def test_task_method(self):
	# 	task_id = str(uuid.uuid4())
	# 	response = arpcp.ARPCP.call(self.host, self.port, 'task', {
	# 		'remote_procedure': 'add',
	# 		'remote_procedure_args': [2, 3],
	# 		'task_id': task_id
	# 	})
	# 	assert response['code'] == 100
	# 	assert response['description'] == 'OK'
	# 	assert response['data']['result'] == float(5)
	# 	assert response['data']['task_id'] == task_id
	# 	assert self.redis.get(f'ARPCP:task:{task_id}:status') == 'done'
	# 	assert self.redis.exists(f'ARPCP:task:{task_id}:host_addr')
	# 	assert not self.redis.exists(f'ARPCP:task:{task_id}:callback')
	# 	assert type(json.loads(self.redis.get(f'ARPCP:task:{task_id}:message'))) == dict
	# 	assert task_id in json.loads(self.redis.get('ARPCP:tasks:assign'))
	# 	self._clear_redis(task_id)


	# def test_task_method_with_extra_headers(self):
	# 	task_id = str(uuid.uuid4())
	# 	response = arpcp.ARPCP.call(self.host, self.port, 'task', {
	# 		'remote_procedure': 'add',
	# 		'remote_procedure_args': [2, 3],
	# 		'task_id': task_id,
	# 		'key': 'value'
	# 	})
	# 	assert response['code'] == 100
	# 	assert response['description'] == 'OK'
	# 	assert response['data']['result'] == float(5)
	# 	assert response['data']['task_id'] == task_id
	# 	assert self.redis.get(f'ARPCP:task:{task_id}:status') == 'done'
	# 	assert self.redis.exists(f'ARPCP:task:{task_id}:host_addr')
	# 	assert not self.redis.exists(f'ARPCP:task:{task_id}:callback')
	# 	assert type(json.loads(self.redis.get(f'ARPCP:task:{task_id}:message'))) == dict
	# 	assert task_id in json.loads(self.redis.get('ARPCP:tasks:assign'))
	# 	self._clear_redis(task_id)


	# def test_task_method_with_extra_additions(self):
	# 	task_id = str(uuid.uuid4())
	# 	response = arpcp.ARPCP.call(self.host, self.port, 'task', {
	# 		'remote_procedure': 'add',
	# 		'remote_procedure_args': [2, 3],
	# 		'task_id': task_id
	# 	}, additions = {
	# 		'key': 'value'
	# 	})
	# 	assert response['code'] == 100
	# 	assert response['description'] == 'OK'
	# 	assert response['data']['result'] == float(5)
	# 	assert response['data']['task_id'] == task_id
	# 	assert self.redis.get(f'ARPCP:task:{task_id}:status') == 'done'
	# 	assert self.redis.exists(f'ARPCP:task:{task_id}:host_addr')
	# 	assert not self.redis.exists(f'ARPCP:task:{task_id}:callback')
	# 	assert type(json.loads(self.redis.get(f'ARPCP:task:{task_id}:message'))) == dict
	# 	assert task_id in json.loads(self.redis.get('ARPCP:tasks:assign'))
	# 	self._clear_redis(task_id)


	# def test_task_method_wo_all_required_headers(self):
	# 	response = arpcp.ARPCP.call(self.host, self.port, 'task')
	# 	assert response['code'] == 210
	# 	assert response['description'] == 'task id is not specified'
	# 	assert response['data'] == None


	# def test_task_method_wo_remote_procedure_args_header(self):
	# 	task_id = str(uuid.uuid4())
	# 	response = arpcp.ARPCP.call(self.host, self.port, 'task', {
	# 		'remote_procedure': 'add',
	# 		'task_id': task_id
	# 	})
	# 	assert response['code'] == 202
	# 	assert response['description'] == 'request message for "task" has no required headers for that method'
	# 	assert response['data'] == None
	# 	assert not self.redis.exists(f'ARPCP:task:{task_id}:status')
	# 	# assert not self.redis.exists(f'ARPCP:task:{task_id}:message')
	# 	# assert not self.redis.exists(f'ARPCP:task:{task_id}:callback')
	# 	# assert not self.redis.exists(f'ARPCP:task:{task_id}:host_addr')
	# 	# assert not task_id in json.loads(self.redis.get('ARPCP:tasks:assign'))


	# def test_task_method_wo_remote_procedure_header(self):
	# 	task_id = str(uuid.uuid4())
	# 	response = arpcp.ARPCP.call(self.host, self.port, 'task', {
	# 		'remote_procedure_args': [2, 3],
	# 		'task_id': task_id
	# 	})
	# 	assert response['code'] == 202
	# 	assert response['description'] == 'request message for "task" has no required headers for that method'
	# 	assert response['data'] == None
	# 	assert not self.redis.exists(f'ARPCP:task:{task_id}:status')
	# 	assert not self.redis.exists(f'ARPCP:task:{task_id}:message')
	# 	assert not self.redis.exists(f'ARPCP:task:{task_id}:callback')
	# 	assert not self.redis.exists(f'ARPCP:task:{task_id}:host_addr')
	# 	assert not task_id in json.loads(self.redis.get('ARPCP:tasks:assign'))


	# def test_task_method_with_invalid_procedure_params(self):
	# 	task_id = str(uuid.uuid4())
	# 	response = arpcp.ARPCP.call(self.host, self.port, 'task', {
	# 		'remote_procedure': 'add',
	# 		'remote_procedure_args': [2, 'a'],
	# 		'task_id': task_id
	# 	})
	# 	assert response['code'] == 301
	# 	assert response['description'].startswith("unsupported operand type(s)")
	# 	assert response['data']['result'] == None
	# 	assert response['data']['task_id'] == task_id
	# 	assert self.redis.get(f'ARPCP:task:{task_id}:status') == 'sent_to_agent'
	# 	assert self.redis.exists(f'ARPCP:task:{task_id}:host_addr')
	# 	assert not self.redis.exists(f'ARPCP:task:{task_id}:callback')
	# 	assert type(json.loads(self.redis.get(f'ARPCP:task:{task_id}:message'))) == dict
	# 	assert task_id in json.loads(self.redis.get('ARPCP:tasks:assign'))
	# 	self._clear_redis(task_id)


	# def test_task_method_with_extra_procedure_params(self):
	# 	task_id = str(uuid.uuid4())
	# 	response = arpcp.ARPCP.call(self.host, self.port, 'task', {
	# 		'remote_procedure': 'add',
	# 		'remote_procedure_args': [1, 2, 3],
	# 		'task_id': task_id
	# 	})
	# 	assert response['code'] == 301
	# 	assert response['description'].startswith("add() takes")
	# 	assert response['data']['result'] == None
	# 	assert response['data']['task_id'] == task_id
	# 	assert self.redis.get(f'ARPCP:task:{task_id}:status') == 'sent_to_agent'
	# 	assert self.redis.exists(f'ARPCP:task:{task_id}:host_addr')
	# 	assert not self.redis.exists(f'ARPCP:task:{task_id}:callback')
	# 	assert type(json.loads(self.redis.get(f'ARPCP:task:{task_id}:message'))) == dict
	# 	assert task_id in json.loads(self.redis.get('ARPCP:tasks:assign'))
	# 	self._clear_redis(task_id)


	# def test_task_method_with_nonexistent_procedure(self):
	# 	task_id = str(uuid.uuid4())
	# 	procedure_name = 'nonexistent_procedure'
	# 	response = arpcp.ARPCP.call(self.host, self.port, 'task', {
	# 		'remote_procedure': procedure_name,
	# 		'remote_procedure_args': [1, 2, 3],
	# 		'task_id': task_id
	# 	})
	# 	assert response['code'] == 302
	# 	assert response['description'].startswith(f"module 'procedures' has no attribute '{procedure_name}'")
	# 	assert response['data']['result'] == None
	# 	assert response['data']['task_id'] == task_id
	# 	assert self.redis.get(f'ARPCP:task:{task_id}:status') == 'sent_to_agent'
	# 	assert self.redis.exists(f'ARPCP:task:{task_id}:host_addr')
	# 	assert not self.redis.exists(f'ARPCP:task:{task_id}:callback')
	# 	assert type(json.loads(self.redis.get(f'ARPCP:task:{task_id}:message'))) == dict
	# 	assert task_id in json.loads(self.redis.get('ARPCP:tasks:assign'))
	# 	self._clear_redis(task_id)


	# def test_tast_method_with_callback(self):
	# 	task_id = str(uuid.uuid4())
	# 	response = arpcp.ARPCP.call(self.host, self.port, 'task', {
	# 		'remote_procedure': 'add',
	# 		'remote_procedure_args': [2, 3],
	# 		'task_id': task_id
	# 	}, {
	# 		'callback': 'double'
	# 	})
	# 	assert response['code'] == 100
	# 	assert response['description'] == 'OK'
	# 	assert response['data']['result'] == float(10)
	# 	assert response['data']['task_id'] == task_id
	# 	assert self.redis.get(f'ARPCP:task:{task_id}:status') == 'done'
	# 	assert self.redis.get(f'ARPCP:task:{task_id}:callback') == 'double'
	# 	assert self.redis.exists(f'ARPCP:task:{task_id}:host_addr')
	# 	assert type(json.loads(self.redis.get(f'ARPCP:task:{task_id}:message'))) == dict
	# 	assert task_id in json.loads(self.redis.get('ARPCP:tasks:assign'))
	# 	self._clear_redis(task_id)


	# def test_tast_method_with_nonexistent_callback(self):
	# 	task_id = str(uuid.uuid4())
	# 	callback_name = 'nonexistent_callback'
	# 	response = arpcp.ARPCP.call(self.host, self.port, 'task', {
	# 		'remote_procedure': 'add',
	# 		'remote_procedure_args': [2, 3],
	# 		'task_id': task_id
	# 	}, {
	# 		'callback': callback_name
	# 	})
	# 	assert response['code'] == 300
	# 	assert response['description'] == f'callback {callback_name} does not exist!'
	# 	assert response['data']['result'] == None
	# 	assert response['data']['task_id'] == None
	# 	assert self.redis.get(f'ARPCP:task:{task_id}:status') == 'done'
	# 	assert self.redis.get(f'ARPCP:task:{task_id}:callback') == 'double'
	# 	assert self.redis.exists(f'ARPCP:task:{task_id}:host_addr')
	# 	assert type(json.loads(self.redis.get(f'ARPCP:task:{task_id}:message'))) == dict
	# 	assert task_id in json.loads(self.redis.get('ARPCP:tasks:assign'))
	# 	# self._clear_redis(task_id)

	# def test_result_method_for_correct_task_status(self):
	# 	task_id = str(uuid.uuid4())
	# 	for status in arpcp.ARPCP.task_statuses:
	# 		response = arpcp.ARPCP.call(self.host, self.port, 'result', {
	# 			'task_id': task_id,
	# 			'task_status': status,
	# 			'task_result': None
	# 		})
	# 		assert response['code'] == 100
	# 		assert response['description'] == 'OK'
	# 		assert response['data'] == 'OK'
	# 		self._clear_redis(task_id)

	# def test_result_method_for_incorrect_task_status(self):
	# 	task_id = str(uuid.uuid4())
	# 	task_status = 'incorrect_task_status'
	# 	response = arpcp.ARPCP.call(self.host, self.port, 'result', {
	# 		'task_id': task_id,
	# 		'task_status': task_status,
	# 		'task_result': None
	# 	})
	# 	assert response['code'] == 310
	# 	assert response['description'] == f'task status {task_status} is undefined'
	# 	assert response['data'] == None
	# 	self._clear_redis(task_id)


	# def test_signal_method(self):
	# 	for status in arpcp.ARPCP.task_statuses:
	# 		task_id = str(uuid.uuid4())
	# 		self.redis.set('ARPCP:tasks:execute', json.dumps([task_id]))
	# 		self.redis.set(f"ARPCP:task:{task_id}:status", status)
	# 		self.redis.set(f"ARPCP:task:{task_id}:result", json.dumps(None))
	# 		response = arpcp.ARPCP.call(self.host, self.port, 'signal', {
	# 			'task_id': task_id
	# 		})
	# 		assert response['code'] == 100
	# 		assert response['description'] == 'OK'
	# 		assert response['data'] == None
	# 		time.sleep(0.1)
	# 		self._clear_redis(task_id)


	# def test_signal_method_with_wrong_task_id(self):
	# 	for status in arpcp.ARPCP.task_statuses:
	# 		task_id = str(uuid.uuid4())
	# 		self.redis.set(f"ARPCP:tasks:execute", json.dumps([task_id]))
	# 		self.redis.set(f"ARPCP:task:{task_id}:status", status)
	# 		self.redis.set(f"ARPCP:task:{task_id}:result", json.dumps(None))
	# 		response = arpcp.ARPCP.call(self.host, self.port, 'signal', {
	# 			'task_id': task_id * 2
	# 		})
	# 		assert response['code'] == 315
	# 		assert response['description'] == 'Non existent task id'
	# 		assert response['data'] == None
	# 		time.sleep(0.1)
	# 		self._clear_redis(task_id)


	# def test_atask_method_wo_callback(self):
	# 	task_id = str(uuid.uuid4())
	# 	response = arpcp.ARPCP.call(self.host, self.port, 'atask', {
	# 		'remote_procedure': 'add',
	# 		'remote_procedure_args': [3, 4],
	# 		'task_id': task_id
	# 	})
	# 	assert response['code'] == 100
	# 	assert response['description'] == 'OK'
	# 	assert response['data']['task_id'] == task_id
	# 	assert response['data']['result'] == None
	# 	time.sleep(0.2)
	# 	assert json.loads(self.redis.get(f'ARPCP:task:{task_id}:result')) == float(3 + 4)
	# 	assert self.redis.get(f'ARPCP:task:{task_id}:status') == 'done'
	# 	assert self.redis.exists(f'ARPCP:task:{task_id}:message')
	# 	assert self.redis.exists(f'ARPCP:task:{task_id}:caller_ip')
	# 	assert self.redis.exists(f'ARPCP:task:{task_id}:host_addr')
	# 	assert task_id in json.loads(self.redis.get('ARPCP:tasks:assign'))
	# 	assert task_id in json.loads(self.redis.get('ARPCP:tasks:execute'))
	# 	self._clear_redis(task_id)


	# def test_atask_method(self):
	# 	import callbacks
	# 	task_id = str(uuid.uuid4())
	# 	response = arpcp.ARPCP.call(self.host, self.port, 'atask', {
	# 		'remote_procedure': 'add',
	# 		'remote_procedure_args': [3, 4],
	# 		'task_id': task_id
	# 	}, additions = {
	# 		'callback': 'double'
	# 	})
	# 	assert response['code'] == 100
	# 	assert response['description'] == 'OK'
	# 	assert response['data']['task_id'] == task_id
	# 	assert response['data']['result'] == None
	# 	time.sleep(0.2)
	# 	assert json.loads(self.redis.get(f'ARPCP:task:{task_id}:result')) == callbacks.double(float(3 + 4))
	# 	assert self.redis.get(f'ARPCP:task:{task_id}:status') == 'done'
	# 	assert self.redis.exists(f'ARPCP:task:{task_id}:message')
	# 	assert self.redis.exists(f'ARPCP:task:{task_id}:caller_ip')
	# 	assert self.redis.exists(f'ARPCP:task:{task_id}:host_addr')
	# 	assert self.redis.exists(f'ARPCP:task:{task_id}:callback')
	# 	assert task_id in json.loads(self.redis.get('ARPCP:tasks:assign'))
	# 	assert task_id in json.loads(self.redis.get('ARPCP:tasks:execute'))
	# 	self._clear_redis(task_id)

