import socket
import numpy as np
import time
from struct import pack, unpack
import io

class GameServerSocket():
    def __init__(self):
        pass

    def start_server(self, port):
        self.server_socket = socket.socket() 
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.server_socket.bind(('localhost', port))
        self.server_socket.listen(5)
        
        print('Waiting for a connection...')
        self.client_connection, client_address = self.server_socket.accept()
        print(f'Connected to {client_address[0]} port {port}')

    def server_send_arr(self, arr, encode=True):
        '''
        Sending frames as np array from Server to Client
        '''
        #print('Sending Arr...')
        start_time = time.time()
        if encode:
            com_arr = self.encode_arr(arr)
        else:
            com_arr = arr
        com_arr.seek(0)

        # Sending Array Size
        self.client_connection.send(pack('>H', len(com_arr.read())))

        # Sending Array
        com_arr.seek(0)
        self.client_connection.send(com_arr.read())
        #print(f'Arr Sent in {(time.time() - start_time) * 1000} ms')
        pass

    def server_receive_int(self, decode=True):
        '''
        Receiving input as int from Server
        '''
        #print('Receiving Int...')
        #start_time = time.time()
        
        # Receive Int Size
        receiving_size = unpack('>H', self.client_connection.recv(2))[0]

        # Receive Int
        data = self.client_connection.recv(receiving_size)
        
        if decode: 
            out = int(data.decode('utf8'))
        else:
            out = data
        #print(f'Int Received in {(time.time() - start_time) * 1000} ms')
        return out

    def close_server(self):
        self.client_connection.close()
        self.server_socket.close()

    @staticmethod
    def encode_arr(arr):    
        '''
        Encode delimited array before sending
        '''
        com_arr = io.BytesIO()
        np.savez_compressed(com_arr, arr)
        
        return com_arr

    @staticmethod
    def decode_int(data):
        return int(data.decode('utf8'))

class GameClientSocket():
    def __init__(self):
        pass

    def start_client(self, server_address, port):
        self.client_socket = socket.socket()
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        try:
            self.client_socket.connect((server_address, port))
            print(f'Connected to {server_address} on port {port}')
        except socket.error:
            print(f'Connection to {server_address} on port {port} failed: {socket.error}')

    def client_receive_arr(self, decode=True):
        '''
        Receiving frames as np array from Server
        '''
        #print('Receiving Arr...')
        #start_time = time.time()

        # Receive Array Size
        receiving_size = unpack('>H', self.client_socket.recv(2))[0]

        # Receive Array
        out = self.client_socket.recv(receiving_size)
        
        if decode:
            out = self.decode_arr(out)
        #print(f'Arr Received in {(time.time() - start_time) * 1000} ms')
        return out

    def client_send_int(self, num, encode=True, len_num=None):
        '''
        Sending input as int from Client to Server
        '''
        #print('Sending Int...')
        #start_time = time.time()

        if encode:
            num_bytes = str(num).encode('utf8')

            # Sending Int Size
            self.client_socket.sendall(pack('>H', len(num_bytes)))

            # Sending Int
            self.client_socket.sendall(num_bytes)

        else:
            # Assuming that Num and Length has been encoded
            self.client_socket.sendall(len_num)
            self.client_socket.sendall(num)

        #print(f'Int Sent in {(time.time() - start_time) * 1000} ms')
        pass

    def close_client(self):
        self.client_socket.shutdown(1)
        self.client_socket.close()

    @staticmethod
    def decode_arr(msg):
        '''
        Decode array after received
        '''
        decom_arr = np.load(io.BytesIO(msg))['arr_0']
        
        return decom_arr

    @staticmethod
    def encode_int(num):
        num_bytes = str(num).encode('utf8')
        len_bytes = pack('>H', len(num_bytes))

        return num_bytes, len_bytes