import socket
import sys, os
sys.path.append(os.path.abspath(os.path.join('..', 'arpcp')))
from __arpcp import Arpcp

LOG = True
ADDR = ("127.0.0.1", 51099)

def log_print(string):
	if LOG:
		print("[LOG] " + string)

class Arpcp_controller_client(object):
	def __init__(self, host = '127.0.0.1', port = 51099, client_name = 'Arpcp_client'):
		self._host = host
		self._port = port
		self._client_name = client_name

	def send_message_to_agent(self, message): # Change method name
		cmd_out = os.popen("arp -a").read()
		line_arr = cmd_out.split('\n')

		# print(cmd_out)
		print(line_arr)

		ip_adresses = [i.split()[0] for i in line_arr[3:] if len(i) > 0]
		print(ip_adresses)
		for ADDR in ip_adresses:
			try:
				log_print('socket object creating..')
				client_sock = Arpcp.create_socket(side = 'client')
				log_print('socket object created')
				log_print('Connecting to server..')
				client_sock.settimeout(1)
				client_sock.connect((ADDR, 51099))
				log_print('Connected to server')
			except Exception as e:
				print('Server connection failed', e)
				continue
			write_socketfile, read_socketfile = Arpcp.make_socket_files(client_sock, buffering=None)

			# Проверка сообщения
			try:
				message = Arpcp.input_string_to_arpcp_format(message)
			except:
				pass
			log_print('sending message..')
			self.send_message(write_socketfile, message)
			log_print('message sended')
			write_socketfile.close()
			log_print('write_socketfile closed')
			log_print('waiting for message..')
			response = self.read_message(read_socketfile)
			log_print('message readed')
			print(response)
			read_socketfile.close()
			log_print('read_socketfile closed')

	def read_message(self, read_socketfile):
		return Arpcp.read_request(read_socketfile)

	def send_message(self, write_socketfile, message):
		Arpcp.send_message(write_socketfile, message)

	def main(self, message):
		log_print('Client script starting')
		self.send_message_to_agent(message)
		log_print('Client script done')



#Исправить, убрать input()

if __name__ == '__main__':
	client = Arpcp_controller_client(host = ADDR[0], port = ADDR[1])
	client.main(input())
else:  
	client = Arpcp_controller_client(host = ADDR[0], port = ADDR[1])
	if len(sys.argv) > 1:
		args = ' '.join(sys.argv[1:])
	else:
		pass
	client.main(args)

if LOG:
	log_print('press Enter to close window')
	input()


