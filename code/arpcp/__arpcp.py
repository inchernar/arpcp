import socket
import json

class Arpcp:
    
    __purpose_words = ['ATASK', 'TASK', 'GET', 'ECHO', 'SIGNAL']
    __p_version = '0.1'
    # Добавить значения
    __headers_and_definitions = {
        'remote-func' : 0,
        'remote-func-arg' : 0,
        'task-id' : 0,
        'task-status' : 0,
        }

    @classmethod
    def create_socket(cls, side = 'server'):
        try:
            arpcp_socket = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM,
                # proto=0
            )
            if side == 'server':
                arpcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            return arpcp_socket
        except socket.error:
            print('Failed to create socket')

    @classmethod
    def make_socket_files(cls, conn, buffering = None):
        return conn.makefile("wb", buffering), conn.makefile("rb",buffering)

    @classmethod
    def read_request(cls, socketfile):
        return json.loads(socketfile.readline().decode('UTF-8'))

    @classmethod
    def input_string_to_arpcp_format(cls, input_string):
        input_string = input_string.split()
        purpose_word = input_string[0].upper()
        if purpose_word not in cls.__purpose_words:
            raise 'Method {} not exist'.format(purpose_word)
        arpcp_dict_message = {}

        if purpose_word in ['TASK','ATASK']:
            arpcp_dict_message['purpose_word'] = purpose_word
            arpcp_dict_message['p_version'] = cls.__p_version
            arpcp_dict_message['remote-func'] = input_string[1]
            if len(input_string) > 2:
                arpcp_dict_message['remote-func-arg'] = {}
            for i in list(range(2, len(input_string))):
                arpcp_dict_message['remote-func-arg'][str(i-2)] = input_string[i]
        elif purpose_word == 'ECHO':
            arpcp_dict_message['purpose_word'] = purpose_word
            arpcp_dict_message['p_version'] = cls.__p_version
            
        return arpcp_dict_message

    @classmethod
    def send_message(cls, socketfile, arpcp_dict_message):
        # socket
        socketfile.write((json.dumps(arpcp_dict_message)+'\r\n').encode('UTF-8'))
        



# m = Arpcp.input_string_to_arpcp_format('TASK my_func 1 key args')
# print(Arpcp.send_message(m))

# a = Arpcp.parse_request_to_arpcp_format()
# print(a)