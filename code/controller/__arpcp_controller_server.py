import socket
import sys, os
import threading
# sys.path.append(os.path.abspath(os.path.join('..', 'arpcp')))
# from arpcp import Arpcp


# class Arpcp_controller_server:
#     def __init__(self, host = 'localhost', port = 65431, server_name = 'myServer'):
#         self._host = host
#         self._port = port
#         self._server_name = server_name
    
#     def serve_forever(self):
#         serv_sock = socket.socket(
#             socket.AF_INET,
#             socket.SOCK_STREAM,
#             proto=0
#         )

#         try:
#             serv_sock.bind((self._host, self._port)) # привязать хост+порт
#             serv_sock.listen(2) # очередь из n людей

#             while True:
#                 conn, addr_conn = serv_sock.accept()
#                 socketfile = conn.makefile("rwb", buffering=0)
#                 try:
#                     self.serve_client(conn, socketfile)
#                 except Exception as e:
#                     print('Client serving failed', e)
#         finally:
#             serv_sock.close()

#     def serve_client(self, conn, socketfile):
#         try:
#             starting_line, headers, body = Arpcp.parse_request(conn, socketfile) 
#             print(starting_line) # Вывод!
#             print(headers)
#             print(body)
#             purpose_word, p_version = Arpcp.split_starting_line(starting_line)
#             if purpose_word == 'GET':
#                 pass
#             elif purpose_word == 'EVENT':
#                 pass
#         except ConnectionResetError:
#             conn = None
#         except Exception as e:
#             self.send_error(conn, e)
#         if conn:
#             conn.close()

#     def handle_request(self, req):
#         return 1

#     def send_response(self, conn, resp):
#         return 1

#     def send_error(self, conn, err):
#         return 1


# class Request:
#   def __init__(self, method, target, version):
#     self.method = method
#     self.target = target
#     self.version = version


# server = Arpcp_controller_server()
# server.serve_forever()