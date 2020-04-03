import os
import sys
import time
import yaml
import threading
sys.path.append(os.path.abspath(os.path.join('..', 'arpcp')))
from __arpcp import Arpcp
import setproctitle
import threading as th
import multiprocessing as mp

BASE_ADDRESS = ('0.0.0.0', 65431,)
WORKERS_COUNT = 5
QUEUE_SIZE = 1
LOG = True

def log_print(string):
	if LOG:
		print("[LOG] " + string)
		
class ConfigReader:
	def __init__(self, config_file):
		with open(config_file) as c:
			self.config = yaml.safe_load(c)

class Workers:
	def __init__(self, count):
		log_print('Workers.__init__()')
		self.count = count
		self.workers = []

	def create(self, target, sock):
		log_print('Workers.create()')
		for i in range(self.count):
			worker = threading.Thread(target=target, args=(sock,))
			worker.name = "Worker " + str(i)
			worker.daemon = True
			self.workers.append(worker)

	def start(self):
		log_print('Workers.start()')
		for worker in self.workers:
			log_print("worker '" + worker.name + "' starts")
			worker.start()

	def join(self):
		log_print('Workers.join()')
		for worker in self.workers:
			worker.join()

class Arpcp_agent_server:
	def __init__(self, host = 'localhost', port = 65431, server_name = 'myServer'):
		log_print('Arpcp_agent_server.__init__()')
		self._host = host
		self._port = port
		self._server_name = server_name

	def start(self):
		log_print('Arpcp_agent_server.start()')
		arpcp_socket = Arpcp.create_socket()
		log_print('socket object created')
		try:
			arpcp_socket.bind((self._host, self._port))
			log_print('socket object binded to {}:{}'.format(str(self._host), str(self._port)))

			arpcp_socket.listen(QUEUE_SIZE)
			log_print('socket object listen connections. QUEUE_SIZE = {}'.format(str(QUEUE_SIZE)))

			workers = Workers(WORKERS_COUNT)
			workers.create(self.worker_serves, arpcp_socket)
			workers.start()
			log_print('main thread join threads')
			workers.join()
		finally:
			arpcp_socket.close()

	def worker_serves(self, arpcp_socket):
		log_print('start serving')
		while True:
			conn, client_address = arpcp_socket.accept() # Соединение с клиентом
			log_print('connection accepted')

			write_socketfile, read_socketfile = Arpcp.make_socket_files(conn, buffering = None)
			log_print('socket file created')

			try:
				self.serve_client(conn, client_address, write_socketfile, read_socketfile)
			except Exception as e:
				print('Client serving failed', e)

	def serve_client(self, conn, client_address, write_socketfile, read_socketfile):
		try:
			arpcp_dict_message = self.read_message(read_socketfile)
			log_print('message readed')
			
			read_socketfile.close()
			log_print('read_socket closed')

			print()
			print("=====CONNECTION=======================================")
			print("Client: " + str(client_address[0]) + ":" + str(client_address[1]))
			print("Data:\r\n" + str(arpcp_dict_message))
			print("======================================================")
			print()
			time.sleep(10)
			self.send_message(write_socketfile, {"task":"200"})
			write_socketfile.close()

		except ConnectionResetError:
			conn = None
		# except Exception as e:
			# self.send_error(conn, e)
		if conn:
			conn.close()

	def create_async_task(self, starting_line, headers):
		# Здесь нужно будет связать с БД и сохранить там данные об этой нерешенной задаче.
		return 1

	def send_response(self, conn, result_of_task):
		# Здесь нужно отправить ответ о выполненной синхронной задаче
		return 1

	# err = result_of_task
	def send_error(self, conn, err):
		# Здесь нужно отправить ответ с информацией об ошибке синхронной задачи
		return 1

	def read_message(self, read_socketfile):
		return Arpcp.read_request(read_socketfile)

	def send_message(self, write_socketfile, message):
		Arpcp.send_message(write_socketfile, message)


def main():
	server = Arpcp_agent_server()
	log_print('server created')
	server.start()

if __name__ == '__main__':
	try:
		log_print('app starting')
		main()
	except KeyboardInterrupt:
		log_print('app stoping')
		exit(1)
