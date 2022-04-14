import os
import sys
import time

import numpy as np

from ale_py import ALEInterface
import pygame

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

# PyGame Initialization
pygame.init()
screen = pygame.display.set_mode((screen_height, screen_width))

# Main Loop
episode = 0
time_frame = []

while (episode < 1):
    
    print(f"\nEpisode: {episode}")
    while not ale.game_over():
        start_time = time.time()
        
        # Pygame event loop
        events = pygame.event.get()
        #if events != []: print(events)
        
        a = minimal_actions[0]
        if events != []:
            if events[0].type == pygame.KEYDOWN:
                if events[0].key == pygame.K_LEFT:
                    a = minimal_actions[3]
                if events[0].key == pygame.K_RIGHT:
                    a = minimal_actions[2]
                if events[0].key == pygame.K_UP:
                    a = minimal_actions[1]
        
        # ALE Act loop
        #a = minimal_actions[np.random.randint(len(minimal_actions))] #uncomment to randomize a
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
print("Display Random Action: " + str(mean_time_frame) + "s, or " + str(1/mean_time_frame) + " FPS")