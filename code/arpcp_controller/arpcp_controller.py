import socket
import sys

class Arpcp_controller_server:
    def __init__(self, host = 'localhost', port = 65431, server_name = 'myServer'):
        self._host = host
        self._port = port
        self._server_name = server_name

    def serve_forever(self):
        serv_sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
            proto=0
        )

        try:
            serv_sock.bind((self._host, self._port)) # привязать хост+порт
            serv_sock.listen(2) # очередь из n людей

            while True:
                conn, addr_conn = serv_sock.accept()
                socketfile = conn.makefile("rwb", buffering=0)
                try:
                    self.serve_client(conn, socketfile)
                except Exception as e:
                    print('Client serving failed', e)
        finally:
            serv_sock.close()

    def serve_client(self, conn, socketfile):
        try:
            req = self.parse_request(conn, socketfile)
            resp = self.handle_request(req)
            self.send_response(conn, resp)
            print(req[0]) # Вывод!
            print(req[1])
            print(req[2])
        except ConnectionResetError:
            conn = None
        except Exception as e:
            self.send_error(conn, e)

        if conn:
            conn.close()

    def parse_request(self, conn, socketfile):
        # method, target, ver = self.parse_request_line(socketfile)
        first_line = self.parse_request_line(socketfile)
        headers = self.parse_headers(socketfile)
        body_line = self.parse_body(socketfile)
        return first_line, headers, body_line

    def parse_request_line(self, socketfile):
        line = socketfile.readline()
        return line

    def parse_headers(self, socketfile):
        headers = {}
        while True:
            line = socketfile.readline()
            if line in (b'\r\n', b'\n', b'', b'-\n'):
                # завершаем чтение заголовков
                break
            splited_line = line.split(b': ')
            headers[splited_line[0]] = splited_line[1]
        return headers

    def parse_body(self, socketfile):
        body_line = b''
        while True:
            line = socketfile.readline()
            if line in (b'\r\n', b'\n', b''):
                # завершаем чтение заголовков
                break
            body_line += line
        return body_line

    def handle_request(self, req):
        return 1

    def send_response(self, conn, resp):
        return 1

    def send_error(self, conn, err):
        return 1


class Request:
  def __init__(self, method, target, version):
    self.method = method
    self.target = target
    self.version = version


server = Arpcp_controller_server()
server.serve_forever()