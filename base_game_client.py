from ast import dump
import time
import argparse
import numpy as np
from multiprocessing import Process
from multiprocessing import Queue

import pygame
from game_socket.game_socket import GameClientSocket

# Handle Arguments
parser = argparse.ArgumentParser(description='')

parser.add_argument('--cont_input', default=False, help='Enables Continuous Presses as Input', 
                    action='store_true', dest='cont_input')
parser.add_argument('--server_address', type=str, help='Server IP Address', dest='server_address')
parser.add_argument('--main_port', type=int, help='Socket Port for Main Loop', dest='main_port')
parser.add_argument('--input_port', type=int, help='Socket Port for Input Loop', dest='input_port')
parser.add_argument('--profiling', help='If True, prints profiling of code components', action='store_true', dest='profiling')

FLAGS = parser.parse_args()

# Threaded Input Function
class ClientFrameReceiver(Process):
    def __init__(self, q, time_q, server_address, input_port):
        Process.__init__(self)
        self.daemon = True
        self.stopped = False

        self.input_port = input_port
        self.server_address = server_address

        self.q = q
        self.time_q = time_q

    def run(self):
        self.cl_socket = GameClientSocket()
        self.cl_socket.start_client(self.server_address, self.input_port)

        while not self.stopped:
            try:
                frame_process_time_items = []
                frame_process_starttime = time.time()

                frame_process_time_items.append(time.time() - frame_process_starttime)

                data = self.cl_socket.client_receive_arr(decode=False)
                self.q.put(data)
                frame_process_time_items.append(time.time() - frame_process_starttime)

                self.time_q.put(frame_process_time_items)

            except:
                pass
        
    def stop(self):
        self.stopped = True
        #self.cl_socket.close_client()
        self.join() 
        self.close()

def get_pygame_keypress(cont_input, prev_num=None):
    if not cont_input:
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
    # else:
    #     events = pygame.event.get()
    #     if events != []:
    #         if events[0].type == pygame.KEYDOWN:
    #             if events[0].key == pygame.K_LEFT:
    #                 num = 3
    #             if events[0].key == pygame.K_RIGHT:
    #                 num = 2
    #             if events[0].key == pygame.K_UP:
    #                 num = 1
    #         elif events[0].type == pygame.KEYUP:
    #             if events[0].key == pygame.K_LEFT:
    #                 num = 0
    #             if events[0].key == pygame.K_RIGHT:
    #                 num = 0
    #             if events[0].key == pygame.K_UP:
    #                 num = 0
    #         else:
    #             num = prev_num
    #     else:
    #         num = prev_num
    
    else:
        num = 0
        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT]:
            num = 3
        if keys[pygame.K_RIGHT]:
            num = 2
        if keys[pygame.K_UP]:
            num = 1
    
    return num

def dump_time_queue_client(time_q):
    """
    Returns items from time queue into two separate lists.
    """
    result_delay = []
    result_nodelay = []

    time_q.put('STOP')

    for i in iter(time_q.get, 'STOP'):
        result_nodelay.append(i[0])
        result_delay.append(i[1])
    time.sleep(0.01)

    return result_delay, result_nodelay

if __name__ == "__main__":

    # PyGame Initialization
    pygame.init()
    screen = pygame.display.set_mode((160, 210))

    # Initialize Socket
    q = Queue()
    time_q = Queue()
    main_socket = GameClientSocket()
    main_socket.start_client(FLAGS.server_address, FLAGS.main_port)
    p_cfr = ClientFrameReceiver(q, time_q, FLAGS.server_address, FLAGS.input_port)

    # Main Loop
    p_cfr.start()

    keypress = 0
    last_sent_keypress = 0
    is_game_over = False

    frame_times = []
    keypress_times = []
    send_int_times = []
    decode_times = []
    pygame_times = []

    max_frame_time = 1 / 60
    frame_starttime = time.time()


    while not is_game_over:
        # Get Player Keypress
        keypress_starttime = time.time()
        if keypress == 0: keypress = get_pygame_keypress(FLAGS.cont_input, prev_num=last_sent_keypress)
        keypress_times.append(time.time() - keypress_starttime)

        running_frame_time = (time.time() - frame_starttime)
        if (running_frame_time >= max_frame_time):
            frame_starttime = time.time()
            frame_times.append(running_frame_time)

            # Send Last Keypress and reset
            send_int_starttime = time.time()
            try:
                main_socket.client_send_int(keypress)
                last_sent_keypress = keypress
                print(keypress)
            except:
                pass
            send_int_times.append(time.time() - send_int_starttime)
            keypress = 0

            if q.empty():
                # If frame queue is empty, no need to process the current tick
                pass
            else:
                # Get Frame Data from Queue
                data = q.get()

                decode_starttime = time.time()
                data = main_socket.decode_arr(data)
                decode_times.append(time.time() - decode_starttime)

                # Check if Loop Over (based on the shape of our data)
                # TODO - Can be made better
                if (data.shape[0] != 160):
                    is_game_over = True
                    break
                
                # Display Frame
                pygame_starttime = time.time()
                frame = pygame.surfarray.make_surface(data)
                screen.blit(frame, (0, 0))
                pygame.display.update()
                pygame_times.append(time.time() - pygame_starttime)

    main_socket.close_client()

    if FLAGS.profiling:
        mean_time_frame = np.mean(np.array(frame_times))
        print("\n")
        print("Client End to End Process  : " + str(mean_time_frame * 1000) + " ms, or " + str(1/mean_time_frame) + " FPS\n")

        mean_time_frame = np.mean(np.array(keypress_times))
        print("Keypress Process           : " + str(mean_time_frame * 1000) + " ms")
        mean_time_frame = np.mean(np.array(send_int_times))
        print("Send Input Process         : " + str(mean_time_frame * 1000) + " ms")
        mean_time_frame = np.mean(np.array(decode_times))
        print("Frame Decode Process       : " + str(mean_time_frame * 1000) + " ms")
        mean_time_frame = np.mean(np.array(pygame_times))
        print("Pygame Display Process     : " + str(mean_time_frame * 1000) + " ms")

        print("")

        delay_times, nodelay_times = dump_time_queue_client(time_q)
        mean_time_frame = np.mean(np.array(delay_times))
        print("Frame Rcv w/ Added Delay   : " + str(mean_time_frame * 1000) + " ms")
        mean_time_frame = np.mean(np.array(nodelay_times))
        print("Frame Rcv w/o Added Delay  : " + str(mean_time_frame * 1000) + " ms")

