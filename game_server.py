import time
import argparse
import numpy as np
import threading
from threading import Thread
from queue import Queue

from ale_py import ALEInterface
from game_socket.game_socket import GameServerSocket

# Handle Arguments
parser = argparse.ArgumentParser(description='')

parser.add_argument('--main_port', type=int, help='Socket Port for Main Loop', dest='main_port')
parser.add_argument('--input_port', type=int, help='Socket Port for Input Loop', dest='input_port')

FLAGS = parser.parse_args()

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
            num = self.rcv_socket.server_receive_int()
            self.q.put(num)
        
    def stop(self):
        self._stop_event.set()
        self.rcv_socket.close_server()
        
    def stopped(self):
        return self._stop_event.is_set()

# ALE Interface Initialization
ale = ALEInterface()
ale.setInt("random_seed", 42)
ale.setFloat("repeat_action_probability", 0)

rom_file = "/Users/aldo/workspace/202201_cs5340/_project/_rom/breakout.bin"
ale.loadROM(rom_file)

minimal_actions = ale.getMinimalActionSet()
(screen_width,screen_height) = ale.getScreenDims()

# ALE Reset and Prep Screen and RAM Data
ram_size = ale.getRAMSize()
ram = np.zeros((ram_size),dtype=np.uint8)
ale.getRAM(ram)

(screen_width,screen_height) = ale.getScreenDims()
screen_data = np.zeros((screen_width,screen_height,3),dtype=np.uint8)
ale.getScreenRGB(screen_data)

(screen_width,screen_height) = ale.getScreenDims()
screen_data = np.zeros((screen_width,screen_height),dtype=np.uint8)
ale.getScreen(screen_data)

# Initialize Socket
q = Queue()
t_sr = ServerInputReceiver(q, FLAGS.input_port)
main_socket = GameServerSocket()
main_socket.start_server(FLAGS.main_port)

# Main Game Loop
episode = 0
time_frame = []

while (episode < 1):
    print(f"\nEpisode: {episode}")
    while not ale.game_over():
        start_time = time.time()

        # Wait for Frame Request
        _ = main_socket.server_receive_int()
        
        # Read Event from Game Client
        if q.empty():
            a = minimal_actions[0]
        else:
            keypress = q.get()
            a = minimal_actions[keypress]
        
        # ALE Act
        reward = ale.act(a);
        
        # Frame Generation
        frame = ale.getScreenRGB()
        frame = np.flip(np.rot90(frame), axis=0)
        
        # Send Frames
        main_socket.server_send_arr(frame)

        time_frame.append(time.time() - start_time)
        
    episode += 1
    ale.reset_game() 

# Indicate Game Over with a Zero np Array
# TODO - Can be made better
main_socket.server_send_arr(np.zeros((5,5)))

t_sr.stop()
main_socket.close_server()
    
mean_time_frame = np.mean(np.array(time_frame))
print("Server End to End Process: " + str(mean_time_frame) + "s, or " + str(1/mean_time_frame) + " FPS")

