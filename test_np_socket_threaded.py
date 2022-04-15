import sys
import argparse
from queue import Queue
import threading
import time
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
    def __init__(self, q, input_port):
        Thread.__init__(self)
        self.daemon = True
        self._stop_event = threading.Event()
        self.q = q
        self.input_port = input_port
        self.start()
    
    def run(self):
        rcv_socket = GameSocket()
        rcv_socket.start_server(self.input_port)
        
        while not self.stopped():
            print("--thread")
            num = rcv_socket.server_receive_int()
            self.q.put(num)
        
    def stop(self):
        self._stop_event.set()
        
    def stopped(self):
        return self._stop_event.is_set()

class ClientInputSender(Thread):
    def __init__(self, server_address, input_port):
        Thread.__init__(self)
        self.daemon = True
        self._stop_event = threading.Event()
        self.input_port = input_port
        self.server_address = server_address
        self.start()

    def run(self):
        send_socket = GameSocket()
        send_socket.start_client(self.server_address, self.input_port)
        
        while not self.stopped():
            num = 2
            print("--thread")
            send_socket.client_send_int(num)
            time.sleep(1)
        
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
    
    t_sr = ServerInputReceiver(q, FLAGS.input_port)
    
    main_socket = GameSocket()
    main_socket.start_server(FLAGS.main_port)
    
    while (i <= 10):
        i += 1
        server_loop(main_socket)
        time.sleep(0.5)
    
    print(list(q.queue))
    
    t_sr.stop()
    rcv_socket.close_server()
    main_socket.close_server()
    
else:
    
    t_cs = ClientInputSender(FLAGS.server_address, FLAGS.input_port)
    
    main_socket = GameSocket()
    main_socket.start_client(FLAGS.server_address, FLAGS.main_port)
    
    while(i <= 10):
        i += 1
        
        client_loop(main_socket)
    
    t_cs.stop()
    send_socket.close_server()
    main_socket.close_server()
        
sys.exit()