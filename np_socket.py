import socket
import numpy as np
import pickle
import time

class NPSocket():
    '''
    Class to facilitate numpy array sending between client and server, 
    through sockets
    '''
    
    def __init__(self):
        pass

    def start_server(self, port):
        self.server_socket = socket.socket() 
        self.server_socket.bind(('0.0.0.0', port))
        self.server_socket.listen(1)
        
        print('Waiting for a connection...')
        self.client_connection, client_address = self.server_socket.accept()
        print(f'Connected to {client_address[0]} \n')

    def start_client(self, server_address, port):
        self.client_socket = socket.socket()
        try:
            self.client_socket.connect((server_address, port))
            print(f'Connected to {server_address} on port {port} \n')
        except socket.error:
            print(f'Connection to {server_address} on port {port} failed: {socket.error} \n')
    
    def send_arr(self, arr):
        start_time = time.time()
        serialized = pickle.dumps(arr, protocol=2)
        self.client_connection.send(serialized)
        print(f'Arr Sent in {time.time() - start_time} s')
        
    def receive_arr(self):
        start_time = time.time()
        data = b''
        while True:
            receiving_buffer = self.client_socket.recv(1024)
            if not receiving_buffer: break
            data += receiving_buffer
        out = pickle.loads(data)
        print(f'Arr Received in {time.time() - start_time} s')
        return out
    
    def close_server(self):
        self.client_connection.close()
        self.server_socket.close()
        
    def close_client(self):
        self.client_socket.shutdown(1)
        self.client_socket.close()