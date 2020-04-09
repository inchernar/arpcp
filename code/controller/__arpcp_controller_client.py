import socket
import sys, os
sys.path.append(os.path.abspath(os.path.join('..', 'arpcp')))
from __arpcp import Arpcp


ADDR = ("127.0.0.1", 51099)


class Arpcp_controller_client(object):
    def __init__(self, host = '127.0.0.1', port = 7018, server_name = 'myServer'):
        self._host = host
        self._port = port
        self._server_name = server_name

    def send_message_to_agent(self, message = None): # Change method name
        try:
            client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_sock.connect(ADDR)
            print('Соединился')
        except Exception as e:
            print('Server connection failed', e)
        write_socketfile, read_socketfile = Arpcp.make_socket_files(client_sock, buffering=None)
        if message == None:
            message = Arpcp.input_string_to_arpcp_format(input())
        else:
            message = Arpcp.input_string_to_arpcp_format(message)
        self.send_message(write_socketfile, message)
        write_socketfile.write('ping\r\n'.encode('UTF-8'))
        write_socketfile.close()
        response = self.read_message(read_socketfile)
        print(response)
        read_socketfile.close()

    def read_message(self, read_socketfile):
        return Arpcp.read_request(read_socketfile)

    def send_message(self, write_socketfile, message):
        Arpcp.send_message(write_socketfile, message)

client = Arpcp_controller_client()

# client.send_message_to_agent(message='task need you')
client.send_message_to_agent()

input()
# if __name__ == "__main__":
#     client.send_message_to_agent(Arpcp.send_message(Arpcp.input_string_to_arpcp_format(input())))