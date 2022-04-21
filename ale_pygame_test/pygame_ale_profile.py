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

# PyGame Initialization
pygame.init()
screen = pygame.display.set_mode((screen_height, screen_width))

# Main Loop
episode = 0
episode_limit = 3
time_frame = []

pg_event_read_time_frame = []
ale_act_time_frame = []
ale_get_screen_time_frame = []
np_img_preproc_time_frame = []
pg_display_time_frame = []

while (episode < episode_limit):
    
    print(f"\nEpisode: {episode}")
    while not ale.game_over():
        start_time = time.time()
        
        # Pygame event loop
        pg_event_start_time = time.time()
        events = pygame.event.get()
        
        a = minimal_actions[0]
        if events != []:
            if events[0].type == pygame.KEYDOWN:
                if events[0].key == pygame.K_LEFT:
                    a = minimal_actions[3]
                if events[0].key == pygame.K_RIGHT:
                    a = minimal_actions[2]
                if events[0].key == pygame.K_UP:
                    a = minimal_actions[1]
        pg_event_read_time_frame.append(time.time() - pg_event_start_time)
        
        # ALE Act loop
        ale_act_start_time = time.time()
        a = minimal_actions[np.random.randint(len(minimal_actions))] #uncomment to randomize a
        reward = ale.act(a);
        ale_act_time_frame.append(time.time() - ale_act_start_time)
        
        # Display Loop
        ale_get_screen_start_time = time.time()
        frame = ale.getScreenRGB()
        ale_get_screen_time_frame.append(time.time() - ale_get_screen_start_time)
        
        np_img_preproc_start_time = time.time()
        frame = np.flip(np.rot90(frame), axis=0)
        np_img_preproc_time_frame.append(time.time() - np_img_preproc_start_time)
        
        pg_display_start_time = time.time()
        frame = pygame.surfarray.make_surface(frame)        
        screen.blit(frame, (0, 0))
        pygame.display.update()
        pg_display_time_frame.append(time.time() - pg_display_start_time)

        time_frame.append(time.time() - start_time)
        
    episode += 1
    ale.reset_game() 

# Print Profiling
mean_time_frame = np.mean(np.array(time_frame))
print("\nEnd to End: " + str(mean_time_frame) + "s, or " + str(1/mean_time_frame) + " FPS")

mean_time_frame = np.mean(np.array(pg_event_read_time_frame))
print("PG Event Reading: " + str(mean_time_frame) + "s, or " + str(1/mean_time_frame) + " FPS")

mean_time_frame = np.mean(np.array(ale_act_time_frame))
print("ALE Act: " + str(mean_time_frame) + "s, or " + str(1/mean_time_frame) + " FPS")

mean_time_frame = np.mean(np.array(ale_get_screen_time_frame))
print("ALE Get Screen RGB: " + str(mean_time_frame) + "s, or " + str(1/mean_time_frame) + " FPS")

mean_time_frame = np.mean(np.array(np_img_preproc_time_frame))
print("Np Preprocess: " + str(mean_time_frame) + "s, or " + str(1/mean_time_frame) + " FPS")

mean_time_frame = np.mean(np.array(pg_display_time_frame))
print("PG Display: " + str(mean_time_frame) + "s, or " + str(1/mean_time_frame) + " FPS")