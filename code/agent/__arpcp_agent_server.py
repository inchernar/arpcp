import sys
import threading
import sys, os
sys.path.append(os.path.abspath(os.path.join('..', 'arpcp')))
from arpcp.__arpcp import Arpcp


class Arpcp_agent_server:
    def __init__(self, host = 'localhost', port = 65431, server_name = 'myServer'):
        self._host = host
        self._port = port
        self._server_name = server_name
    

    def serve_forever(self):
        arpcp_socket = Arpcp.create_socket()

        try:
            arpcp_socket.bind((self._host, self._port)) # привязать хост+порт
            arpcp_socket.listen(2) # очередь из n людей

            while True:
                conn, addr_conn = arpcp_socket.accept() # Соединение с клиентом
                socketfile = conn.makefile("rwb", buffering=0) # Оболочка над сокетом в виде файла
                try:
                    self.serve_client(conn, socketfile)
                except Exception as e:
                    print('Client serving failed', e)
        finally:
            arpcp_socket.close()

    def serve_client(self, conn, socketfile):
        try:
            starting_line, headers, body = Arpcp.parse_request(socketfile) 
            # print(starting_line) # Вывод!
            # print(headers)
            # print(body)
            if 'Async' in headers.keys() and headers['Async']:
                self.create_async_task(starting_line, headers, body)
            else:
                # successful_execution содержит True в случае успеха, False в противном случае. 
                # result_of_task содержит результат выполнения задачи(может быть пустой) или код ошибки. 
                successful_execution, result_of_task = self.perform_sync_task(starting_line, headers, body)
                if successful_execution:
                    self.send_response(conn, result_of_task)
                    
                    socketfile.write('Solved!'.encode('UTF-8')) # Это пример отправки ответа
                
                else:
                    self.send_error(conn, result_of_task)
        except ConnectionResetError:
            conn = None
        # except Exception as e:
            # self.send_error(conn, e)
        if conn:
            conn.close()

    def perform_sync_task(self, starting_line, headers, body):
        purpose_word, p_version = Arpcp.split_starting_line(starting_line)
        if purpose_word == 'TASK':
            pass
        elif purpose_word == 'GET':
            pass
        elif purpose_word == 'ECHO':
            pass
        elif purpose_word == '...':
            pass
        [...]
        return True, None

    def create_async_task(self, starting_line, headers, body):
        # Здесь нужно будет связать с БД и сохранить там данные об этой нерешенной задаче.
        return 1

    def send_response(self, conn, result_of_task):
        # Здесь нужно отправить ответ о выполненной синхронной задаче
        return 1

    # err = result_of_task
    def send_error(self, conn, err):
        # Здесь нужно отправить ответ с информацией об ошибке синхронной задачи
        return 1




server = Arpcp_agent_server()
server.serve_forever()