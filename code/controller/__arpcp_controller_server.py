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

sys.path.append(os.path.abspath(os.path.join('..', 'arpcp')))
from __arpcp import Arpcp



LOG = True
REDIS_CLIENT = redis.Redis(host = '127.0.0.1', port = 6379)

def log_print(string):
    if LOG:
        print("[LOG] " + string)
        
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
        workers_count=2,
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
        log_print('ARPCPServer initialized')

    def start(self):
        log_print('ARPCPServer starting')
        server_procname = \
            self.procname_prefix + ':' + \
            self.server_procname
        setproctitle.setproctitle(server_procname)

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

    def prepare_socket(self, arpcp_socket):
        log_print('TCP socket preparing')
        arpcp_socket.bind((self.host, self.port,))
        arpcp_socket.listen(self.connection_queue_size)
        log_print('TCP socket prepared. Binded to {}:{}'.format(str(self.host), str(self.port)))

    def worker_serves(self, arpcp_socket):
        worker_procname = \
            self.procname_prefix + ':' + \
            self.server_procname + ':' + \
            self.worker_procname + '[' + str(mp.current_process().pid) + ']'
        setproctitle.setproctitle(worker_procname)
        log_print('start serving')
        while True:
            conn, client_address = arpcp_socket.accept() # Соединение с клиентом
            log_print('connection accepted')

            write_socketfile, read_socketfile = Arpcp.make_socket_files(conn, buffering = None)
            log_print('socket file created')

            try:
                arpcp_dict_message = self.read_message(read_socketfile)
                log_print('message readed')
        
                read_socketfile.close()
                log_print('read_socket closed')

                print()
                print("=====CONNECTION=======================================")
                print("Client: " + str(client_address[0]) + ":" + str(client_address[1]))
                print("Data:\r\n" + str(arpcp_dict_message))
                print("======================================================")
                print()

                # if arpcp_dict_message['purpose_word'] == 'TASK':
                # 	log_print('TASK request')
                # 	self.task_request(arpcp_dict_message, write_socketfile)
                # elif arpcp_dict_message['purpose_word'] == 'ATASK':
                # 	log_print('ATASK request')
                # 	self.atask_request(arpcp_dict_message, write_socketfile)
                # elif arpcp_dict_message['purpose_word'] == 'GET':
                # 	log_print('GET request')
                # 	self.get_request(arpcp_dict_message, write_socketfile)
                # elif arpcp_dict_message['purpose_word'] == 'ECHO':
                # 	log_print('ECHO request')
                # 	self.echo_request(arpcp_dict_message, write_socketfile)
    
                if arpcp_dict_message['purpose_word'] == 'SIGNAL':
                    log_print('SIGNAL request')
                    self.signal_request(arpcp_dict_message, write_socketfile)
                else:
                    self.send_message(write_socketfile, {"code": "301", "describe": "uncorrect purpose word"})

                write_socketfile.close()


            except Exception as e:
                print('Client serving failed', e)

# --------------------------------------------------------------------------------
    # def task_request(self, arpcp_dict_message, write_socketfile):
    #     self.execute_task()

    # def atask_request(self, arpcp_dict_message, write_socketfile):
    #     random_key = str(uuid.uuid4())
    #     self.add_to_redis(random_key, arpcp_dict_message)
    #     self.send_message(write_socketfile, {"code": "200", "key":random_key})

    # def get_request(self, arpcp_dict_message, write_socketfile):
    #     self.get_from_redis(1)

    # def echo_request(self, arpcp_dict_message, write_socketfile):
    #     self.send_message(write_socketfile, {"code": "100", "mac_addr": uuid.getnode()})

    def signal_request(self, arpcp_dict_message, write_socketfile):
        pass

# --------------------------------------------------------------------------------



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



if __name__ == '__main__':
    try:
        log_print('Application starting')
        arpcp_server = Arpcp_agent_server(**ConfigReader('arpcp.conf.yml').config['server'])
        arpcp_server.start()
    except KeyboardInterrupt:
        log_print('Application stoping')
        exit(1)
