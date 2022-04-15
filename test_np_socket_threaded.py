import sys
import argparse
from queue import Queue
from threading import Thread

import numpy as np

from np_socket import GameSocket

'''
Test Code for GameSocket Class
'''

parser = argparse.ArgumentParser(description='')

parser.add_argument('-s', help='Call if Server', action='store_true', dest='server')
parser.add_argument('--server_address', type=str, help='Server IP Address', dest='server_address')
parser.add_argument('--main_port', type=int, help='Socket Port for Main Loop', dest='main_port')
parser.add_argument('--input_port', type=int, help='Socket Port for Input Loop', dest='input_port')

FLAGS = parser.parse_args()

# Threaded Input Functions
class ServerInputReceiver(Thread):
    def __init__(self, q, rcv_socket):
        Thread.__init__(self)
        self.daemon = True
        self.__stop_event = threading.Event()
    
    def run(self):
        while not self.stopped():
            num = rcv_socket.server_receive_int()
            q.put(num)
        
    def stop(self):
        self._stop_event.set()
        
    def stopped(self):
        return self._stop_event.is_set()

class ClientInputSender(Thread):
    def __init__(self, send_socket):
        Thread.__init__(self)
        self.daemon = True
        self.__stop_event = threading.Event()
        self.start()

    def run(self)
        while not self.stopped():
            num = 2
            sleep(1)
            send_socket.client_send_int(num)
        
    def stop(self):
        self._stop_event.set()
        
    def stopped(self):
        return self._stop_event.is_set()    

# Main Loop Functions
def server_loop(main_socket):
    data = np.zeros((5,5))
    main_socket.server_send_arr(data)    

def client_loop(main_socket):
    data = main_socket.client_receive_arr()

q = Queue()
i = 0
if FLAGS.server:
    
    main_socket = GameSocket()
    main_socket.start_server(FLAGS.main_port)
    
    rcv_socket = GameSocket()
    rcv_socket.start_server(FLAGS.input_port)
    t_sr = ServerInputReceiver(q, rcv_socket)
    
    while (i <= 10):
        i += 1
        server_loop(main_socket)
    
    print(q)
    
    t_sr.stop()
    rcv_socket.close_server()
    main_socket.close_server()
    
else:
    
    main_socket = GameSocket()
    main_socket.start_server(FLAGS.server_address, FLAGS.main_port)
    
    send_socket = GameSocket()
    send_socket.start_server(FLAGS.server_address, FLAGS.input_port)
    t_cs = ClientInputSender(send_socket)
    
    while(i <= 10):
        i += 1
        
        client_loop(main_socket)
    
    t_cs.stop()
    send_socket.close_server()
    main_socket.close_server()
        
sys.exit()