import time
import argparse

import numpy as np

from ale_py import ALEInterface
import pygame

# Handle Arguments
parser = argparse.ArgumentParser(description='')

parser.add_argument('--num_ep', default=1, type=int, help='Number of Episodes', dest='num_ep')
parser.add_argument('--cont_input', default=False, help='Enables Continuous Presses as Input', 
                    action='store_true', dest='cont_input')
parser.add_argument('--rand_input', default=False, help='Enables Randomized Inputs', 
                    action='store_true', dest='rand_input')

FLAGS = parser.parse_args()

# Input Function
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
    else:
        events = pygame.event.get()
        if events != []:
            if events[0].type == pygame.KEYDOWN:
                if events[0].key == pygame.K_LEFT:
                    num = 3
                if events[0].key == pygame.K_RIGHT:
                    num = 2
                if events[0].key == pygame.K_UP:
                    num = 1
            elif events[0].type == pygame.KEYUP:
                if events[0].key == pygame.K_LEFT:
                    num = 0
                if events[0].key == pygame.K_RIGHT:
                    num = 0
                if events[0].key == pygame.K_UP:
                    num = 0
            else:
                num = prev_num
        else:
            num = prev_num
    
    return num

# ALE Interface Initialization
ale = ALEInterface()
ale.setInt("random_seed", 42)
ale.setFloat("repeat_action_probability", 0)

rom_file = "../rom/breakout.bin"
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

# PyGame Initialization
pygame.init()
screen = pygame.display.set_mode((screen_height, screen_width))

# Main Loop
episode = 0
time_frame = []

keypress = 0

while (episode < FLAGS.num_ep):
    
    print(f"\nEpisode: {episode}")
    while not ale.game_over():
        start_time = time.time()
        
        # Pygame event loop        
        if not FLAGS.rand_input:
            keypress = get_pygame_keypress(FLAGS.cont_input, prev_num=keypress)
            a = minimal_actions[keypress]
        else:
            a = minimal_actions[np.random.randint(len(minimal_actions))]

        print(keypress)
        
        # ALE Act loop
        reward = ale.act(a);
        
        # Display Loop
        frame = ale.getScreenRGB()
        frame = np.flip(np.rot90(frame), axis=0)
        frame = pygame.surfarray.make_surface(frame)
        screen.blit(frame, (0, 0))
        pygame.display.update()

        time_frame.append(time.time() - start_time)
        
    episode += 1
    ale.reset_game() 

mean_time_frame = np.mean(np.array(time_frame))
print("Game Loop Time: " + str(mean_time_frame) + "s, or " + str(1/mean_time_frame) + " FPS")