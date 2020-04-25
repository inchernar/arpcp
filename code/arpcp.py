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
import setproctitle
import threading as th
from importlib import reload

import procedures


VERSION = '0.3'
LOG = True
ERROR = True
REDIS_CLIENT = redis.Redis(host = '127.0.0.1', port = 6379)


proto = {
	'request': {
		'requires': ['method', 'version'],
		'methods': {
			'procedures': [],
			'id': [],
			'task': ['remote_procedure_args'],
			'atask': []
		}
	},
	'response': {
		'requires': ['code', 'description', 'data'],
	}
}


def log_print(message):
	if LOG:
		print(f"[{time.ctime()}] {message}")

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
		with open(config_file) as c:
			self.config = yaml.safe_load(c)

# ==============================================================================

class ARPCPException(Exception):
	def __init__(self, errno, errmsg):
		self.args = (errno, errmsg)
		self.errno = errno
		self.errmsg = errmsg

	@staticmethod
	def handle_bad_request_exception(sock, e):
		if type(e) is ARPCPException:
			error_print(str(e))
			error_response = {'code': e.errno, 'description': e.errmsg, 'data': None}
			ARPCP.send_message(sock, error_response, ARPCP.MT_RES)
			traffic_print(error_response, ARPCP.MT_RES)
			ARPCP.close(sock)
		else:
			error_response = {'code': 300, 'description': 'internal server error', 'data': None}
			ARPCP.send_message(sock, error_response, ARPCP.MT_RES)
			traffic_print(error_response, ARPCP.MT_RES)
			ARPCP.close(sock)

# ==============================================================================

class ARPCP:

	# ----- arpcp constants ----------------------------------------------------

	MT_REQ = 0
	MT_RES = 1

	# ----- low-level methods for processing a connection ----------------------

	@staticmethod
	def socket(local_host, local_port, connection_queue_size, timeout = 0.1):
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		sock.bind((local_host, local_port,))
		sock.listen(connection_queue_size)
		sock.settimeout(timeout) # setblocking(False) <-> settimeout(0)
		return sock

	@staticmethod
	def accept(sock):
		conn, addr = sock.accept()
		return conn, addr

	@staticmethod
	def close(sock):
		sock.close()

	@staticmethod
	def connect(remote_host, remote_port, timeout = 30):
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.settimeout(30)
		sock.connect((remote_host, remote_port,))
		return sock

	# ----- methods for receiving and sending arpcp messages -------------------

	@staticmethod
	def parse_message(message, message_type):
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
					raise ARPCPException(202, f'method {method} is unsupported')
				if not set(method_headers).issubset(set(message.keys())):
					raise ARPCPException(203, f'request message for "{method}" has no required headers for that method')
			else:
				raise ARPCPException(201, 'request message has no required headers')
		else:
			pass
		return message

	@staticmethod
	def receive_message(sock, message_type):
		with sock.makefile("rb") as socketfile:
			message = socketfile.readline()
		message = ARPCP.parse_message(message, message_type)
		return message

	@staticmethod
	def serialize_message(message, message_type):
		return (json.dumps(message)+'\r\n').encode('UTF-8')

	@staticmethod
	def send_message(sock, message, message_type):
		message = ARPCP.serialize_message(message, message_type)
		with sock.makefile("wb") as socketfile:
			socketfile.write(message)

	# ----- high-level client-side methods for call arpcp methods --------------

	@staticmethod
	def call(remote_host, remote_port, method, headers = {}):
		sock = ARPCP.connect(remote_host, remote_port)
		message = {'method': method, 'version': VERSION}
		message.update(headers)
		ARPCP.send_message(sock, message, ARPCP.MT_REQ)
		return ARPCP.receive_message(sock, ARPCP.MT_RES)

	# ----- high-level server-side methods for handling arpcp methods ----------

	@staticmethod
	def handle(sock, addr):
		try:
			request = ARPCP.receive_message(sock, ARPCP.MT_REQ)
			traffic_print(request, ARPCP.MT_REQ)
			getattr(ARPCP, f'handle_{request["method"]}')(sock, addr, request)
		except Exception as e:
			ARPCPException.handle_bad_request_exception(sock ,e)

	@staticmethod
	def handle_procedures(sock, addr, message):
		available_procedures = []
		try:
			reload(procedures)
			available_procedures = list(filter(lambda x: not x.startswith('_'), dir(procedures)))
		except:
			pass
		response = {'code': 100, 'description': 'OK', 'data': available_procedures}
		ARPCP.send_message(sock, response, ARPCP.MT_RES)
		traffic_print(response, ARPCP.MT_RES)
		ARPCP.close(sock)

	# @staticmethod
	# def handle_id(sock, addr, message):
	# 	response = {'code': 100, 'description': 'OK', 'data': uuid.getnode()}
	# 	ARPCP.send_message(sock, response, ARPCP.MT_RES)
	# 	traffic_print(response, ARPCP.MT_RES)
	# 	ARPCP.close(sock)

	@staticmethod
	def handle_task(sock, addr, message):
		try:
			reload(procedures)
			try:
				remote_procedure_result = getattr(procedures, message['remote_procedure'])(*message['remote_procedure_args'])
			except Exception as e:
				raise ARPCPException(301, str(e))
			response = {'code': 100, 'description': 'OK', 'data': str(remote_procedure_result)}
			ARPCP.send_message(sock, response, ARPCP.MT_RES)
			traffic_print(response, ARPCP.MT_RES)
			ARPCP.close(sock)
		except Exception as e:
			ARPCPException.handle_bad_request_exception(sock, e)

# ==============================================================================

class RemoteNode:
	def __init__(self, remote_host='0.0.0.0', remote_port=7018):
		self.remote_host = remote_host
		self.remote_port = remote_port
		self.procedures = self.__procedures(self)

	def call(self, method, headers = {}):
		method_response = ARPCP.call(self.remote_host, self.remote_port, method, headers)
		if method_response['code'] is 100:
			return method_response['data']
		else:
			raise ARPCPException(method_response['code'], method_response['description'])

	class __procedures:
		def __init__(self, node):
			self.node = node
			self.available_procedures = node.call('procedures')
			for procedure in self.available_procedures:
				# add sync procedure to <RemoteNodeInstance>.procedures
				sync_procedure = (lambda __self, *__args, __remote_procedure=procedure: #, **__kwargs:
					self.node.call(
						'task',
						{
							'remote_procedure': __remote_procedure,
							'remote_procedure_args': __args
							# 'remote_procedure_kwargs': __kwargs
						}
					))
				setattr(self, procedure, types.MethodType( sync_procedure, self ) )

				# add async procedure to <RemoteNodeInstance>.procedures
				async_procedure = (lambda __self, *__args, __remote_procedure=procedure: #, **__kwargs:
					self.node.call(
						'atask',
						{
							'remote_procedure': __remote_procedure,
							'remote_procedure_args': __args
							# 'remote_procedure_kwargs': __kwargs
						}
					))
				setattr(self, 'async_' + procedure, types.MethodType( async_procedure, self ) )

				# exec('\n'.join([
				# 	f'def {procedure}(self, *args, **kwargs):',
				# 	f'	return self.node.call("task", {{"remote_procedure": "{procedure}"}})',
				# 	f'setattr(self, "{procedure}", types.MethodType( {procedure}, self ))'
				# ]))

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
		log_print('initializing')
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
		log_print('initialized')

	def start(self):
		setproctitle.setproctitle(self.master_threadname)
		log_print(f'{self.master_threadname} starting')

		log_print('socket preparing')
		self.sock = ARPCP.socket(self.host, self.port, self.connection_queue_size)
		log_print('socket prepared')

		log_print('eventloop starting')
		while True:
			try:
				conn, addr = ARPCP.accept(self.sock)
				log_print('-'*25 + ' connection accepted ' + '-'*25)
				worker = th.Thread(target=self.worker, args=(conn, addr,))
				worker.daemon = True
				worker.start()
			except (socket.timeout, BlockingIOError) as e:
				pass

	def worker(self, conn, addr):
		setproctitle.setproctitle(self.worker_threadname)
		# log_print(f'{self.worker_threadname} started')

		ARPCP.handle(conn, addr)

		# log_print('connection closed')
		# log_print(f'{self.worker_threadname} stopped')

# ==============================================================================

if __name__ == '__main__':
	try:
		log_print('ARPCPServer starting')
		arpcp_server = ARPCPServer(**ConfigReader('arpcp.conf.yml').config['server'])
		arpcp_server.start()
	except KeyboardInterrupt as e:
		log_print('Ctrl^C interrupt handling')
