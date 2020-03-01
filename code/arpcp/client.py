import socket

class Arpcp:
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
    def split_starting_line(cls, line):
        purpose_word, p_version = line.split(' ', maxsplit = 1)
        return purpose_word, p_version

    @classmethod
    def parse_request(cls, socketfile):
        starting_line = cls.parse_starting_line(socketfile)
        headers = cls.parse_headers(socketfile)
        body_line = cls.parse_body(socketfile)
        return starting_line, headers, body_line

    @classmethod
    def parse_starting_line(cls, socketfile):
        line = socketfile.readline()
        return line.decode('UTF-8').replace('\n','')

    @classmethod
    def parse_headers(cls, socketfile):
        headers = {}
        while True:
            line = socketfile.readline()
            if line in (b'\r\n', b'\n', b'', b'-\n'):
                # завершаем чтение заголовков
                break
            splited_line = line.split(b': ')
            headers[splited_line[0].decode('UTF-8')] = (splited_line[1].decode('UTF-8')).replace('\n','')
        return headers

    @classmethod
    def parse_body(cls, socketfile):
        body_line = b''
        while True:
            line = socketfile.readline()
            if line in (b'\r\n', b'\n', b''):
                break
            print(line)
            body_line += line
        return body_line.decode('UTF-8')