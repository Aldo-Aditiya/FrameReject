import time
import argparse
import numpy as np
from multiprocessing import Process
from multiprocessing import Queue

import pygame
from game_socket.game_socket import GameClientSocket

# Handle Arguments
parser = argparse.ArgumentParser(description='')

parser.add_argument('--server_address', type=str, help='Server IP Address', dest='server_address')
parser.add_argument('--main_port', type=int, help='Socket Port for Main Loop', dest='main_port')
parser.add_argument('--input_port', type=int, help='Socket Port for Input Loop', dest='input_port')
parser.add_argument('--frame_delay_ms', default=0, type=int, help='ms Delay in frame sending', dest='frame_delay_ms')

FLAGS = parser.parse_args()

# Threaded Input Function
class ClientFrameReceiver(Process):
    def __init__(self, q, server_address, input_port):
        Process.__init__(self)
        self.daemon = True
        self.stopped = False
        self.q = q
        self.input_port = input_port
        self.server_address = server_address

    def run(self):
        self.cl_socket = GameClientSocket()
        self.cl_socket.start_client(self.server_address, self.input_port)

        while not self.stopped:
            try:
                time.sleep(FLAGS.frame_delay_ms / 1000)
                data = self.cl_socket.client_receive_arr(decode=False)
                self.q.put(data)
            except:
                pass
        
    def stop(self):
        self.stopped = True
        #self.cl_socket.close_client()
        self.join() 
        self.close()

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

if __name__ == "__main__":

    # PyGame Initialization
    pygame.init()
    screen = pygame.display.set_mode((160, 210))

    # Initialize Socket
    q = Queue()
    main_socket = GameClientSocket()
    main_socket.start_client(FLAGS.server_address, FLAGS.main_port)
    p_cfr = ClientFrameReceiver(q, FLAGS.server_address, FLAGS.input_port)

    # Main Loop
    p_cfr.start()
    is_game_over = False
    frame_time = 1 / 60
    time_frame = []
    keypress = 0

    frame_starttime = time.time()

    while not is_game_over:
        # Get Player Keypress
        if keypress == 0: keypress = get_pygame_keypress()

        running_frame_time = (time.time() - frame_starttime)
        if (running_frame_time >= frame_time):
            time_frame.append(running_frame_time)
            frame_starttime = time.time()

            # Send Last Keypress and reset
            try:
                main_socket.client_send_int(keypress)
            except:
                pass
            keypress = 0

            if q.empty():
                # If frame queue is empty, no need to process the current tick
                pass
            else:
                # Get Frame Data from Queue
                data = q.get()

                data = main_socket.decode_arr(data)

                # Check if Loop Over (based on the shape of our data)
                # TODO - Can be made better
                if (data.shape[0] != 160):
                    is_game_over = True
                    break
                
                # Display Frame
                frame = pygame.surfarray.make_surface(data)
                screen.blit(frame, (0, 0))
                pygame.display.update()

    main_socket.close_client()

    mean_time_frame = np.mean(np.array(time_frame))
    print("\nClient End to End Process: " + str(mean_time_frame) + "s, or " + str(1/mean_time_frame) + " FPS")