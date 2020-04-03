import os
import sys
import time
import yaml
# import threading
sys.path.append(os.path.abspath(os.path.join('..', 'arpcp')))
from __arpcp import Arpcp
import setproctitle
import threading as th
# import multiprocessing as mp

# from multiprocessing.managers import BaseManager
# mp.set_start_method('s spawn')

LOG = True

def log_print(string):
    if LOG:
        print("[LOG] " + string)
        
class ConfigReader:
    def __init__(self, config_file):
        with open(config_file) as c:
            self.config = yaml.safe_load(c)

class ARPCPServer:
    def __init__(
        self,
        host='0.0.0.0',
        port=7018,
        connection_queue_size=1,
        workers_count=2,
        max_invokers_count=100,
        procname_prefix='ARPCP',
        master_procname='server',
        worker_procname='worker',
        invoker_procname='invoker'
    ):
        log_print('ARPCPServer initializing')
        # configuration variables
        self.host = host
        self.port = port
        self.connection_queue_size = connection_queue_size
        self.workers_count = workers_count
        self.max_invokers_count = max_invokers_count
        self.procname_prefix = procname_prefix
        self.master_procname = master_procname
        self.worker_procname = worker_procname
        self.invoker_procname = invoker_procname
        # internal objects
        self.sock = None
        self.workers = []
        log_print('ARPCPServer initialized')

    def start(self, sync=True):
        if sync:
            self.__start()
        else:
            log_print('async ARPCPServer')
            # ...

    def __start(self):
        master_procname = \
            self.procname_prefix + ':' + \
            self.master_procname
        # mp.current_process().name = master_procname
            # setproctitle.setproctitle(master_procname)

        log_print('ARPCPServer starting')
        self.__prepare_socket()
        self.__create_workers()
        self.__start_workers()
        log_print('ARPCPServer started')
        self.__join_workers()

    def __prepare_socket(self):
        log_print('TCP socket preparing')
        self.sock = Arpcp.create_socket()
        self.sock.bind((self.host, self.port,))
        self.sock.listen(self.connection_queue_size)
        log_print('TCP socket prepared')

    def __create_workers(self):
        log_print('Workers creating')

        platform = sys.platform
        if platform == "linux" or platform == "linux2":
            print('linux')
            # for i in range(self.workers_count):
            #     worker = mp.Process(target=self.__worker)
            #     worker.daemon = True
            #     self.workers.append(worker)
        elif platform == "win32":
            print('win32')
            # worker = mp.Process(target=self.worker)
            worker = th.Thread(target=self.worker)
            worker.daemon = True
            self.workers.append(worker)
            # Windows...
            pass

        log_print('Workers created')

    def __start_workers(self):
        log_print('Workers starting')
        for worker in self.workers:
            worker.start()
            time.sleep(0.1)
        log_print('Workers started')

    def __join_workers(self):
        log_print('Workers joining')
        for worker in self.workers:
            worker.join()
            log_print(worker.name + " joins")
        log_print('Workers joined')

    def worker(self):
        # worker_procname = \
        #     self.procname_prefix + ':' + \
        #     self.master_procname + ':' + \
        #     self.worker_procname + '[' + str(mp.current_process().pid) + ']'
        # mp.current_process().name = worker_procname
            # setproctitle.setproctitle(worker_procname)

        # log_print(worker_procname + ' started')
        
        try:
            while True:
                conn, addr = self.sock.accept()
                invoker = th.Thread(target=self.__invoker, args=(conn, addr,))
                invoker.start()
        except KeyboardInterrupt:
            log_print('Application stoping')
            exit(1)

        
        

    def __invoker(self, conn, addr):
        # invoker_procname = \
        #     self.procname_prefix + ':' + \
        #     self.master_procname + ':' + \
        #     self.worker_procname + '[' + str(mp.current_process().pid) + ']:' + \
        #     self.invoker_procname + '[' + str(th.current_thread().ident) + ']'
        # mp.current_process().name = invoker_procname
            # setproctitle.setproctitle(invoker_procname)


        write_socketfile, read_socketfile = Arpcp.make_socket_files(conn, buffering = None)
        log_print('socket file created')
        try:
            arpcp_dict_message = self.read_message(read_socketfile)
            log_print('message readed')
            
            read_socketfile.close()
            log_print('read_socket closed')

            print()
            print("=====CONNECTION=======================================")
            print("Client: " + str(addr[0]) + ":" + str(addr[1]))
            print("Data:\r\n" + str(arpcp_dict_message))
            print("======================================================")
            print()
            time.sleep(10)
            self.send_message(write_socketfile, {"task":"200"})
            write_socketfile.close()

        except ConnectionResetError:
            conn = None
        # except Exception as e:
            # self.send_error(conn, e)
        if conn:
            conn.close()
            print('Client serving failed')

    def read_message(self, read_socketfile):
        return Arpcp.read_request(read_socketfile)

    def send_message(self, write_socketfile, message):
        Arpcp.send_message(write_socketfile, message)

if __name__ == '__main__':
    try:
        log_print('Application starting')
        arpcp_server = ARPCPServer(**ConfigReader('arpcp.conf.yml').config['server'])
        # arpcp_server = ARPCPServer()
        arpcp_server.start()
    except KeyboardInterrupt:
        log_print('Application stoping')
        exit(1)
