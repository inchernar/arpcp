import socket

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
    def create_socket(cls):
        try:
            arpcp_socket = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM,
                # proto=0
            )
            return arpcp_socket
        except socket.error:
            print('Failed to create socket')

    @classmethod
    def make_socket_file(cls, conn, mode = "rwb", buffering = 0):
        return conn.makefile("rwb", buffering=0)

    @classmethod
    def parse_request_to_arpcp_format(cls, socketfile):
        arpcp_dict_message = {}
        cls.parse_starting_line(socketfile, arpcp_dict_message)
        cls.parse_headers(socketfile, arpcp_dict_message)
        # body_line = cls.parse_body(socketfile)
        # return starting_line, headers, body_line
        return arpcp_dict_message

    @classmethod
    def parse_starting_line(cls, socketfile, arpcp_dict_message):
        purpose_word, p_version = socketfile.readline().decode('UTF-8').replace('\n','').split()
        if purpose_word not in cls.__purpose_words:
            raise 'Method {} not exist'.format(purpose_word)
        if p_version != 'ARPCP/{}'.format(cls.__p_version):
            raise 'Uncorrect version of arcpcp. You have {} instead {}'.format(p_version,cls.__p_version)
        arpcp_dict_message['purpose_word'] = purpose_word
        arpcp_dict_message['p_version'] = p_version

    @classmethod
    def parse_headers(cls, socketfile, arpcp_dict_message):
        while True:
            line = socketfile.readline().decode('UTF-8')
            if line in ('\r\n', '\n', '', '-\n'):
                # завершаем чтение заголовков
                break
            splited_line = line.split()
            if splited_line[0] in cls.__headers_and_definitions.keys():
                if splited_line[0] == 'remote-func-arg':
                    if arpcp_dict_message.get('remote-func-arg') == None:
                        arpcp_dict_message['remote-func-arg'] = {}
                    arpcp_dict_message['remote-func-arg'][splited_line[1]] = splited_line[2].replace('\n','')
                else:
                    arpcp_dict_message[splited_line[0]] = splited_line[1].replace('\n','')

    # @classmethod
    # def parse_body(cls, socketfile):
    #     body_line = b''
    #     while True:
    #         line = socketfile.readline()
    #         if line in (b'\r\n', b'\n', b''):
    #             break
    #         print(line)
    #         body_line += line
    #     return body_line.decode('UTF-8')

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
        
        return arpcp_dict_message

    @classmethod
    def send_message(cls, arpcp_dict_message):
        message = ''
        for key_word, definition in arpcp_dict_message.items():
            if key_word == 'purpose_word' and arpcp_dict_message['purpose_word'] in cls.__purpose_words:
                message += definition
            elif key_word == 'p_version':
                message += ' ARPCP/{}\n'.format(definition)
            elif key_word == 'remote-func-arg':
                for i ,arg in definition.items():
                    message += '{} {} {}\n'.format(key_word, i, arg)
            elif key_word in cls.__headers_and_definitions:
                message += '{} {}\n'.format(key_word, definition)
            else:
                pass
        return message


# m = Arpcp.input_string_to_arpcp_format('TASK my_func 1 key args')
# print(Arpcp.send_message(m))

# a = Arpcp.parse_request_to_arpcp_format()
# print(a)