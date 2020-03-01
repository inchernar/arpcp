import socket
ADDR = ("localhost", 65431)

class Arpcp_agent_client(object):
    def __init__(self, host = 'localhost', port = 65431, server_name = 'myServer'):
        self._host = host
        self._port = port
        self._server_name = server_name

    def send_message_to_controller(self, message = 'hello world'): # Change method name
        try:
            client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_sock.connect(ADDR)
        except Exception as e:
            print('Server connection failed', e)
        socketfile = client_sock.makefile("rwb", buffering=0)
        self.send_message(socketfile, message)
        socketfile.close()

    def send_message(self, socketfile, message):
        socketfile.write(message.encode('UTF-8'))

client = Arpcp_agent_client()
client.send_message_to_controller( message = '''GET ARPCP/0.1
WAT?: this is EXAMPLE
YOU ARE: NO
I am: YES
GO to: ROCK SAFARI 9.0
-
plz do someone
or not do someone
it's does not matter
I have point about that
''')
