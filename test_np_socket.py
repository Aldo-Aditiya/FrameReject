import sys
import argparse
import numpy as np
from np_socket import GameSocket

'''
Test Code for NPSocket Class
'''

parser = argparse.ArgumentParser(description='')

parser.add_argument('-s', help='Call if Server', action='store_true', dest='server')
parser.add_argument('--server_address', type=str, help='Server IP Address', dest='server_address')
parser.add_argument('--port', type=int, help='Socket Port', dest='port')

FLAGS = parser.parse_args()

gsocket = GameSocket()
                    
if FLAGS.server:
    gsocket.start_server(FLAGS.port)
    
    num = gsocket.server_receive_int()
    print(num)
    
    data = np.zeros((5,5))
    gsocket.server_send_arr(data)
    
    gsocket.close_server()
    
else:
    gsocket.start_client(FLAGS.server_address, FLAGS.port)
    
    num = 2
    gsocket.client_send_int(num)
    
    data = gsocket.client_receive_arr()
    
    print(data)
    gsocket.close_client()

sys.exit()