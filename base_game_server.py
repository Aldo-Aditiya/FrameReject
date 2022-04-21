import time
import argparse
import numpy as np
from multiprocessing import Process
from multiprocessing import Queue

from ale_py import ALEInterface
from game_socket.game_socket import GameServerSocket

# Handle Arguments
parser = argparse.ArgumentParser(description='')

parser.add_argument('--server_address', type=str, help='Server IP Address', dest='server_address')
parser.add_argument('--main_port', type=int, help='Socket Port for Main Loop', dest='main_port')
parser.add_argument('--input_port', type=int, help='Socket Port for Input Loop', dest='input_port')
parser.add_argument('--profiling', help='If True, prints profiling of code components - also randomizes inputs', 
                    action='store_true', dest='profiling')

FLAGS = parser.parse_args()

# Threaded Input Functions
class ServerFrameSender(Process):
    def __init__(self, q, time_q, server_address, input_port):
        Process.__init__(self)
        self.daemon = True
        self.stopped = False
        
        self.input_port = input_port
        self.server_address = server_address

        self.q = q
        self.time_q = time_q
    
    def run(self):
        self.s_socket = GameServerSocket()
        self.s_socket.start_server(self.server_address, self.input_port)

        while not self.stopped:
            if self.q.empty():
                pass
            else:
                frame_process_starttime = time.time()

                arr = self.q.get()
                self.s_socket.server_send_arr(arr, encode=False)

                self.time_q.put(time.time() - frame_process_starttime)
        
    def stop(self):
        self.stopped = True
        #self.s_socket.close_server()
        self.join()
        self.close()

def dump_time_queue_server(time_q):
    """
    Returns items from time queue into two separate lists.
    """
    result_nodelay = []

    time_q.put('STOP')

    for i in iter(time_q.get, 'STOP'):
        result_nodelay.append(i)
    time.sleep(0.01)

    return result_nodelay

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
    time_q = Queue()
    main_socket = GameServerSocket()
    main_socket.start_server(FLAGS.server_address, FLAGS.main_port)
    p_sfs = ServerFrameSender(q, time_q, FLAGS.server_address, FLAGS.input_port)

    # Main Game Loop
    p_sfs.start()
    episode = 0

    frame_times = []
    rcv_int_times = []
    ale_act_times = []
    gen_frame_times = []
    encode_times = []

    keypress = 0
    while (episode < 1):
        print(f"\nEpisode: {episode}")
        while not ale.game_over():
            start_time = time.time()

            # Wait for Client Input
            rcv_int_starttime = time.time()
            try:
                keypress = main_socket.server_receive_int()
            except:
                pass
            
            # Randomizes input if in profiling mode
            if not FLAGS.profiling:
                a = minimal_actions[keypress]
            else:
                a = minimal_actions[np.random.randint(len(minimal_actions))]
            rcv_int_times.append(time.time() - rcv_int_starttime)

            # ALE Act
            ale_act_starttime = time.time()
            reward = ale.act(a);
            ale_act_times.append(time.time() - ale_act_starttime)
            
            # Frame Generation
            gen_frame_starttime = time.time()
            frame = ale.getScreenRGB()
            frame = np.flip(np.rot90(frame), axis=0)
            gen_frame_times.append(time.time() - gen_frame_starttime)

            # Encode Frame
            encode_starttime = time.time()
            frame = main_socket.encode_arr(frame)
            encode_times.append(time.time() - encode_starttime)
            
            # Send Frames
            q.put(frame)

            frame_times.append(time.time() - start_time)

        episode += 1
        ale.reset_game() 

    # Indicate Loop Over with a Zero np Array
    # TODO - Can be made better
    loop_over = main_socket.encode_arr(np.zeros((5,5)))
    q.put(loop_over)

    time.sleep(1)
    main_socket.close_server()
    
    if FLAGS.profiling:
        mean_time_frame = np.mean(np.array(frame_times))
        print("\n")
        print("Server End to End Process  : " + str(mean_time_frame * 1000) + " ms, or " + str(1/mean_time_frame) + " FPS \n")

        mean_time_frame = np.mean(np.array(rcv_int_times))
        print("Receive Input Process      : " + str(mean_time_frame * 1000) + " ms")
        mean_time_frame = np.mean(np.array(ale_act_times))
        print("ALE Act Process            : " + str(mean_time_frame * 1000) + " ms")
        mean_time_frame = np.mean(np.array(gen_frame_times))
        print("Generate Frames Process    : " + str(mean_time_frame * 1000) + " ms")
        mean_time_frame = np.mean(np.array(encode_times))
        print("Encode Frames Process      : " + str(mean_time_frame * 1000) + " ms")

        print("")

        nodelay_times = dump_time_queue_server(time_q)
        mean_time_frame = np.mean(np.array(nodelay_times))
        print("Frame Send Process         : " + str(mean_time_frame * 1000) + " ms")