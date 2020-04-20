import os
import sys
import time
import yaml
import uuid
import threading
import setproctitle
import threading as th
import multiprocessing as mp
import redis
import socket

sys.path.append(os.path.abspath(os.path.join('..', 'arpcp')))
from __arpcp import Arpcp

import procedures
from procedures import *


LOG = True
REDIS_CLIENT = redis.Redis(host = '127.0.0.1', port = 6379)

def log_print(string = None):
    try:
        if LOG:
            print("[LOG] " + string)
    except:
        print('!!!Uncorrect logging!!!')
        
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
    def __init__(
        self,
        host = 'localhost',
        port = 51099,
        connection_queue_size=1,
        workers_count=1,
        procname_prefix='ARPCP',
        server_procname = 'Server',
        worker_procname='worker',
    ):
        log_print('ARPCPServer initializing')
        # configuration variables
        self.host = host
        self.port = port
        self.connection_queue_size = connection_queue_size
        self.workers_count = workers_count
        self.procname_prefix = procname_prefix
        self.server_procname = server_procname
        self.worker_procname = worker_procname
        self.modules = self.load_modules()
        log_print('ARPCPServer initialized')

    def start(self):
        log_print('ARPCPServer starting')
        try:
            server_procname = \
                self.procname_prefix + ':' + \
                self.server_procname
            setproctitle.setproctitle(server_procname)
        except:
            log_print("Warning! Can't change main process name")
        
        arpcp_socket = Arpcp.create_socket()
        log_print('socket object created')
        try:
            self.prepare_socket(arpcp_socket)
            workers = Workers(self.workers_count)
            workers.create(self.worker_serves, arpcp_socket)
            workers.start()
            log_print('ARPCPServer started')
            workers.join()
        finally:
            arpcp_socket.close()

    def load_modules(self):
        # Сделать проверку на наличие модулей
        log_print('preparing modules with procedures')
        modules = []
        for module in procedures.__all__:
            modules.append(getattr(procedures, module))
        log_print('modules with procedures is loaded')
        return modules

    def prepare_socket(self, arpcp_socket):
        log_print('TCP socket preparing')
        arpcp_socket.bind((self.host, self.port,))
        arpcp_socket.listen(self.connection_queue_size)
        arpcp_socket.setblocking(False)
        log_print('TCP socket prepared. Binded to {}:{}'.format(str(self.host), str(self.port)))

    def worker_serves(self, arpcp_socket):
        try:
            worker_procname = \
                self.procname_prefix + ':' + \
                self.server_procname + ':' + \
                self.worker_procname + '[' + str(mp.current_process().pid) + ']'
            setproctitle.setproctitle(worker_procname)
        except:
            log_print("Warning! Can't change worker thread name")

        log_print('start serving')
        while True:
            try:
                conn, client_address = arpcp_socket.accept() # Соединение с клиентом
                log_print('connection accepted')

                write_socketfile, read_socketfile = Arpcp.make_socket_files(conn, buffering = None)
                log_print('socket file created')

            except socket.error:
                print('No clients')
            except KeyboardInterrupt:
                arpcp_socket.close()
                break 
            else:
                log_print('waiting for message')
                try:
                    # timer = threading.Timer(10.0, log_print)
                    # timer.start()
                    conn.settimeout(4.0)
                    arpcp_dict_message = self.read_message(read_socketfile)
                    # timer.cancel()
                except Exception as e:
                    log_print('time out')
                    read_socketfile.close()
                    self.send_message(write_socketfile, {'code': '400'})
                    write_socketfile.close()
                else:
                    log_print('message readed')
            
                    read_socketfile.close()
                    log_print('read_socket closed')

                    print()
                    print("=====CONNECTION=======================================")
                    print("Client: " + str(client_address[0]) + ":" + str(client_address[1]))
                    print("Data:\r\n" + str(arpcp_dict_message))
                    print("======================================================")
                    print()

                    if arpcp_dict_message['purpose_word'] == 'TASK':
                        log_print('TASK request')
                        self.task_request(arpcp_dict_message, write_socketfile)
                    elif arpcp_dict_message['purpose_word'] == 'ATASK':
                        log_print('ATASK request')
                        self.atask_request(arpcp_dict_message, write_socketfile)
                    elif arpcp_dict_message['purpose_word'] == 'GET':
                        log_print('GET request')
                        self.get_request(arpcp_dict_message, write_socketfile)
                    elif arpcp_dict_message['purpose_word'] == 'ECHO':
                        log_print('ECHO request')
                        self.echo_request(arpcp_dict_message, write_socketfile)
                    else:
                        self.send_message(write_socketfile, {"code": "301", "describe": "uncorrect purpose word"})

                    write_socketfile.close()


            # except Exception as e:
            #     print('Client serving failed', e)

# --------------------------------------------------------------------------------
    def task_request(self, arpcp_dict_message, write_socketfile):
        result, success = self.execute_task(arpcp_dict_message['remote-func'])
        if success == True:
            if result != None:
                self.send_message(write_socketfile, {"code": '201', "result": str(result)})
            else:
                self.send_message(write_socketfile, {"code": '202'})
        else:
            self.send_message(write_socketfile, {"code": '303', 'describe': 'uncorrect procedure name'})


    def atask_request(self, arpcp_dict_message, write_socketfile):
        random_key = str(uuid.uuid4())
        self.add_to_redis(random_key, arpcp_dict_message)
        self.send_message(write_socketfile, {"code": "200", "key":random_key})

    def get_request(self, arpcp_dict_message, write_socketfile):
        self.get_from_redis(1)

    def echo_request(self, arpcp_dict_message, write_socketfile):
        self.send_message(write_socketfile, {"code": "100", "mac_addr": uuid.getnode()})

# --------------------------------------------------------------------------------

    def execute_task(self, procedure_name):
        for module in self.modules:
            try:
                result = getattr(module, procedure_name)()
            except AttributeError:
                pass
            else:
                return result, True
        return None, False

    def add_to_redis(self, key, message):
        message = str(message)
        REDIS_CLIENT['ATASK/'+key] = message.encode('UTF-8')
        log_print('{} saved in redis with key: ATASK/{}'.format(message, key))

    def	get_from_redis(self, id):
        pass

    def read_message(self, read_socketfile):
        return Arpcp.read_request(read_socketfile)

    def send_message(self, write_socketfile, message):
        Arpcp.send_message(write_socketfile, message)
        log_print('sended to client:')
        print(message)


    # def do_echo(self, arpcp_socket):
    #     cmd_out = os.popen("arp -a").read()
    #     line_arr = cmd_out.split('\n')

    #     # print(cmd_out)

    #     ip_adresses = [i.split()[0] for i in line_arr[3:] if len(i) > 0]
    #     print(ip_adresses)



if __name__ == '__main__':
    try:
        log_print('Application starting')
        arpcp_server = Arpcp_agent_server(**ConfigReader('arpcp.conf.yml').config['server'])
        arpcp_server.start()
    except KeyboardInterrupt:
        log_print('Application stoping')
        exit(1)