import sys
import argparse
import numpy as np
from np_socket import GameServerSocket, GameClientSocket

'''
Test Code for GameSocket Class
'''

parser = argparse.ArgumentParser(description='')

parser.add_argument('-s', help='Call if Server', action='store_true', dest='server')
parser.add_argument('--server_address', type=str, help='Server IP Address', dest='server_address')
parser.add_argument('--port', type=int, help='Socket Port', dest='port')
parser.add_argument('--test_multi', help='Test Multiple iterations of the process', action='store_true',dest='test_multi')

FLAGS = parser.parse_args()

if FLAGS.test_multi:
    itr = 10
else:
    itr = 1

test_num = 2

if FLAGS.server:
    gsocket = GameServerSocket()
    gsocket.start_server(FLAGS.port)
    for _ in range(itr):
        num = gsocket.server_receive_int()
        print(f'Data Received same as Data sent? {test_num == 2}')

        data = np.load('test_frame.npz')['arr_0']
        gsocket.server_send_arr(data)
        print("")

    gsocket.close_server()
    
else:
    gsocket = GameClientSocket()
    gsocket.start_client(FLAGS.server_address, FLAGS.port)
    for _ in range(itr):
        gsocket.client_send_int(test_num)

        data = gsocket.client_receive_arr()
        
        print(f'Data Received same as Data sent? {np.array_equal(data, np.load("test_frame.npz")["arr_0"])}')
        print("")

    gsocket.close_client()

sys.exit()