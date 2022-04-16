import sys
import argparse
from queue import Queue
import threading
import time
from threading import Thread

import numpy as np

from game_socket import GameServerSocket, GameClientSocket

'''
Threaded Test Code for GameServerSocket, GameClientSocket Classes
'''

parser = argparse.ArgumentParser(description='')

parser.add_argument('-s', help='Call if Server', action='store_true', dest='server')
parser.add_argument('--server_address', type=str, help='Server IP Address', dest='server_address')
parser.add_argument('--main_port', type=int, help='Socket Port for Main Loop', dest='main_port')
parser.add_argument('--input_port', type=int, help='Socket Port for Input Loop', dest='input_port')
parser.add_argument('--test_multi', help='Test Multiple iterations of the process', action='store_true',dest='test_multi')

FLAGS = parser.parse_args()

if FLAGS.test_multi:
    itr = 10
else:
    itr = 1

test_num = 2
input_send_delay = 0.5
frame_send_delay = 1

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
        self.rcv_socket = GameServerSocket()
        self.rcv_socket.start_server(self.input_port)
        
        while not self.stopped():
            print("--thread")
            num = self.rcv_socket.server_receive_int()
            print(f'Data Received same as Data sent? {num == test_num}')
            self.q.put(num)
        
    def stop(self):
        self._stop_event.set()
        self.rcv_socket.close_server()
        
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
        self.send_socket = GameClientSocket()
        self.send_socket.start_client(self.server_address, self.input_port)
        
        while not self.stopped():
            num = test_num
            time.sleep(input_send_delay)
            print("--thread")
            self.send_socket.client_send_int(num)
        
    def stop(self):
        self._stop_event.set()
        self.send_socket.close_client()
        
    def stopped(self):
        return self._stop_event.is_set()    

# Main Loop Functions
def server_loop(data, main_socket):
    main_socket.server_send_arr(data)    

def client_loop(main_socket):
    data = main_socket.client_receive_arr()
    return data

q = Queue()
i = 0
if FLAGS.server:
    
    t_sr = ServerInputReceiver(q, FLAGS.input_port)
    
    main_socket = GameServerSocket()
    main_socket.start_server(FLAGS.main_port)
    data = np.load('test_frame.npz')['arr_0']
    
    for _ in range(itr):
        server_loop(data, main_socket)
        time.sleep(frame_send_delay)
        print("")
    
    print(f'Length of Queue {len(list(q.queue))}')
    
    t_sr.stop()
    main_socket.close_server()
    
else:
    
    t_cs = ClientInputSender(FLAGS.server_address, FLAGS.input_port)
    
    main_socket = GameClientSocket()
    main_socket.start_client(FLAGS.server_address, FLAGS.main_port)
    
    for _ in range(itr):
        data = client_loop(main_socket)
        print(f'Data Received same as Data sent? {np.array_equal(data, np.load("test_frame.npz")["arr_0"])}')
        print("")
    
    t_cs.stop()
    main_socket.close_client()
        
sys.exit()