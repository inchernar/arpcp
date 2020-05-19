#!/usr/bin/python3

import os
import sys
import uuid
import time
import yaml
import json
import types
import redis
import socket
import threading as th
from importlib import reload

import procedures
import callbacks

VERSION = '0.6'
ERROR = True
LOG = 30
# 0,False - without logging
# 10 - necessary logging
# 20 - logging without low-level methods
# 30 - Full logging

# @TODO
# - all redis ops do with pipelines!!! (conqurent writing into redis)
# - try...except for all redis.get ops
# - difficulties with simultaneously client & server logging

# ==============================================================================

def log_print(extent, message = None, done = False, fail = False, end = '\n'):
	try:
		if LOG and (LOG >= extent):
			if done:
				print('Done')
			elif fail:
				print('Fail')
			else:
				print(f"[{time.ctime()}] {message}", end = end)
	except:
		pass

def error_print(message):
	try:
		if ERROR:
			print(f"[{time.ctime()}] [ERROR] {message}")
	except:
		pass

def traffic_print(message, message_type):
	try:
		if LOG:
			if message_type is ARPCP.MT_REQ:
				print(f"[{time.ctime()}] <=== {message}")
			elif message_type is ARPCP.MT_RES:
				print(f"[{time.ctime()}] ===> {message}")
	except:
		pass

# ==============================================================================

class ConfigReader:
	def __init__(self, config_file):
		log_print(extent=20, message='loading config_file...', end = '')
		with open(config_file) as c:
			self.config = yaml.safe_load(c)
		log_print(extent=20, done=True)

try:
	CONFIG = ConfigReader('arpcp.conf.yml').config
except:
	CONFIG = {
		'server': {
			'host': '0.0.0.0',
			'port': 7018,
			'connection_queue_size': 1,
			'max_workers_count': 100,
			'threadname_prefix': 'ARPCP',
			'master_threadname': 'server',
			'worker_threadname': 'worker'
		},
		'redis': {
			'host': '127.0.0.1',
			'port': 6379
		}
	}

SERVER_CONFIGS = CONFIG['server']
ADDR_CONF = (SERVER_CONFIGS['host'],SERVER_CONFIGS['port'])

REDIS_HOST = CONFIG['redis']['host']
REDIS_PORT = CONFIG['redis']['port']

# ==============================================================================

class ARPCPException(Exception):
	def __init__(self, errno, errmsg):
		self.args = (errno, errmsg)
		self.errno = errno
		self.errmsg = errmsg

# ==============================================================================

class ARPCP:

	# ----- arpcp constants ----------------------------------------------------

	proto = {
		'request': {
			'requires': ['method', 'version'],
			'methods': {
				'procedures': [],
				'id': [],
				'task': ['remote_procedure','remote_procedure_args','task_id'],
				'result': ['task_id', 'task_status', 'task_result'],
				'signal': ['task_id'],
				'atask': ['remote_procedure','remote_procedure_args','task_id'],
				'test_method': []
			}
		},
		'response': {
			'requires': ['code', 'description', 'data'],
		}
	}

	task_statuses = [
		'created',
		'sended_to_agent',
		'successfully_registered',
		'unregistered',
		'executing',
		'done',
		'execution_error',
		'callback_error',
		'unknown_error'
	]

	MT_REQ = 0
	MT_RES = 1

	# ----- low-level methods for processing a connection ----------------------

	@staticmethod
	def redis(host = '127.0.0.1', port = 6379):
		return redis.Redis(host = host, port = port, decode_responses = True)


	@staticmethod
	def erase_task_from_redis(r, task_id):
		try:
			# remove from assigned tasks
			if r.exists('ARPCP:tasks:assign'):
				assigned_tasks = json.loads(r.get('ARPCP:tasks:assign'))
				if task_id in assigned_tasks:
					assigned_tasks.remove(task_id)
					r.set('ARPCP:tasks:assign', json.dumps(assigned_tasks))
			# remove from executed tasks
			if r.exists('ARPCP:tasks:execute'):
				executed_tasks = json.loads(r.get('ARPCP:tasks:execute'))
				if task_id in executed_tasks:
					executed_tasks.remove(task_id)
					r.set('ARPCP:tasks:execute', json.dumps(executed_tasks))
			# remove all keys
			r.delete(f'ARPCP:task:{task_id}:message')
			r.delete(f'ARPCP:task:{task_id}:status')
			r.delete(f'ARPCP:task:{task_id}:host_addr')
			r.delete(f'ARPCP:task:{task_id}:caller_ip')
			r.delete(f'ARPCP:task:{task_id}:callback')
			r.delete(f'ARPCP:task:{task_id}:result')
		except:
			return


	@staticmethod
	def socket(local_host, local_port, connection_queue_size, timeout = 0.1):
		log_print(extent=30, message='creating server socket..')
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		sock.bind((local_host, local_port,))
		log_print(extent=30, message=f'server socket binded to {local_host}:{local_port}')
		sock.listen(connection_queue_size)
		log_print(extent=30, message=f'max queue to server socket {connection_queue_size}')
		sock.settimeout(timeout) # setblocking(False) <-> settimeout(0)
		log_print(extent=30, message=f'timeout for server socket {timeout}')
		log_print(extent=30, message='server socket created')
		return sock


	@staticmethod
	def accept(sock):
		conn, addr = sock.accept()
		return conn, addr


	@staticmethod
	def close(sock):
		log_print(extent=30, message='closing socket...', end='')
		sock.close()
		log_print(extent=30, done = True)


	@staticmethod
	def connect(remote_host, remote_port, timeout = 5):
		log_print(extent=30, message='creating client socket..')
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.settimeout(timeout)
		log_print(extent=30, message=f'timeout for server socket {timeout}')
		log_print(extent=30, message='client socket created')
		log_print(extent=30, message=f'connecting to {remote_host}:{remote_port}...', end='')
		sock.connect((remote_host, remote_port,))
		log_print(extent=30, done=True)
		return sock

	# ----- methods for receiving and sending arpcp messages -------------------

	@staticmethod
	def parse_data(data, message_type):
		log_print(extent=30, message='parsing data..')
		# params validation
		if (message_type != ARPCP.MT_REQ) and (message_type != ARPCP.MT_RES):
			raise ARPCPException(None, 'invalid message type')
		# parsing
		if message_type is ARPCP.MT_REQ:
			try:
				message = json.loads(data.decode('utf-8'))
				if not type(message) is dict:
					raise Exception
			except:
				raise ARPCPException(400, 'bad request')
			if set(ARPCP.proto['request']['requires']).issubset(set(message.keys())):
				method = message['method']
				try:
					method_headers = ARPCP.proto['request']['methods'][method]
				except:
					raise ARPCPException(401, f'method {method} is unsupported')
				if not set(method_headers).issubset(set(message.keys())):
					raise ARPCPException(402, f'request message for "{method}" has no required headers for that method')
			else:
				raise ARPCPException(403, 'request message has no required headers')
		elif message_type is ARPCP.MT_RES:
			try:
				message = json.loads(data.decode('utf-8'))
				if not type(message) is dict:
					raise Exception
			except:
				raise ARPCPException(1200, 'bad response')
			if not set(ARPCP.proto['response']['requires']).issubset(set(message.keys())):
				raise ARPCPException(1201, 'response message has no required headers')
		log_print(extent=30, message='data parsed!')
		return message


	@staticmethod
	def receive_message(sock, message_type):
		log_print(extent=20, message='receiving message..')
		# params validation
		if (message_type != ARPCP.MT_REQ) and (message_type != ARPCP.MT_RES):
			ARPCP.close(sock)
			raise ARPCPException(None, 'invalid message type')
		# reading data from socket
		log_print(extent=20, message='reading data from socket..')
		try:
			with sock.makefile("rb") as socketfile:
				data = socketfile.readline()
		except Exception as e:
			if message_type == ARPCP.MT_REQ:
				ARPCP.close(sock)
				error_print(str(e))
				return None
			elif message_type == ARPCP.MT_RES:
				ARPCP.close(sock)
				error_print(str(e))
				return {'code': 1300, 'description': str(e), 'data': None}
		log_print(extent=20, message='data read!')
		# parse data to message
		try:
			message = ARPCP.parse_data(data, message_type)
		except ARPCPException as e:
			if message_type == ARPCP.MT_REQ:
				error_print(str(e))
				error_response = {'code': e.errno, 'description': e.errmsg, 'data': None}
				ARPCP.send_message(sock, error_response, ARPCP.MT_RES)
				ARPCP.close(sock)
				return None
			elif message_type == ARPCP.MT_RES:
				ARPCP.close(sock)
				error_print(str(e))
				return {'code': e.errno, 'description': e.errmsg, 'data': None}
		log_print(extent=20, message='message received!')
		traffic_print(message, message_type)
		return message


	@staticmethod
	def serialize_message(message, message_type):
		log_print(extent=30, message='message serializing..')
		# params validation
		if (message_type != ARPCP.MT_REQ) and (message_type != ARPCP.MT_RES):
			raise ARPCPException(None, 'invalid message type')
		# serializing
		try:
			data = (json.dumps(message)+'\r\n').encode('UTF-8')
		except Exception as e:
			if message_type is ARPCP.MT_REQ:
				raise ARPCPException(1600, 'can not serialize request')
			elif message_type is ARPCP.MT_RES:
				raise ARPCPException(101, 'can not serialize response')
		log_print(extent=30, message='message serialized!')
		return data


	@staticmethod
	def send_message(sock, message, message_type):
		# @TODO add close_sock (True|False) option for closing socket into function or not
		log_print(extent=30, message='sending message..')
		# params validation
		if (message_type != ARPCP.MT_REQ) and (message_type != ARPCP.MT_RES):
			ARPCP.close(sock)
			raise ARPCPException(None, 'invalid message type')
		# serializing message to data
		try:
			data = ARPCP.serialize_message(message, message_type)
		except ARPCPException as e:
			if message_type == ARPCP.MT_REQ:
				ARPCP.close(sock)
				error_print(str(e))
				raise ARPCPException(e.errno, e.errmsg)
			elif message_type == ARPCP.MT_RES:
				try:
					error_print(str(e))
					error_response = {'code': e.errno, 'description': e.errmsg, 'data': None}
					ARPCP.send_message(sock, error_response, ARPCP.MT_RES)
					ARPCP.close(sock)
					raise ARPCPException(e.errno, e.errmsg)
				except:
					# defense from recursion explosion
					ARPCP.close(sock)
					raise ARPCPException(None, str(e))
		# writing data to socket
		log_print(extent=20, message='writing data to socket..')
		try:
			with sock.makefile("wb") as socketfile:
				socketfile.write(data)
		except Exception as e:
			if message_type == ARPCP.MT_REQ:
				ARPCP.close(sock)
				error_print(str(e))
				raise ARPCPException(1500, str(e))
			elif message_type == ARPCP.MT_RES:
				ARPCP.close(sock)
				error_print(str(e))
				raise ARPCPException(None, str(e))
		log_print(extent=20, message='data written')
		log_print(extent=30, message='message sent')
		traffic_print(message, message_type)

	# ----- high-level client-side methods for call arpcp methods --------------

	@staticmethod
	def call(remote_host, remote_port, method, headers = {}, additions = {}):
	# def call(remote_host, remote_port, method, headers = {}, additions = {}):
		log_print(extent=20, message='ARPCP.call method started')

		if (not type(remote_host) is str) or \
			(not type(remote_port) is int) or \
			(not type(method) is str) or \
			(not type(headers) is dict) or \
			(not type(additions) is dict):
			raise Exception('invalid arguments')

		message = {'method': method, 'version': VERSION}
		message.update(headers)
		message.update(additions)

		if method == 'task':
			## request preprocessing
			try:
				task_id = message['task_id']
			except Exception as e:
				return {'code': 1700, 'description': 'task id is not specified', 'data': None}
			try:
				_redis = ARPCP.redis(REDIS_HOST, REDIS_PORT)
			except Exception as e:
				return {'code': 1701, 'description': str(e), 'data': None}

			# Check & registering callback
			if 'callback' in additions:
				log_print(extent=20, message='check out existense callback function')
				try:
					import callbacks
					reload(callbacks)
					getattr(callbacks, additions['callback'])
				except Exception as e:
					return {'code': 1702, 'description': str(e), 'data': None}
				log_print(extent=20, message=f'callback {additions["callback"]} exists!')
				_redis.set(f'ARPCP:task:{task_id}:callback', additions['callback'])

			# Check & update ARPCP:tasks:assign, append task_id
			if not _redis.exists('ARPCP:tasks:assign'):
				_redis.set('ARPCP:tasks:assign', json.dumps([]))
			assigned_tasks = json.loads(_redis.get('ARPCP:tasks:assign'))
			if task_id in assigned_tasks:
				return {'code': 1703, 'description': f'task {task_id} already exists!', 'data': None}
			# @TODO pipe begin
			assigned_tasks = json.loads(_redis.get('ARPCP:tasks:assign'))
			assigned_tasks.append(task_id)
			_redis.set('ARPCP:tasks:assign', json.dumps(assigned_tasks))
			# @TODO pipe end

			# Set meta info about assigned task into redis
			log_print(extent=20, message='saving data in redis with ARPCP:task:<id>:* prefix')
			_redis.set(f'ARPCP:task:{task_id}:message', json.dumps(message))
			log_print(extent=20, message=f'*:message {message}')
			default_task_status = 'created'
			_redis.set(f'ARPCP:task:{task_id}:status',default_task_status)
			log_print(extent=20, message=f'*:status {default_task_status}')
			host_addr = json.dumps({'remote_host': remote_host, 'remote_port': remote_port})
			_redis.set(f'ARPCP:task:{task_id}:host_addr', host_addr)
			log_print(extent=20, message=f'*:host_addr {host_addr}')

			## connection openning
			sock = ARPCP.connect(remote_host, remote_port)

			## request sending
			try:
				ARPCP.send_message(sock, message, ARPCP.MT_REQ)
			except ARPCPException as e:
				ARPCP.erase_task_from_redis(_redis, task_id)
				return {'code': e.errno, 'description': e.errmsg, 'data': None}

			## intermediate processing
			sent_status = 'sent_to_agent'
			_redis.set(f'ARPCP:task:{task_id}:status', sent_status)
			log_print(extent=20, message=f'*:status {sent_status}')

			## response receiving
			try:
				received_message = ARPCP.receive_message(sock, ARPCP.MT_RES)
			except Exception as e:
				ARPCP.erase_task_from_redis(_redis, task_id)
				return {'code': 1704, 'description': str(e), 'data': None}

			## closing the connection
			ARPCP.close(sock)

			## response postprocessing
			if received_message['code'] == 100:
				result = received_message['data']['result']
				if _redis.exists(f'ARPCP:task:{task_id}:callback'):
					callback = _redis.get(f'ARPCP:task:{task_id}:callback')
					log_print(extent=20, message=f'calling callback "{callback}"')
					try:
						result = getattr(callbacks, callback)(received_message['data']['result'])
					except Exception as e:
						_redis.set(f'ARPCP:task:{task_id}:status', 'callback_error')
						return {'code': 1101, 'description': str(e), 'data': None}
					log_print(extent=20, message=f'callback executed with result "{result}"')
				received_message['data'].update({'result': result})
				_redis.set(f'ARPCP:task:{task_id}:status', 'done')
				_redis.set(f'ARPCP:task:{task_id}:result', json.dumps(result))
			else:
				ARPCP.erase_task_from_redis(_redis, task_id)
				return received_message

			log_print(extent=20, message='ARPCP.call method finished')
			return received_message

		elif method == 'atask':
			try:
				task_id = message['task_id']
			except Exception as e:
				return {'code': 1700, 'description': 'task id is not specified', 'data': None}
			try:
				_redis = ARPCP.redis(REDIS_HOST, REDIS_PORT)
			except Exception as e:
				return {'code': 1701, 'description': str(e), 'data': None}

			# Check & registering callback
			if 'callback' in additions:
				log_print(extent=20, message='check out existense callback function')
				try:
					import callbacks
					reload(callbacks)
					getattr(callbacks, additions['callback'])
				except Exception as e:
					return {'code': 1702, 'description': str(e), 'data': None}
				log_print(extent=20, message=f'callback {additions["callback"]} exists!')
				_redis.set(f'ARPCP:task:{task_id}:callback', additions['callback'])

			# Check & update ARPCP:tasks:assign, append task_id
			if not _redis.exists('ARPCP:tasks:assign'):
				_redis.set('ARPCP:tasks:assign', json.dumps([]))
			assigned_tasks = json.loads(_redis.get('ARPCP:tasks:assign'))
			if task_id in assigned_tasks:
				return {'code': 1703, 'description': f'task {task_id} already exists!', 'data': None}
			assigned_tasks.append(task_id)
			_redis.set('ARPCP:tasks:assign', json.dumps(assigned_tasks))

			# Set meta info about assigned task into redis
			log_print(extent=20, message='saving data in redis with ARPCP:task:<id>:* prefix')
			_redis.set(f'ARPCP:task:{task_id}:message', json.dumps(message))
			log_print(extent=20, message=f'*:message {message}')
			default_task_status = 'created'
			_redis.set(f'ARPCP:task:{task_id}:status',default_task_status)
			log_print(extent=20, message=f'*:status {default_task_status}')
			host_addr = json.dumps({'remote_host': remote_host, 'remote_port': remote_port})
			_redis.set(f'ARPCP:task:{task_id}:host_addr', host_addr)
			log_print(extent=20, message=f'*:host_addr {host_addr}')

			## connection openning
			sock = ARPCP.connect(remote_host, remote_port)

			## request sending
			try:
				ARPCP.send_message(sock, message, ARPCP.MT_REQ)
			except ARPCPException as e:
				ARPCP.erase_task_from_redis(_redis, task_id)
				return {'code': e.errno, 'description': e.errmsg, 'data': None}

			## intermediate processing
			sent_status = 'sent_to_agent'
			_redis.set(f'ARPCP:task:{task_id}:status', sent_status)
			log_print(extent=20, message=f'*:status {sent_status}')

			## response receiving
			try:
				received_message = ARPCP.receive_message(sock, ARPCP.MT_RES)
			except Exception as e:
				ARPCP.erase_task_from_redis(_redis, task_id)
				return {'code': 1704, 'description': str(e), 'data': None}

			## closing the connection
			ARPCP.close(sock)

			# Update assigned task status after response receiving
			if received_message['code'] == 100:
				successfully_registered = 'successfully_registered'
				_redis.set(f'ARPCP:task:{task_id}:status', successfully_registered)
				log_print(extent=20, message=f'*:status {successfully_registered}')
			else:
				unregistered = 'unregistered'
				_redis.set(f'ARPCP:task:{task_id}:status', unregistered)
				log_print(extent=20, message=f'*:status {unregistered}')

			log_print(extent=20, message='ARPCP.call method finished')
			return received_message

		else:
			## request preprocessing
			pass
			## connection openning
			sock = ARPCP.connect(remote_host, remote_port)
			## request sending
			try:
				ARPCP.send_message(sock, message, ARPCP.MT_REQ)
			except ARPCPException as e:
				return {'code': e.errno, 'description': e.errmsg, 'data': None}
			## intermediate processing
			pass
			## response receiving
			try:
				received_message = ARPCP.receive_message(sock, ARPCP.MT_RES)
			except ARPCPException as e:
				return {'code': e.errno, 'description': e.errmsg, 'data': None}
			## closing the connection
			ARPCP.close(sock)
			## response postprocessing
			pass
			log_print(extent=20, message='ARPCP.call method finished')
			return received_message

	# ----- high-level server-side methods for handling arpcp methods ----------

	@staticmethod
	def handle(sock, addr):
		log_print(extent=20, message='common handle started')

		# read data & parse message (4xx)
		request = ARPCP.receive_message(sock, ARPCP.MT_REQ)
		if request is None:
			log_print(extent=20, message='common handle finished with error')
			return

		# check method handler existence (3xx)
		try:
			log_print(extent=20, message=f'check handle_{request["method"]} existence')
			getattr(ARPCP, f'handle_{request["method"]}')
			log_print(extent=20, message=f'handle_{request["method"]} exists')
		except Exception as e:
			error_print(str(e))
			error_response = {'code': 300, 'description': str(e), 'data': None}
			try:
				ARPCP.send_message(sock, error_response, ARPCP.MT_RES)
				ARPCP.close(sock)
				log_print(extent=20, message='common handle finished with error')
				return
			except ARPCPException as e:
				log_print(extent=20, message='common handle finished with error')
				return
			except Exception as e:
				raise e

		try:
			getattr(ARPCP, f'handle_{request["method"]}')(sock, addr, request)
		except ARPCPException as e:
			log_print(extent=20, message='common handle finished with error')
			return
		except Exception as e:
			raise e

		log_print(extent=20, message='common handle finished')


	@staticmethod
	def handle_id(sock, addr, message):
		log_print(extent=20, message='handle_id started')
		def _mac_addr():
			address = uuid.getnode()
			hexeble = iter(hex(address)[2:].zfill(12))
			mac_addr = ":".join(i + next(hexeble) for i in hexeble)
			return mac_addr

		response = {'code': 100, 'description': 'OK', 'data': {'agent_mac': _mac_addr()}}
		try:
			ARPCP.send_message(sock, response, ARPCP.MT_RES)
		except ARPCPException as e:
			log_print(extent=20, message='handle_id finished with error')
			return
		except Exception as e:
			raise e

		ARPCP.close(sock)
		log_print(extent=20, message='handle_id finished')


	@staticmethod
	def handle_procedures(sock, addr, message):
		log_print(extent=20, message='handle_procedures started')

		log_print(extent=20, message='procedures reloading..')
		try:
			import procedures
			reload(procedures)
		except Exception as e:
			error_print(str(e))
			error_response = {'code': 200, 'description': str(e), 'data': None}
			try:
				ARPCP.send_message(sock, error_response, ARPCP.MT_RES)
			except ARPCPException as e:
				log_print(extent=20, message='handle_procedures finished with error')
				return
			except Exception as e:
				raise e
			ARPCP.close(sock)
			log_print(extent=20, message='handle_procedures finished with error')
			return
		log_print(extent=20, message='procedures reloaded')

		available_procedures = list(filter(lambda x: not x.startswith('_'), dir(procedures)))
		response = {'code': 100, 'description': 'OK', 'data': available_procedures}
		try:
			ARPCP.send_message(sock, response, ARPCP.MT_RES)
		except ARPCPException as e:
			log_print(extent=20, message='handle_procedures finished with error')
			return
		except Exception as e:
			raise e

		ARPCP.close(sock)
		log_print(extent=20, message='handle_procedures finished')


	@staticmethod
	def handle_task(sock, addr, message):
		log_print(extent=20, message='handle_task started')
		task_id = message["task_id"]
		remote_procedure = message["remote_procedure"]
		remote_procedure_args = message['remote_procedure_args']

		# import & reload procedures
		try:
			log_print(extent=20, message='procedures reloading..')
			import procedures
			reload(procedures)
		except Exception as e:
			error_print(str(e))
			error_response = {'code': 201, 'description': str(e), 'data': {'task_id': task_id, 'result': None}}
			try:
				ARPCP.send_message(sock, error_response, ARPCP.MT_RES)
			except ARPCPException as e:
				log_print(extent=20, message='handle_task finished with error')
				return
			except Exception as e:
				raise e
			ARPCP.close(sock)
			log_print(extent=20, message='handle_task finished with error')
			return

		# execute procedure
		log_print(extent=20,message=f'procedure {remote_procedure} started..')
		try:
			remote_procedure_result = getattr(procedures, remote_procedure)(*remote_procedure_args)
		except Exception as e:
			error_print(str(e))
			error_response = {'code': 202, 'description': 'procedure execution error', 'data': {'task_id': task_id, 'result': None}}
			try:
				ARPCP.send_message(sock, error_response, ARPCP.MT_RES)
			except ARPCPException as e:
				log_print(extent=20, message='handle_task finished with error')
				return
			except Exception as e:
				raise e
			ARPCP.close(sock)
			log_print(extent=20, message='handle_task finished with error')
			return
		log_print(extent=20, message='procedure finished')

		# response sending
		response = {
			'code': 100,
			'description': 'OK',
			'data': {
				'task_id': task_id,
				'result': remote_procedure_result
			}
		}
		try:
			ARPCP.send_message(sock, response, ARPCP.MT_RES)
		except ARPCPException as e:
			log_print(extent=20, message='handle_task finished with error')
			return
		except Exception as e:
			raise e

		ARPCP.close(sock)
		log_print(extent=20, message='handle_task finished')


	@staticmethod
	def handle_result(sock, addr, message):
		log_print(extent=20, message='handle_result started')

		# check redis availability
		try:
			_redis = ARPCP.redis(REDIS_HOST, REDIS_PORT)
		except Exception as e:
			error_response = {'code': 203, 'description': 'redis unavailable', 'data': None}
			try:
				ARPCP.send_message(sock, error_response, ARPCP.MT_RES)
			except ARPCPException as e:
				log_print(extent=20, message='handle_result finished with error')
				return
			except Exception as e:
				raise e
			log_print(extent=20, message='handle_result finished with error')
			ARPCP.close(sock)
			return

		task_id = message['task_id']
		task_result = message['task_result']
		task_status = message['task_status']

		# check task_id in ARPCP:tasks:assign
		if not _redis.exists('ARPCP:tasks:assign') or \
				(not task_id in json.loads(_redis.get('ARPCP:tasks:assign'))):
			error_response = {'code': 204, 'description': 'unknown assign task', 'data': None}
			try:
				ARPCP.send_message(sock, error_response, ARPCP.MT_RES)
			except ARPCPException as e:
				log_print(extent=20, message='handle_result finished with error')
				return
			except Exception as e:
				raise e
			log_print(extent=20, message='handle_result finished with error')
			ARPCP.close(sock)
			return

		# check task_status
		if not task_status in ARPCP.task_statuses:
			error_response = {'code': 206, 'description': 'incorrect task status', 'data': None}
			try:
				ARPCP.send_message(sock, error_response, ARPCP.MT_RES)
			except ARPCPException as e:
				log_print(extent=20, message='handle_result finished with error')
				return
			except Exception as e:
				raise e
			log_print(extent=20, message='handle_result finished with error')
			ARPCP.close(sock)
			return

		# update data in redis
		log_print(extent=20, message='saving data in redis with ARPCP:task:* prefix')
		_redis.set(f'ARPCP:task:{task_id}:status', task_status)
		log_print(extent=20, message=f'*:status {task_status}')
		_redis.set(f'ARPCP:task:{task_id}:result', json.dumps(task_result))
		log_print(extent=20, message=f'*:result {task_result}')

		# send OK response
		response = {'code': 100, 'description': 'OK', 'data': 'OK'}
		try:
			ARPCP.send_message(sock, response, ARPCP.MT_RES)
		except ARPCPException as e:
			log_print(extent=20, message='handle_result finished with error')
			return
		except Exception as e:
			raise e

		# execute callback
		if _redis.exists(f'ARPCP:task:{task_id}:callback') and \
				task_status == 'done':
			import callbacks
			reload(callbacks)
			callback = _redis.get(f'ARPCP:task:{task_id}:callback')
			log_print(extent=20, message=f'calling callback "{callback}"')
			try:
				task_result = getattr(callbacks, callback)(task_result)
			except Exception as e:
				task_result = None
				log_print(extent=20, message='handle_result finished with error')
				_redis.set(f'ARPCP:task:{task_id}:status', 'callback_error')
				_redis.set(f'ARPCP:task:{task_id}:result', json.dumps(task_result))
				log_print(extent=20, message=f'*:result {task_result}')
				return
			log_print(extent=20, message=f'callback executed with result "{task_result}"')
			_redis.set(f'ARPCP:task:{task_id}:result', json.dumps(task_result))
			log_print(extent=20, message=f'*:result {task_result}')

		ARPCP.close(sock)
		log_print(extent=20, message='handle_result finished')


	@staticmethod
	def handle_signal(sock, addr, message):
		log_print(extent=20, message='handle_signal started')

		# check redis availability
		try:
			_redis = ARPCP.redis(REDIS_HOST, REDIS_PORT)
		except Exception as e:
			error_response = {'code': 203, 'description': 'redis unavailable', 'data': None}
			try:
				ARPCP.send_message(sock, error_response, ARPCP.MT_RES)
			except ARPCPException as e:
				log_print(extent=20, message='handle_signal finished with error')
				return
			except Exception as e:
				raise e
			log_print(extent=20, message='handle_signal finished with error')
			ARPCP.close(sock)
			return

		task_id = message['task_id']

		# check task_id in ARPCP:tasks:execute
		if not _redis.exists('ARPCP:tasks:execute') or \
				(not task_id in json.loads(_redis.get('ARPCP:tasks:execute'))):
			error_response = {'code': 205, 'description': 'unknown execute task', 'data': None}
			try:
				ARPCP.send_message(sock, error_response, ARPCP.MT_RES)
			except ARPCPException as e:
				log_print(extent=20, message='handle_result finished with error')
				return
			except Exception as e:
				raise e
			log_print(extent=20, message='handle_result finished with error')
			ARPCP.close(sock)
			return

		# send OK response
		response = {'code': 100, 'description': 'OK', 'data': 'OK'}
		try:
			ARPCP.send_message(sock, response, ARPCP.MT_RES)
		except ARPCPException as e:
			log_print(extent=20, message='handle_result finished with error')
			return
		except Exception as e:
			raise e
		ARPCP.close(sock)

		task_result = json.loads(_redis.get(f'ARPCP:task:{task_id}:result'))
		task_status = _redis.get(f'ARPCP:task:{task_id}:status')
		result_request = {'task_result': task_result, 'task_status': task_status, 'task_id': task_id}
		result_response = ARPCP.call(addr[0], ADDR_CONF[1], 'result', result_request)

		log_print(extent=20, message='handle_signal finished')


	@staticmethod
	def handle_atask(sock, addr, message):
		log_print(extent=20, message='handle_atask started')

		# check redis availability
		try:
			_redis = ARPCP.redis(REDIS_HOST, REDIS_PORT)
		except Exception as e:
			error_response = {'code': 203, 'description': 'redis unavailable', 'data': None}
			try:
				ARPCP.send_message(sock, error_response, ARPCP.MT_RES)
			except ARPCPException as e:
				log_print(extent=20, message='handle_atask finished with error')
				return
			except Exception as e:
				raise e
			log_print(extent=20, message='handle_atask finished with error')
			ARPCP.close(sock)
			return

		task_id = message["task_id"]
		remote_procedure = message["remote_procedure"]
		remote_procedure_args = message['remote_procedure_args']
		default_result = None
		default_task_status = 'created'

		## 1 part. Request receiving
		# Check & update ARPCP:tasks:execute, append task_id
		if not _redis.exists('ARPCP:tasks:execute'):
			_redis.set('ARPCP:tasks:execute', json.dumps([]))
		executed_tasks = json.loads(_redis.get('ARPCP:tasks:execute'))
		if task_id in executed_tasks:
			error_response = {'code': 207, 'description': f'task {task_id} already exists!', 'data': {'task_id': task_id, 'result': None}}
			try:
				ARPCP.send_message(sock, error_response, ARPCP.MT_RES)
			except ARPCPException as e:
				log_print(extent=20, message='handle_atask finished with error')
				return
			except Exception as e:
				raise e
			log_print(extent=20, message='handle_atask finished with error')
			ARPCP.close(sock)
			return
		# @TODO pipe begin
		executed_tasks = json.loads(_redis.get('ARPCP:tasks:execute'))
		executed_tasks.append(task_id)
		_redis.set('ARPCP:tasks:execute', json.dumps(executed_tasks))
		# @TODO pipe end

		# Set meta info about executing task into redis
		log_print(extent=20, message='saving data in redis with ARPCP:task:* prefix')
		_redis.set(f'ARPCP:task:{task_id}:message', str(message))
		log_print(extent=20, message=f'*:message {message}')
		_redis.set(f'ARPCP:task:{task_id}:caller_ip', str(addr[0]))
		log_print(extent=20, message=f'*:caller_ip {str(addr[0])}')
		_redis.set(f'ARPCP:task:{task_id}:status', default_task_status)
		log_print(extent=20, message=f'*:status {default_task_status}')
		_redis.set(f'ARPCP:task:{task_id}:result', json.dumps(default_result))
		log_print(extent=20, message=f'*:result {default_result}')

		# send OK response
		response = {'code': 100, 'description': 'OK', 'data': {'task_id': task_id, 'result': None}}
		try:
			ARPCP.send_message(sock, response, ARPCP.MT_RES)
		except ARPCPException as e:
			ARPCP.erase_task_from_redis(_redis, task_id)
			log_print(extent=20, message='handle_atask finished with error')
			return
		except Exception as e:
			raise e
		ARPCP.close(sock)

		## 2 part. Procedure executing & sending result
		# import & reload procedures
		try:
			log_print(extent=20, message='procedures reloading..')
			import procedures
			reload(procedures)
		except Exception as e:
			# @TODO update redis status
			error_print(str(e))
			result_message = {'task_id': task_id, 'task_result': None, 'task_status': 'execution_error'}
			ARPCP.call(addr[0], ADDR_CONF[1], 'result', result_message)
			log_print(extent=20, message='handle_task finished with error')
			return

		# execute procedure
		log_print(extent=20,message=f'procedure {remote_procedure} started..')
		# @TODO update redis status
		try:
			remote_procedure_result = getattr(procedures, remote_procedure)(*remote_procedure_args)
		except Exception as e:
			# @TODO update redis status
			error_print(str(e))
			result_message = {'task_id': task_id, 'task_result': None, 'task_status': 'execution_error'}
			ARPCP.call(addr[0], ADDR_CONF[1], 'result', result_message)
			log_print(extent=20, message='handle_task finished with error')
			return
		log_print(extent=20, message='procedure finished')
		# @TODO update redis status

		# send result
		result_message = {'task_id': task_id, 'task_result': remote_procedure_result, 'task_status': 'done'}
		ARPCP.call(addr[0], ADDR_CONF[1], 'result', result_message)

		log_print(extent=20, message='handle_atask finished')

# ==============================================================================

# class RemoteNode:
# 	def __init__(self, remote_host='0.0.0.0', remote_port=7018):
# 		log_print(extent=10, message='initializing RemoteNode..')

# 		self.remote_host = remote_host
# 		self.remote_port = remote_port
# 		self.procedures = self.__procedures(self)

# 		log_print(extent=10, message='RemoteNode initialized')


# 	def call(self, method, headers = {}, additions = {}):
# 		log_print(extent=10, message='RemoteNode.call method started..')
# 		log_print(extent=10, message=f'calling {method} request')

# 		response = ARPCP.call(self.remote_host, self.remote_port, method, headers, additions)
# 		log_print(extent=10,message='RemoteNode.call method finished')

# 		if response['code'] is 100:
# 			return response['data']
# 		else:
# 			raise ARPCPException(response['code'], response['description'])


# 	class __procedures:

# 		def __init__(self, node):
# 			log_print(extent=20, message='downloading remote procedures..')
# 			self.node = node 
# 			self.available_procedures = node.call('procedures')
# 			log_print(extent=20, message='remote procedures downloaded')
# 			log_print(extent=20, message='adding remote procedures to local class..')

# 			for procedure in self.available_procedures:
# 				# add sync procedure to <RemoteNodeInstance>.procedures
# 				sync_procedure = (lambda __self, *__args, __remote_procedure=procedure, **__kwargs:
# 					self.node.call(
# 						'task',
# 						{
# 							'remote_procedure': __remote_procedure,
# 							'remote_procedure_args': __args,
# 							# 'remote_procedure_kwargs': __kwargs
# 						},
# 						additions = __kwargs['additions'] if 'additions' in __kwargs.keys() else {},
# 					))
# 				setattr(self, procedure, types.MethodType( sync_procedure, self ) )

# 				# add async procedure to <RemoteNodeInstance>.procedures
# 				async_procedure = (lambda __self, *__args, __remote_procedure=procedure, **__kwargs:
# 					self.node.call(
# 						'atask',
# 						{
# 							'remote_procedure': __remote_procedure,
# 							'remote_procedure_args': __args,
# 							# 'remote_procedure_kwargs': __kwargs,
# 						},
# 						additions = __kwargs['additions'] if 'additions' in __kwargs.keys() else {},
# 					))

# 				setattr(self, 'async_' + procedure, types.MethodType( async_procedure, self ) )

# 				log_print(extent=20, message=f'remote procedure "{procedure}" added')


# 		def __repr__(self):
# 			return str(self.available_procedures)

# ==============================================================================

class ARPCPServer:
	def __init__(
		self,
		host='0.0.0.0',
		port=7018,
		connection_queue_size=20,
		max_workers_count=100,
		threadname_prefix='ARPCP',
		master_threadname='server',
		worker_threadname='worker',
	):
		log_print(extent=10 ,message='initializing ARPCP server...', end = '')

		self.host = host
		self.port = port
		self.connection_queue_size = connection_queue_size
		self.max_workers_count = max_workers_count
		self.threadname_prefix = threadname_prefix
		self.master_threadname = \
			self.threadname_prefix + ':' + \
			master_threadname
		self.worker_threadname = \
			self.master_threadname + ':' + \
			worker_threadname
		self.sock = None
		self.workers = []

		log_print(extent=10 ,done = True)

	def _setproctitle(self, name):
		if sys.platform in ['linux','linux2']:
			import setproctitle
			setproctitle.setproctitle(name)

	def start(self):
		self._setproctitle(self.master_threadname)
		log_print(extent=10, message=f'{self.master_threadname} starting')

		log_print(extent=10, message='socket preparing..')
		self.sock = ARPCP.socket(self.host, self.port, self.connection_queue_size)
		log_print(extent=10, message='socket ready')

		log_print(extent=10, message='eventloop starting')
		while True:
			try:
				conn, addr = ARPCP.accept(self.sock)
				log_print(extent=10, message=str('-'*25 + ' connection accepted ' + '-'*25))
				worker = th.Thread(target=self.worker, args=(conn, addr,))
				worker.daemon = True
				worker.start()
			except (socket.timeout, BlockingIOError):
				pass


	def worker(self, conn, addr):
		self._setproctitle(self.worker_threadname)
		log_print(extent=10,message=f'{self.worker_threadname} started')

		ARPCP.handle(conn, addr)

		log_print(extent=10, message=f'{self.worker_threadname} stopped')

# ==============================================================================

if __name__ == '__main__':
	try:
		log_print(extent=10 ,message='ARPCPServer starting')
		arpcp_server = ARPCPServer(**SERVER_CONFIGS)
		arpcp_server.start()
	except KeyboardInterrupt as e:
		log_print(extent=10 ,message='Ctrl^C interrupt handling')
