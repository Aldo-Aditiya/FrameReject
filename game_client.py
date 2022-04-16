import time
import argparse
import numpy as np
import threading
from threading import Thread
from queue import Queue

import pygame
from game_socket.game_socket import GameClientSocket

# Handle Arguments
parser = argparse.ArgumentParser(description='')

parser.add_argument('--server_address', type=str, help='Server IP Address', dest='server_address')
parser.add_argument('--main_port', type=int, help='Socket Port for Main Loop', dest='main_port')
parser.add_argument('--input_port', type=int, help='Socket Port for Input Loop', dest='input_port')

FLAGS = parser.parse_args()

# Threaded Input Function
class ClientInputSender(Thread):
    def __init__(self, q, server_address, input_port):
        Thread.__init__(self)
        self.daemon = True
        self._stop_event = threading.Event()
        self.q = q
        self.input_port = input_port
        self.server_address = server_address
        self.start()

    def run(self):
        self.send_socket = GameClientSocket()
        self.send_socket.start_client(self.server_address, self.input_port)
        
        while not self.stopped():
            if q.empty():
                pass
            else:
                num = q.get()
                self.send_socket.client_send_int(num)
        
    def stop(self):
        self._stop_event.set()
        self.send_socket.close_client()
        
    def stopped(self):
        return self._stop_event.is_set()   

def get_pygame_keypress():
    events = pygame.event.get()
    num = 0
    if events != []:
        if events[0].type == pygame.KEYDOWN:
            if events[0].key == pygame.K_LEFT:
                num = 3
            if events[0].key == pygame.K_RIGHT:
                num = 2
            if events[0].key == pygame.K_UP:
                num = 1
    
    return num

# PyGame Initialization
pygame.init()
screen = pygame.display.set_mode((160, 210))

# Initialize Socket
q = Queue()
t_cs = ClientInputSender(q, FLAGS.server_address, FLAGS.input_port)
main_socket = GameClientSocket()
main_socket.start_client(FLAGS.server_address, FLAGS.main_port)

# Main Loop
is_game_over = False
time_frame = []

while not is_game_over:
    start_time = time.time()

    # Get Player Keypress and send through a separate thread
    num = get_pygame_keypress()
    if num != 0: q.put(num)

    # Receive Frames
    data = main_socket.client_receive_arr()

    # Check if Game Over (based on the length of frame array)
    # TODO - Can be made better
    if (data.shape[0] != 160):
        is_game_over = True
        break

    frame = pygame.surfarray.make_surface(data)
    screen.blit(frame, (0, 0))
    pygame.display.update()

    time_frame.append(time.time() - start_time)

t_cs.stop()
main_socket.close_client()

mean_time_frame = np.mean(np.array(time_frame))
print("Client End to End Process: " + str(mean_time_frame) + "s, or " + str(1/mean_time_frame) + " FPS")