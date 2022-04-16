import socket
import numpy as np
import pickle
import time
from struct import pack, unpack
import io

class GameSocket():
    '''
    Class to facilitate game data sending between client and server, 
    through sockets
    '''
    
    def __init__(self):
        pass

    def start_server(self, port):
        self.server_socket = socket.socket() 
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('0.0.0.0', port))
        self.server_socket.listen(5)
        
        print('Waiting for a connection...')
        self.client_connection, client_address = self.server_socket.accept()
        print(f'Connected to {client_address[0]} \n')

    def start_client(self, server_address, port):
        self.client_socket = socket.socket()
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.client_socket.connect((server_address, port))
            print(f'Connected to {server_address} on port {port} \n')
        except socket.error:
            print(f'Connection to {server_address} on port {port} failed: {socket.error} \n')
    
    def server_send_arr(self, arr):
        '''
        Sending frames as np array from Server to Client
        '''
        print('Sending Arr...')
        start_time = time.time()
        com_arr = self.encode_arr(arr)
        com_arr.seek(0)

        # Sending Array Size
        self.client_connection.send(pack('>H', len(com_arr.read())))

        # Sending Array
        com_arr.seek(0)
        self.client_connection.send(com_arr.read())
        print(f'Arr Sent in {(time.time() - start_time) * 1000} ms')
        
    def client_receive_arr(self):
        '''
        Receiving frames as np array from Server
        '''
        print('Receiving Arr...')
        start_time = time.time()

        # Receive Array Size
        receiving_size = unpack('>H', self.client_socket.recv(2))[0]

        # Receive Array
        data = self.client_socket.recv(receiving_size)
        
        out = self.decode_arr(data)
        print(f'Arr Received in {(time.time() - start_time) * 1000} ms')
        return out
    
    def encode_arr(self, arr):
        '''
        Encode delimited array before sending
        '''
        com_arr = io.BytesIO()
        np.savez_compressed(com_arr, arr)
        
        return com_arr
        
    def decode_arr(self, msg):
        '''
        Decode array after received
        '''
        decom_arr = np.load(io.BytesIO(msg))['arr_0']
        
        return decom_arr
    
    def client_send_int(self, num):
        '''
        Sending input as int from Client to Server
        '''
        print('Sending Int...')
        start_time = time.time()
        self.client_socket.sendall(str(num).encode('utf8'))
        print(f'Int Sent in {(time.time() - start_time) * 1000} ms')
    
    def server_receive_int(self):
        '''
        Receiving input as int from Server
        '''
        print('Receiving Int...')
        start_time = time.time()
        data = b''
        
        receiving_buffer = self.client_connection.recv(1)
        data += receiving_buffer
        
        out = int(data.decode('utf8'))
        print(f'Int Received in {(time.time() - start_time) * 1000} ms')
        return out
    
    def close_server(self):
        self.client_connection.close()
        self.server_socket.close()
        
    def close_client(self):
        self.client_socket.shutdown(1)
        self.client_socket.close()