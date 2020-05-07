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

PLATFORM = sys.platform
if PLATFORM in ['linux','linux2']:
	import setproctitle



VERSION = '0.3'
ERROR = True
REDIS_CLIENT = redis.Redis(host = '127.0.0.1', port = 6379)


# 0,False - without logging
# 10 - necessary logging
# 20 - logging without low-level methods
# 30 - Full logging
LOG = 30

proto = {
	'request': {
		'requires': ['method', 'version'],
		'methods': {
			'procedures': [],
			'id': [],
			'result': ['task_id', 'task_status', 'task_result'],
			'task': ['remote_procedure','remote_procedure_args'],
			'atask': ['remote_procedure','remote_procedure_args'],
			'signal': ['task_id'],
		}
	},
	'response': {
		'requires': ['code', 'description', 'data'],
	}
}


def linux_setproctitle(name):
	if PLATFORM in ['linux','linux2']:
		setproctitle.setproctitle(name)


# ==============================================================================


def log_print(extent,message = None, done = False, end = '\n'):
	if LOG and (LOG >= extent):
		if done:
			print('Done')
		else:
			print(f"[{time.ctime()}] {message}", end = end)

def error_print(message):
	if ERROR:
		print(f"[{time.ctime()}] [ERROR] {message}")

def traffic_print(message, message_type):
	if LOG:
		if message_type is ARPCP.MT_REQ:
			print(f"[{time.ctime()}] <=== {message}")
		elif message_type is ARPCP.MT_RES:
			print(f"[{time.ctime()}] ===> {message}")


# ==============================================================================

class ConfigReader:
	def __init__(self, config_file):
		log_print(extent=20, message='loading config_file...', end = '')
		with open(config_file) as c:
			self.config = yaml.safe_load(c)
		log_print(extent=20, done=True)


SERVER_CONFIGS = ConfigReader('arpcp.conf.yml').config['server']
ADDR_CONF = (SERVER_CONFIGS['host'],SERVER_CONFIGS['port'])

# ==============================================================================

class ARPCPException(Exception):
	def __init__(self, errno, errmsg):
		self.args = (errno, errmsg)
		self.errno = errno
		self.errmsg = errmsg


	@staticmethod
	def handle_exception_while_connection(sock,e):
		if type(e) is ARPCPException:
			log_print(extent=20, message='handle ARPCPException')
			error_print(str(e))
			error_response = {'code': e.errno, 'description': e.errmsg, 'data': None}
			ARPCP.send_message(sock, error_response, ARPCP.MT_RES)
			traffic_print(error_response, ARPCP.MT_RES)
			ARPCP.close(sock)
		else:
			log_print(extent=20, message='handle Exception')
			print(e)
			error_response = {'code': 300, 'description': 'internal server error', 'data': None}
			ARPCP.send_message(sock, error_response, ARPCP.MT_RES)
			traffic_print(error_response, ARPCP.MT_RES)
			ARPCP.close(sock)


	@staticmethod
	def handle_atask_exception_at_runtime(message, addr, e):
		if type(e) is ARPCPException:
			log_print(extent=20, message='handle atask ARPCPException')
			error_print(str(e))
		else:
			log_print(extent=20, message='handle atask Exception')
			print(e)
		response_message = ARPCP.call(addr[0], ADDR_CONF[1], 'result', message)
	

	@staticmethod
	def handle_remote_procedure_execution_exception(e, message):
		if type(e) is ARPCPException:
			log_print(extent=20, message='handle task ARPCPException')
			error_print(str(e))
		else:
			log_print(extent=20, message='handle task Exception')
			print(e)
		# REDIS_CLIENT.set('ARPCP:atask:response:'+message['atask_id']+':message', message['atask_status'])


	# @staticmethod
	# def handle_connection_exception(e):


	@staticmethod
	def handle_signal_exception_at_runtime(parameter_list):
		pass

# ==============================================================================

class ARPCP:

	# ----- arpcp constants ----------------------------------------------------

	MT_REQ = 0
	MT_RES = 1

	# ----- low-level methods for processing a connection ----------------------

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
		log_print(extent=30, message='closing socket', end='')
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
	def parse_message(message, message_type):
		log_print(extent=30, message= 'parsing message...', end='')
		try:
			message = json.loads(message.decode('utf-8'))
		except:
			raise ARPCPException(200, 'bad request')
		if message_type is ARPCP.MT_REQ:
			if set(proto['request']['requires']).issubset(set(message.keys())):
				method = message['method']
				try:
					method_headers = proto['request']['methods'][method]
				except:
					raise ARPCPException(201, f'method {method} is unsupported')
				if not set(method_headers).issubset(set(message.keys())):
					raise ARPCPException(202, f'request message for "{method}" has no required headers for that method')
			else:
				raise ARPCPException(202, 'request message has no required headers')
		elif message_type is ARPCP.MT_RES:
			if not set(proto['response']['requires']).issubset(set(message.keys())):
				raise ARPCPException(202, 'request message has no required headers')

		log_print(extent=30, done=True)
		return message


	@staticmethod
	def receive_message(sock, message_type):
		log_print(extent=30, message='receiving message..')
		with sock.makefile("rb") as socketfile:
			message = socketfile.readline()
		message = ARPCP.parse_message(message, message_type)
		log_print(extent=30, message='message received')
		return message


	@staticmethod
	def serialize_message(message, message_type):
		log_print(extent=30, message='serializing message...', end='')
		result = (json.dumps(message)+'\r\n').encode('UTF-8')
		log_print(extent=30, done=True)		
		return result


	@staticmethod
	def send_message(sock, message, message_type):
		log_print(extent=30, message='sending message..')
		message = ARPCP.serialize_message(message, message_type)
		with sock.makefile("wb") as socketfile:
			socketfile.write(message)
		log_print(extent=30, message='message sended')


	# ----- high-level client-side methods for call arpcp methods --------------


	@staticmethod
	def call(remote_host, remote_port, method, headers = {}, additions = {}):
		log_print(extent=20, message='ARPCP.call method started')
		try:
			message = {'method': method, 'version': VERSION}

			if method in ['task', 'atask']:
				task_id = str(uuid.uuid4())
				headers.update({'task_id': task_id})
				log_print(extent=20, message=f'generated id to task - {task_id}')
				log_print(extent=20, message='saving data in redis with ARPCP:task:<id>:* prefix')
				if 'callback' in additions:
					REDIS_CLIENT.set(f'ARPCP:task:{task_id}:callback', additions['callback'])
					log_print(extent=20, message=f'*:callback {additions["callback"]}')
				message.update(headers)

				dumped_message = json.dumps(message)
				REDIS_CLIENT.set(f'ARPCP:task:{task_id}:message', dumped_message)
				log_print(extent=20, message=f'*:message {message}')

				host_addr = json.dumps({'remote_host': remote_host, 'remote_port': remote_port})
				REDIS_CLIENT.set(f'ARPCP:task:{task_id}:host_addr', host_addr)
				log_print(extent=20, message=f'*:host_addr {host_addr}')
			else:
				message.update(headers)

			sock = ARPCP.connect(remote_host, remote_port)
			traffic_print(message, ARPCP.MT_RES)
			ARPCP.send_message(sock, message, ARPCP.MT_REQ)
			received_message = ARPCP.receive_message(sock, ARPCP.MT_RES)
			traffic_print(received_message, ARPCP.MT_REQ)

			if method in ['task', 'atask'] and \
					received_message['task_status'] == '100' and \
					REDIS_CLIENT.exists(f'ARPCP:task:{task_id}:callback'):
				callback = REDIS_CLIENT.get(f'ARPCP:task:{task_id}:callback')
				log_print(extent=20, message=f'calling callback "{callback}"')
				reload(callbacks)
				callback_result = getattr(callbacks, callback)(received_message['task_result'])
				log_print(extent=20, message=f'callback executed with result "{callback_result}"')
				log_print(extent=20, message='handle_result done')
				return callback_result

			ARPCP.close(sock)
			return received_message
		except Exception as e:
			#Нужно что-то с этим сделать
			print('Ошибка подключаниея')
			raise e

		log_print(extent=20,message=f'response code is {received_message["code"]}. {received_message["description"]}')
		log_print(extent=20, message='ARPCP.call method ended')

		if received_message['code'] is 100:
			# return received_message['data']
			return received_message
		else:
			raise ARPCPException(received_message['code'], received_message['description'])


	# ----- high-level server-side methods for handling arpcp methods ----------


	@staticmethod
	def handle(sock, addr):
		try:
			log_print(extent=20, message='handing request..')
			request = ARPCP.receive_message(sock, ARPCP.MT_REQ)
			traffic_print(request, ARPCP.MT_REQ)
			getattr(ARPCP, f'handle_{request["method"]}')(sock, addr, request)
			log_print(extent=20, message='request handled')
		except Exception as e:
			ARPCPException.handle_exception_while_connection(sock ,e)


	@staticmethod
	def handle_procedures(sock, addr, message):
		log_print(extent=20, message='handle_procedures is called')
		try:
			available_procedures = []
			log_print(extent=20, message='procedures reloading...', end='')
			reload(procedures)
			available_procedures = list(filter(lambda x: not x.startswith('_'), dir(procedures)))
			log_print(extent=20, done=True)
			response = {'code': 100, 'description': 'OK', 'data': available_procedures}
			ARPCP.send_message(sock, response, ARPCP.MT_RES)
			traffic_print(response, ARPCP.MT_RES)
			ARPCP.close(sock)
		except Exception as e:
			ARPCPException.handle_exception_while_connection(sock ,e)

		log_print(extent=20, message='handle_procedures done')


	@staticmethod
	def handle_result(sock, addr, message):
		log_print(extent=20, message='handle_result is called')

		try:
			response = {'code': 100, 'description': 'OK', 'data': 'OK'}
			traffic_print(response, ARPCP.MT_RES)
			ARPCP.send_message(sock, response, ARPCP.MT_RES)
			ARPCP.close(sock)
		except Exception as e:
			ARPCPException.handle_exception_while_connection(sock, e)
		task_id = message['task_id']
		task_result = message['task_result']
		task_status = message['task_status']

		log_print(extent=20, message='saving data in redis with ARPCP:task:* prefix')
		REDIS_CLIENT.set('ARPCP:task:'+task_id+':status', task_status)
		log_print(extent=20, message=f'*:status {task_status}')
		REDIS_CLIENT.set('ARPCP:task:'+task_id+':result', task_result)
		log_print(extent=20, message=f'*:result {task_result}')

		if REDIS_CLIENT.exists(f'ARPCP:task:{task_id}:callback'):
			callback = REDIS_CLIENT.get(f'ARPCP:task:{task_id}:callback')
			log_print(extent=20, message=f'calling callback "{callback}"')
			reload(callbacks)
			callback_result = getattr(callbacks, callback)(task_result)
			log_print(extent=20, message=f'callback executed with result "{callback_result}"')
			log_print(extent=20, message='handle_result done')
			return callback_result
		else:	
			log_print(extent=20, message='handle_result done')
			return task_result


	@staticmethod
	def handle_signal(sock, addr, message):
		log_print(extent=20, message='handle_signal is called')
		try:
			response = {'code': 100, 'description': 'OK', 'data': None}
			ARPCP.send_message(sock, response, ARPCP.MT_RES)
			traffic_print(response, ARPCP.MT_RES)
			ARPCP.close(sock)
		except Exception as e:
			ARPCPException.handle_exception_while_connection(sock, e)

		task_id = message['task_id']
		task_result = (REDIS_CLIENT.get('ARPCP:task:'+task_id+':result')).decode('UTF-8')
		task_status = (REDIS_CLIENT.get('ARPCP:task:'+task_id+':status')).decode('UTF-8')
		result_message = {'task_result': task_result, 'task_status': task_status, 'task_id': task_id}

		response_result_message = ARPCP.call(addr[0], ADDR_CONF[1], 'result', result_message)
		traffic_print(response_result_message, ARPCP.MT_REQ)
		
		log_print(extent=20, message='handle_signal done')


	@staticmethod
	def handle_task(sock, addr, message):
		log_print(extent=20, message='handle_task is called')
		try:
			remote_procedure = message["remote_procedure"]
			remote_procedure_args = message['remote_procedure_args']
			
			log_print(extent=20, message='procedures reloading...', end='')
			reload(procedures)
			log_print(extent=20,done=True)
			try:
				log_print(extent=20,message=f'procedure {remote_procedure} calling..')
				remote_procedure_result = getattr(procedures, remote_procedure)(*remote_procedure_args)
				log_print(extent=20, message='procedure finished')
			except TypeError as e:
				# Неверное количество или тип аргумента
				raise ARPCPException(210, str(e))
			except AttributeError as e:
				# Неверное имя метода
				raise ARPCPException(211, str(e))
			except Exception as e:
				raise ARPCPException(212, str(e))
			response = {'code': 100, 'description': 'OK', 'data': str(remote_procedure_result)}
			ARPCP.send_message(sock, response, ARPCP.MT_RES)
			traffic_print(response, ARPCP.MT_RES)
			ARPCP.close(sock)
			log_print(extent=20, message='handle_task done')
		except Exception as e:
			ARPCPException.handle_exception_while_connection(sock, e)


	@staticmethod
	def handle_atask(sock, addr, message):
		log_print(extent=20, message='handle_atask is called')

		try:
			# atask_id = str(uuid.uuid4())
			task_id = message["task_id"]
			remote_procedure = message["remote_procedure"]
			remote_procedure_args = message['remote_procedure_args']

			default_result = 'None'
			default_task_status = 'created'

			log_print(extent=20, message='saving data in redis with ARPCP:task:* prefix')
			REDIS_CLIENT.set('ARPCP:task:'+task_id+':message', str(message))
			log_print(extent=20, message=f'*:message {message}')
			REDIS_CLIENT.set('ARPCP:task:'+task_id+':caller_ip', str(addr[0]))
			log_print(extent=20, message=f'*:caller_ip {str(addr[0])}')
			REDIS_CLIENT.set('ARPCP:task:'+task_id+':status', default_task_status)
			log_print(extent=20, message=f'*:status {default_task_status}')
			REDIS_CLIENT.set('ARPCP:task:'+task_id+':result', default_result)
			log_print(extent=20, message=f'*:result {default_result}')

			response = {'code': 100, 'description': 'OK', 'data': None}
			ARPCP.send_message(sock, response, ARPCP.MT_RES)
			traffic_print(response, ARPCP.MT_RES)
			ARPCP.close(sock)
		except Exception as e:
			ARPCPException.handle_exception_while_connection(sock, e)

		try:
			log_print(extent=20, message='procedures reloading...', end='')
			reload(procedures)
			log_print(extent=20,done=True)
			try:
				log_print(extent=20,message=f'procedure {remote_procedure} calling..')
				remote_procedure_result = str(getattr(procedures, remote_procedure)(*remote_procedure_args))
				log_print(extent=20, message='procedure finished')
			except TypeError as e:
				# Неверное количество или тип аргумента
				task_status = 'executing_error'
				REDIS_CLIENT.set('ARPCP:task:'+task_id+'saving data in redis *:status', task_status)
				log_print(extent=20, message=f'*:status {task_status}')
				raise ARPCPException(204, str(e))
			except AttributeError as e:
				# Неверное имя метода
				task_status = 'executing_error'
				REDIS_CLIENT.set('ARPCP:task:'+task_id+'saving data in redis *:status', task_status)
				log_print(extent=20, message=f'*:status {task_status}')
				raise ARPCPException(203, str(e))
			except Exception as e:
				task_status = 'executing_error'
				REDIS_CLIENT.set('ARPCP:task:'+task_id+'saving data in redis *:status', task_status)
				log_print(extent=20, message=f'*:status {task_status}')
				raise e

			log_print(extent=20, message='saving result in redis with ARPCP:task:* prefix')

			task_status = 'done'
			REDIS_CLIENT.set('ARPCP:task:'+task_id+':status', task_status)
			log_print(extent=20, message=f'*:status {task_status}')
			REDIS_CLIENT.set('ARPCP:task:'+task_id+':result', remote_procedure_result)
			log_print(extent=20, message=f'*:result {remote_procedure_result}')

			result_message = {
				'task_id': task_id,
				'task_result': remote_procedure_result,
				'task_status': task_status,
				}
		except Exception as e:
			result_message = {
				'task_id': task_id,
				'task_result': None,
				'task_status': task_status,
				}
			ARPCPException.handle_atask_exception_at_runtime(result_message, addr, e)
		else:
			ARPCP.call(addr[0], ADDR_CONF[1], 'result', result_message)
			log_print(extent=20, message='handle_atask done')


# ==============================================================================


class RemoteNode:
	def __init__(self, remote_host='0.0.0.0', remote_port=7018):
		log_print(extent=10, message='initializing RemoteNode..')

		self.remote_host = remote_host
		self.remote_port = remote_port
		self.procedures = self.__procedures(self)

		log_print(extent=10, message='RemoteNode initialized')


	def call(self, method, headers = {}, additions = {}):
		print(additions)
		log_print(extent=10, message='RemoteNode.call method started..')
		log_print(extent=10, message=f'calling {method} request')

		response = ARPCP.call(self.remote_host, self.remote_port, method, headers, additions)

		log_print(extent=10,message='RemoteNode.call method ended')
		return response['data']


	class __procedures:

		def __init__(self, node):
			log_print(extent=20, message='downloading remote procedures..')
			self.node = node 
			self.available_procedures = node.call('procedures')
			log_print(extent=20, message='remote procedures downloaded')
			log_print(extent=20, message='adding remote procedures to local class..')

			for procedure in self.available_procedures:
				# add sync procedure to <RemoteNodeInstance>.procedures
				sync_procedure = (lambda __self, *__args, __remote_procedure=procedure, **__kwargs:
					self.node.call(
						'task',
						{
							'remote_procedure': __remote_procedure,
							'remote_procedure_args': __args,
							# 'remote_procedure_kwargs': __kwargs
						},
						additions = __kwargs['additions'],
					))
				setattr(self, procedure, types.MethodType( sync_procedure, self ) )

				# add async procedure to <RemoteNodeInstance>.procedures
				async_procedure = (lambda __self, *__args, __remote_procedure=procedure, **__kwargs:
					self.node.call(
						'atask',
						{
							'remote_procedure': __remote_procedure,
							'remote_procedure_args': __args,
							# 'remote_procedure_kwargs': __kwargs,
						},
						additions = __kwargs['additions'],
					))

				setattr(self, 'async_' + procedure, types.MethodType( async_procedure, self ) )

				log_print(extent=20, message=f'remote procedure "{procedure}" added')


		def __repr__(self):
			return str(self.available_procedures)

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


	def start(self):
		linux_setproctitle(self.master_threadname)
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
		linux_setproctitle(self.worker_threadname)
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
