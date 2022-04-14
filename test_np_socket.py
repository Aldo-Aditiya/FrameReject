import sys
import argparse
import numpy as np
from np_socket import NPSocket

'''
Test Code for NPSocket Class
'''

parser = argparse.ArgumentParser(description='')

parser.add_argument('-s', help='Call if Server', action='store_true', dest='server')
parser.add_argument('--server_address', type=str, help='Server IP Address', dest='server_address')
parser.add_argument('--port', type=int, help='Socket Port', dest='port')

FLAGS = parser.parse_args()

np_socket = NPSocket()
                    
if FLAGS.server:
    np_socket.start_server(FLAGS.port)
    data = np_socket.receive_arr()
    
    print(data)
    np_socket.close_server()
    
else:
    np_socket.start_client(FLAGS.server_address, FLAGS.port)
    
    data = np.zeros((5,5))
    np_socket.send_arr(data)
    
    np_socket.close_client

sys.exit()