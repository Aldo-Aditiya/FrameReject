import time
import argparse
import numpy as np
from multiprocessing import Process
from multiprocessing import Queue

from ale_py import ALEInterface
from game_socket.game_socket import GameServerSocket

# Handle Arguments
parser = argparse.ArgumentParser(description='')

parser.add_argument('--main_port', type=int, help='Socket Port for Main Loop', dest='main_port')
parser.add_argument('--input_port', type=int, help='Socket Port for Input Loop', dest='input_port')

FLAGS = parser.parse_args()

# Threaded Input Functions
class ServerFrameSender(Process):
    def __init__(self, q, input_port):
        Process.__init__(self)
        self.daemon = True
        self.stopped = False
        self.q = q
        self.input_port = input_port
    
    def run(self):
        self.s_socket = GameServerSocket()
        self.s_socket.start_server(self.input_port)

        while not self.stopped:
            if self.q.empty():
                pass
            else:
                arr = self.q.get()
                self.s_socket.server_send_arr(arr, encode=False)
        
    def stop(self):
        self.stopped = True
        #self.s_socket.close_server()
        self.join()
        self.close()

if __name__ == "__main__":
    # ALE Interface Initialization
    ale = ALEInterface()
    ale.setInt("random_seed", 42)
    ale.setFloat("repeat_action_probability", 0)

    rom_file = "./rom/breakout.bin"
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
    main_socket = GameServerSocket()
    main_socket.start_server(FLAGS.main_port)
    p_sfs = ServerFrameSender(q, FLAGS.input_port)

    # Main Game Loop
    p_sfs.start()
    episode = 0
    time_frame = []

    keypress = 0
    while (episode < 1):
        print(f"\nEpisode: {episode}")
        while not ale.game_over():
            start_time = time.time()

            # Wait for Client Input
            try:
                keypress = main_socket.server_receive_int()
            except:
                pass
            a = minimal_actions[keypress]

            # ALE Act
            reward = ale.act(a);
            
            # Frame Generation
            frame = ale.getScreenRGB()
            frame = np.flip(np.rot90(frame), axis=0)
            frame = main_socket.encode_arr(frame)
            
            # Send Frames
            q.put(frame)

            time_frame.append(time.time() - start_time)

        episode += 1
        ale.reset_game() 

    # Indicate Loop Over with a Zero np Array
    # TODO - Can be made better
    loop_over = main_socket.encode_arr(np.zeros((5,5)))
    q.put(loop_over)

    time.sleep(1)

    main_socket.close_server()
        
    mean_time_frame = np.mean(np.array(time_frame))
    print("\nServer End to End Process: " + str(mean_time_frame) + "s, or " + str(1/mean_time_frame) + " FPS")