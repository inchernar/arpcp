import uuid
import time
import json
import arpcp
import redis
import pytest

class TestARPCP:
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


	def test_id_method_with_extra_headers(self):
		response = arpcp.ARPCP.call(self.host, self.port, 'id', {
			'key1': 'value1',
			'key2': 'value2',
			'callback': 'callback'
		})
		assert response['code'] == 100
		assert response['description'] == 'OK'
		assert type(response['data']) == dict
		assert type(response['data']['agent_mac']) == str


	def test_id_method_with_extra_additions(self):
		response = arpcp.ARPCP.call(self.host, self.port, 'id', additions = {
			'key1': 'value1',
			'key2': 'value2',
			'callback': 'callback'
		})
		assert response['code'] == 100
		assert response['description'] == 'OK'
		assert type(response['data']) == dict
		assert type(response['data']['agent_mac']) == str


	def test_procedures_method(self):
		response = arpcp.ARPCP.call(self.host, self.port, 'procedures')
		assert response['code'] == 100
		assert response['description'] == 'OK'
		assert type(response['data']) == list
		assert set(['add','multiple','sub','divide']).issubset(set(response['data']))


	def test_procedures_method_with_extra_headers(self):
		response = arpcp.ARPCP.call(self.host, self.port, 'procedures', {
			'key1': 'value1',
			'key2': 'value2',
			'callback': 'callback'
		})
		assert response['code'] == 100
		assert response['description'] == 'OK'
		assert set(['add','multiple','sub','divide']).issubset(set(response['data']))


	def test_procedures_method_with_extra_additions(self):
		response = arpcp.ARPCP.call(self.host, self.port, 'procedures', additions = {
			'key1': 'value1',
			'key2': 'value2',
			'callback': 'callback'
		})
		assert response['code'] == 100
		assert response['description'] == 'OK'
		assert set(['add','multiple','sub','divide']).issubset(set(response['data']))


	def test_task_method(self):
		task_id = str(uuid.uuid4())
		response = arpcp.ARPCP.call(self.host, self.port, 'task', {
			'remote_procedure': 'add',
			'remote_procedure_args': [2, 3],
			'task_id': task_id
		})
		assert response['code'] == 100
		assert response['description'] == 'OK'
		assert response['data']['result'] == float(5)
		assert response['data']['task_id'] == task_id
		assert self.redis.get(f'ARPCP:task:{task_id}:status') == 'done'
		assert self.redis.exists(f'ARPCP:task:{task_id}:host_addr')
		assert not self.redis.exists(f'ARPCP:task:{task_id}:callback')
		assert type(json.loads(self.redis.get(f'ARPCP:task:{task_id}:message'))) == dict
		assert task_id in json.loads(self.redis.get('ARPCP:tasks:assign'))
		arpcp.ARPCP.erase_task_from_redis(self.redis, task_id)


	def test_task_method_with_extra_headers(self):
		task_id = str(uuid.uuid4())
		response = arpcp.ARPCP.call(self.host, self.port, 'task', {
			'remote_procedure': 'add',
			'remote_procedure_args': [2, 3],
			'task_id': task_id,
			'key': 'value'
		})
		assert response['code'] == 100
		assert response['description'] == 'OK'
		assert response['data']['result'] == float(5)
		assert response['data']['task_id'] == task_id
		assert self.redis.get(f'ARPCP:task:{task_id}:status') == 'done'
		assert self.redis.exists(f'ARPCP:task:{task_id}:host_addr')
		assert not self.redis.exists(f'ARPCP:task:{task_id}:callback')
		assert type(json.loads(self.redis.get(f'ARPCP:task:{task_id}:message'))) == dict
		assert task_id in json.loads(self.redis.get('ARPCP:tasks:assign'))
		arpcp.ARPCP.erase_task_from_redis(self.redis, task_id)


	def test_task_method_with_extra_additions(self):
		task_id = str(uuid.uuid4())
		response = arpcp.ARPCP.call(self.host, self.port, 'task', {
			'remote_procedure': 'add',
			'remote_procedure_args': [2, 3],
			'task_id': task_id
		}, additions = {
			'key': 'value'
		})
		assert response['code'] == 100
		assert response['description'] == 'OK'
		assert response['data']['result'] == float(5)
		assert response['data']['task_id'] == task_id
		assert self.redis.get(f'ARPCP:task:{task_id}:status') == 'done'
		assert self.redis.exists(f'ARPCP:task:{task_id}:host_addr')
		assert not self.redis.exists(f'ARPCP:task:{task_id}:callback')
		assert type(json.loads(self.redis.get(f'ARPCP:task:{task_id}:message'))) == dict
		assert task_id in json.loads(self.redis.get('ARPCP:tasks:assign'))
		arpcp.ARPCP.erase_task_from_redis(self.redis, task_id)


	def test_task_method_wo_all_required_headers(self):
		response = arpcp.ARPCP.call(self.host, self.port, 'task')
		assert response['code'] == 1700
		assert response['description'] == 'task id is not specified'
		assert response['data'] == None


	def test_task_method_wo_remote_procedure_args_header(self):
		task_id = str(uuid.uuid4())
		response = arpcp.ARPCP.call(self.host, self.port, 'task', {
			'remote_procedure': 'add',
			'task_id': task_id
		})
		assert response['code'] == 402
		assert response['description'] == 'request message for "task" has no required headers for that method'
		assert response['data'] == None
		assert not self.redis.exists(f'ARPCP:task:{task_id}:status')
		assert not self.redis.exists(f'ARPCP:task:{task_id}:message')
		assert not self.redis.exists(f'ARPCP:task:{task_id}:callback')
		assert not self.redis.exists(f'ARPCP:task:{task_id}:host_addr')
		assert not task_id in json.loads(self.redis.get('ARPCP:tasks:assign'))


	def test_task_method_wo_remote_procedure_header(self):
		task_id = str(uuid.uuid4())
		response = arpcp.ARPCP.call(self.host, self.port, 'task', {
			'remote_procedure_args': [2, 3],
			'task_id': task_id
		})
		assert response['code'] == 402
		assert response['description'] == 'request message for "task" has no required headers for that method'
		assert response['data'] == None
		assert not self.redis.exists(f'ARPCP:task:{task_id}:status')
		assert not self.redis.exists(f'ARPCP:task:{task_id}:message')
		assert not self.redis.exists(f'ARPCP:task:{task_id}:callback')
		assert not self.redis.exists(f'ARPCP:task:{task_id}:host_addr')
		assert not task_id in json.loads(self.redis.get('ARPCP:tasks:assign'))


	def test_task_method_with_invalid_procedure_params(self):
		task_id = str(uuid.uuid4())
		response = arpcp.ARPCP.call(self.host, self.port, 'task', {
			'remote_procedure': 'add',
			'remote_procedure_args': [2, 'a'],
			'task_id': task_id
		})
		assert response['code'] == 202
		assert response['description'] == 'procedure execution error'
		assert response['data']['result'] == None
		assert response['data']['task_id'] == task_id
		assert not self.redis.exists(f'ARPCP:task:{task_id}:status')
		assert not self.redis.exists(f'ARPCP:task:{task_id}:host_addr')
		assert not self.redis.exists(f'ARPCP:task:{task_id}:callback')
		assert not self.redis.exists(f'ARPCP:task:{task_id}:message')
		assert not task_id in json.loads(self.redis.get('ARPCP:tasks:assign'))


	def test_task_method_with_extra_procedure_params(self):
		task_id = str(uuid.uuid4())
		response = arpcp.ARPCP.call(self.host, self.port, 'task', {
			'remote_procedure': 'add',
			'remote_procedure_args': [1, 2, 3],
			'task_id': task_id
		})
		assert response['code'] == 202
		assert response['description'] == 'procedure execution error'
		assert response['data']['result'] == None
		assert response['data']['task_id'] == task_id
		assert not self.redis.exists(f'ARPCP:task:{task_id}:status')
		assert not self.redis.exists(f'ARPCP:task:{task_id}:host_addr')
		assert not self.redis.exists(f'ARPCP:task:{task_id}:callback')
		assert not self.redis.exists(f'ARPCP:task:{task_id}:message')
		assert not task_id in json.loads(self.redis.get('ARPCP:tasks:assign'))


	def test_task_method_with_nonexistent_procedure(self):
		task_id = str(uuid.uuid4())
		procedure_name = 'nonexistent_procedure'
		response = arpcp.ARPCP.call(self.host, self.port, 'task', {
			'remote_procedure': procedure_name,
			'remote_procedure_args': [1, 2, 3],
			'task_id': task_id
		})
		assert response['code'] == 202
		assert response['description'] == 'procedure execution error'
		assert response['data']['result'] == None
		assert response['data']['task_id'] == task_id
		assert not self.redis.exists(f'ARPCP:task:{task_id}:status')
		assert not self.redis.exists(f'ARPCP:task:{task_id}:host_addr')
		assert not self.redis.exists(f'ARPCP:task:{task_id}:callback')
		assert not self.redis.exists(f'ARPCP:task:{task_id}:message')
		assert not task_id in json.loads(self.redis.get('ARPCP:tasks:assign'))


	def test_task_method_with_callback(self):
		task_id = str(uuid.uuid4())
		response = arpcp.ARPCP.call(self.host, self.port, 'task', {
			'remote_procedure': 'add',
			'remote_procedure_args': [2, 3],
			'task_id': task_id
		}, {
			'callback': 'double'
		})
		assert response['code'] == 100
		assert response['description'] == 'OK'
		assert response['data']['result'] == float(10)
		assert response['data']['task_id'] == task_id
		assert json.loads(self.redis.get(f'ARPCP:task:{task_id}:result')) == float(10)
		assert self.redis.get(f'ARPCP:task:{task_id}:status') == 'done'
		assert self.redis.get(f'ARPCP:task:{task_id}:callback') == 'double'
		assert self.redis.exists(f'ARPCP:task:{task_id}:host_addr')
		assert type(json.loads(self.redis.get(f'ARPCP:task:{task_id}:message'))) == dict
		assert task_id in json.loads(self.redis.get('ARPCP:tasks:assign'))
		arpcp.ARPCP.erase_task_from_redis(self.redis, task_id)


	def test_task_method_with_nonexistent_callback(self):
		task_id = str(uuid.uuid4())
		callback_name = 'nonexistent_callback'
		response = arpcp.ARPCP.call(self.host, self.port, 'task', {
			'remote_procedure': 'add',
			'remote_procedure_args': [2, 3],
			'task_id': task_id
		}, {
			'callback': callback_name
		})
		assert response['code'] == 1702
		assert response['description'] == f"module 'callbacks' has no attribute '{callback_name}'"
		assert response['data'] == None
		assert not self.redis.exists(f'ARPCP:task:{task_id}:status')
		assert not self.redis.exists(f'ARPCP:task:{task_id}:host_addr')
		assert not self.redis.exists(f'ARPCP:task:{task_id}:callback')
		assert not self.redis.exists(f'ARPCP:task:{task_id}:message')
		assert not task_id in json.loads(self.redis.get('ARPCP:tasks:assign'))


	def test_result_method(self):
		task_id = str(uuid.uuid4())
		try:
			assigned_tasks = json.loads(self.redis.get('ARPCP:tasks:assign'))
		except:
			assigned_tasks = []
		assigned_tasks.append(task_id)
		self.redis.set('ARPCP:tasks:assign', json.dumps(assigned_tasks))
		response = arpcp.ARPCP.call(self.host, self.port, 'result', {
			'task_id': task_id,
			'task_status': 'done',
			'task_result': float(5)
		})
		assert response['code'] == 100
		assert response['description'] == 'OK'
		assert response['data'] == 'OK'
		assert json.loads(self.redis.get(f'ARPCP:task:{task_id}:result')) == float(5)
		assert self.redis.get(f'ARPCP:task:{task_id}:status') == 'done'
		assert task_id in json.loads(self.redis.get('ARPCP:tasks:assign'))
		arpcp.ARPCP.erase_task_from_redis(self.redis, task_id)


	def test_result_method_with_callback(self):
		task_id = str(uuid.uuid4())
		try:
			assigned_tasks = json.loads(self.redis.get('ARPCP:tasks:assign'))
		except:
			assigned_tasks = []
		assigned_tasks.append(task_id)
		self.redis.set('ARPCP:tasks:assign', json.dumps(assigned_tasks))
		self.redis.set(f'ARPCP:task:{task_id}:callback', 'double')
		response = arpcp.ARPCP.call(self.host, self.port, 'result', {
			'task_id': task_id,
			'task_status': 'done',
			'task_result': float(5)
		})
		assert response['code'] == 100
		assert response['description'] == 'OK'
		assert response['data'] == 'OK'
		time.sleep(0.2)
		assert json.loads(self.redis.get(f'ARPCP:task:{task_id}:result')) == float(10)
		assert self.redis.get(f'ARPCP:task:{task_id}:status') == 'done'
		assert task_id in json.loads(self.redis.get('ARPCP:tasks:assign'))
		assert self.redis.get(f'ARPCP:task:{task_id}:callback') == 'double'
		arpcp.ARPCP.erase_task_from_redis(self.redis, task_id)


	def test_result_method_with_incorrect_callback(self):
		task_id = str(uuid.uuid4())
		callback_name = 'incorrect_callback'
		try:
			assigned_tasks = json.loads(self.redis.get('ARPCP:tasks:assign'))
		except:
			assigned_tasks = []
		assigned_tasks.append(task_id)
		self.redis.set('ARPCP:tasks:assign', json.dumps(assigned_tasks))
		self.redis.set(f'ARPCP:task:{task_id}:callback', callback_name)
		response = arpcp.ARPCP.call(self.host, self.port, 'result', {
			'task_id': task_id,
			'task_status': 'done',
			'task_result': float(5)
		})
		assert response['code'] == 100
		assert response['description'] == 'OK'
		assert response['data'] == 'OK'
		time.sleep(0.2)
		assert json.loads(self.redis.get(f'ARPCP:task:{task_id}:result')) == None
		assert self.redis.get(f'ARPCP:task:{task_id}:status') == 'callback_error'
		assert task_id in json.loads(self.redis.get('ARPCP:tasks:assign'))
		assert self.redis.get(f'ARPCP:task:{task_id}:callback') == callback_name
		arpcp.ARPCP.erase_task_from_redis(self.redis, task_id)


	def test_result_method_with_callback_and_incorrect_status(self):
		task_id = str(uuid.uuid4())
		incorrect_status = None
		try:
			assigned_tasks = json.loads(self.redis.get('ARPCP:tasks:assign'))
		except:
			assigned_tasks = []
		assigned_tasks.append(task_id)
		self.redis.set('ARPCP:tasks:assign', json.dumps(assigned_tasks))
		self.redis.set(f'ARPCP:task:{task_id}:callback', 'double')
		response = arpcp.ARPCP.call(self.host, self.port, 'result', {
			'task_id': task_id,
			'task_status': incorrect_status,
			'task_result': float(5)
		})
		assert response['code'] == 206
		assert response['description'] == 'incorrect task status'
		assert response['data'] == None
		time.sleep(0.2)
		assert not self.redis.exists(f'ARPCP:task:{task_id}:result')
		assert not self.redis.exists(f'ARPCP:task:{task_id}:status')
		arpcp.ARPCP.erase_task_from_redis(self.redis, task_id)


	def test_result_method_for_unassigned_task(self):
		task_id = str(uuid.uuid4())
		try:
			assigned_tasks = json.loads(self.redis.get('ARPCP:tasks:assign'))
		except:
			assigned_tasks = []
		self.redis.set('ARPCP:tasks:assign', json.dumps(assigned_tasks))
		response = arpcp.ARPCP.call(self.host, self.port, 'result', {
			'task_id': task_id,
			'task_status': 'done',
			'task_result': float(5)
		})
		assert response['code'] == 204
		assert response['description'] == 'unknown assign task'
		assert response['data'] == None
		time.sleep(0.2)
		assert not self.redis.exists(f'ARPCP:task:{task_id}:result')
		assert not self.redis.exists(f'ARPCP:task:{task_id}:status')
		assert not task_id in json.loads(self.redis.get('ARPCP:tasks:assign'))


	def test_signal_method(self):
		time.sleep(1)
		task_id = str(uuid.uuid4())
		if self.redis.exists('ARPCP:tasks:execute'):
			executed_tasks = json.loads(self.redis.get('ARPCP:tasks:execute'))
		else:
			executed_tasks = []
		executed_tasks.append(task_id)
		self.redis.set('ARPCP:tasks:execute', json.dumps(executed_tasks))
		if self.redis.exists('ARPCP:tasks:assign'):
			assigned_tasks = json.loads(self.redis.get('ARPCP:tasks:assign'))
		else:
			assigned_tasks = []
		assigned_tasks.append(task_id)
		self.redis.set('ARPCP:tasks:assign', json.dumps(assigned_tasks))
		self.redis.set(f"ARPCP:task:{task_id}:status", 'done')
		self.redis.set(f"ARPCP:task:{task_id}:result", json.dumps(12))
		self.redis.set(f"ARPCP:task:{task_id}:callback", 'double')
		response = arpcp.ARPCP.call(self.host, self.port, 'signal', {
			'task_id': task_id
		})
		assert response['code'] == 100
		assert response['description'] == 'OK'
		assert response['data'] == 'OK'
		time.sleep(0.2)
		assert json.loads(self.redis.get(f"ARPCP:task:{task_id}:result")) == float(24)
		arpcp.ARPCP.erase_task_from_redis(self.redis, task_id)


	def test_signal_method_with_wrong_task_id(self):
		task_id = str(uuid.uuid4())
		response = arpcp.ARPCP.call(self.host, self.port, 'signal', {
			'task_id': task_id * 2
		})
		assert response['code'] == 205
		assert response['description'] == 'unknown execute task'
		assert response['data'] == None
		arpcp.ARPCP.erase_task_from_redis(self.redis, task_id)


	def test_atask_method_wo_callback(self):
		task_id = str(uuid.uuid4())
		response = arpcp.ARPCP.call(self.host, self.port, 'atask', {
			'remote_procedure': 'add',
			'remote_procedure_args': [3, 4],
			'task_id': task_id
		})
		assert response['code'] == 100
		assert response['description'] == 'OK'
		assert response['data']['task_id'] == task_id
		assert response['data']['result'] == None
		time.sleep(0.2)
		assert json.loads(self.redis.get(f'ARPCP:task:{task_id}:result')) == float(3 + 4)
		assert self.redis.get(f'ARPCP:task:{task_id}:status') == 'done'
		assert self.redis.exists(f'ARPCP:task:{task_id}:message')
		assert self.redis.exists(f'ARPCP:task:{task_id}:caller_ip')
		assert self.redis.exists(f'ARPCP:task:{task_id}:host_addr')
		assert task_id in json.loads(self.redis.get('ARPCP:tasks:assign'))
		assert task_id in json.loads(self.redis.get('ARPCP:tasks:execute'))
		arpcp.ARPCP.erase_task_from_redis(self.redis, task_id)


	def test_atask_method(self):
		import callbacks
		task_id = str(uuid.uuid4())
		response = arpcp.ARPCP.call(self.host, self.port, 'atask', {
			'remote_procedure': 'add',
			'remote_procedure_args': [3, 4],
			'task_id': task_id
		}, additions = {
			'callback': 'double'
		})
		assert response['code'] == 100
		assert response['description'] == 'OK'
		assert response['data']['task_id'] == task_id
		assert response['data']['result'] == None
		time.sleep(0.2)
		assert json.loads(self.redis.get(f'ARPCP:task:{task_id}:result')) == callbacks.double(float(3 + 4))
		assert self.redis.get(f'ARPCP:task:{task_id}:status') == 'done'
		assert self.redis.exists(f'ARPCP:task:{task_id}:message')
		assert self.redis.exists(f'ARPCP:task:{task_id}:caller_ip')
		assert self.redis.exists(f'ARPCP:task:{task_id}:host_addr')
		assert self.redis.exists(f'ARPCP:task:{task_id}:callback')
		assert task_id in json.loads(self.redis.get('ARPCP:tasks:assign'))
		assert task_id in json.loads(self.redis.get('ARPCP:tasks:execute'))
		arpcp.ARPCP.erase_task_from_redis(self.redis, task_id)
