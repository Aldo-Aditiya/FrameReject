import time
from datetime import datetime
import argparse

import numpy as np
import pandas as pd
import cv2

from ale_py import ALEInterface
import pygame

# Handle Arguments
parser = argparse.ArgumentParser(description='')

parser.add_argument('--num_ep', default=1, type=int, help='Number of Episodes', dest='num_ep')
parser.add_argument('--collect_data', default=False, help='Enables game data collection to a separate csv file', 
                    action='store_true', dest='collect_data')
parser.add_argument('--cont_input', default=False, help='Enables Continuous Presses as Input', 
                    action='store_true', dest='cont_input')
parser.add_argument('--rand_input', default=False, help='Enables Randomized Inputs', 
                    action='store_true', dest='rand_input')

FLAGS = parser.parse_args()

# Helper Functions
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

def generate_game_object_position(frame, all_black_pixels_ball):
    # Get ball and paddle states from the frame
    colored_region = frame[57:57 + 36, 43:146]
    ball_frame = frame[107:107 + 82, 43:146]
    paddle_frame = frame[190:190 + 3, 43:146]
    red_pixels_ball = np.argwhere(cv2.inRange(ball_frame, (1, 1, 1), (255, 255, 255)))
    red_pixels_paddle = np.argwhere(cv2.inRange(paddle_frame, (1, 1, 1), (255, 255, 255)))

    if len(red_pixels_ball) != 0:
        ball_position = red_pixels_ball[0]
    else:
        black_pixels_ball = np.argwhere(cv2.inRange(colored_region, (0, 0, 0), (0, 0, 0)))
        values = []

        for j in range(len(all_black_pixels_ball)):
            values = all_black_pixels_ball[j]

        red_pixels_ball = [i for i in black_pixels_ball if i not in values]
        try:
            ball_position = red_pixels_ball[0]
        except:
            ball_position = [0, 0]
        all_black_pixels_ball.append(black_pixels_ball)
    try:
        paddle_position = red_pixels_paddle[0]
    except:
        paddle_position = [0, 0]

    return paddle_position, ball_position

def generate_game_state(objects_position, previous_objects_position):
    paddle_position = objects_position[0]
    ball_position = objects_position[1]

    previous_paddle_position = previous_objects_position[0]
    previous_ball_position = previous_objects_position[1]

    if previous_paddle_position[1] < paddle_position[1]:
        paddle_state = "right"
    elif previous_paddle_position[1] > paddle_position[1]:
        paddle_state = "left"
    else:
        paddle_state = "stagnant"

    if previous_ball_position[1] < ball_position[1]:
        ball_state = "right"
    elif previous_ball_position[1] > ball_position[1]:
        ball_state = "left"
    else:
        ball_state = "stagnant"

    return paddle_state, ball_state

# Define Directories of Interest
rom_file = "./rom/breakout.bin"
data_dir = "./_data/"

# ALE Interface Initialization
ale = ALEInterface()
ale.setInt("random_seed", 42)
ale.setFloat("repeat_action_probability", 0)

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
time_frame = []
timestamp = str(datetime.now())[:-7]

for ep in range(FLAGS.num_ep):

    keypress = 0
    all_black_pixels_ball = []

    paddle_positions = []
    paddle_states = []
    previous_paddle_positions = []
    ball_positions = []
    ball_states = []
    previous_ball_positions = []
    keypresses = []

    previous_paddle_position = [0, 0]
    previous_ball_position = [0, 0]
    previous_keypress = 0

    print(f"\nEpisode: {ep}")
    while not ale.game_over():
        start_time = time.time()
        
        # Pygame event loop        
        if not FLAGS.rand_input:
            keypress = get_pygame_keypress(FLAGS.cont_input, prev_num=keypress)
            a = minimal_actions[keypress]
        else:
            a = minimal_actions[np.random.randint(len(minimal_actions))]
        
        # ALE Act loop
        reward = ale.act(a);
        
        # Display Loop
        frame_ori = ale.getScreenRGB()
        frame = np.flip(np.rot90(frame_ori), axis=0)
        frame = pygame.surfarray.make_surface(frame)
        screen.blit(frame, (0, 0))
        pygame.display.update()

        # Append Game Data (Game State and Inputs)
        if (FLAGS.collect_data):
            # Generate and append relevant game information (keypress, states, positions)
            paddle_position, ball_position = generate_game_object_position(frame_ori, all_black_pixels_ball)
            paddle_state, ball_state = generate_game_state([paddle_position, ball_position], 
                                                            [previous_paddle_position, previous_ball_position])

            paddle_positions.append(paddle_position)
            paddle_states.append(paddle_state)
            previous_paddle_positions.append(previous_paddle_position)
            ball_positions.append(ball_position)
            ball_states.append(ball_state)
            previous_ball_positions.append(previous_ball_position)
            keypresses.append(keypress)

            # Handle 0-valued inputs in between navigational inputs
            if (not FLAGS.cont_input):
                if keypress == 0 and str(previous_paddle_position) != str(paddle_position):
                    keypress = previous_keypress

            # Assign current information as "previous" for the next time step
            previous_keypress = keypress
            previous_paddle_position = paddle_position
            previous_ball_position = ball_position

        time_frame.append(time.time() - start_time)
        
    ale.reset_game() 

    # Save Game Data for This Episode
    df_dict = {'paddle_position': paddle_positions,
               'paddle_state': paddle_states,
               'previous_paddle_position': previous_paddle_positions,
               'ball_position': ball_positions,
               'ball_state': ball_states,
               'previous_ball_position': previous_ball_positions,
               'keypress': keypresses}
    if (FLAGS.collect_data):
        df = pd.DataFrame(df_dict)

        if (FLAGS.cont_input): 
            input_setting = "cont" 
        else: 
            input_setting = "man"

        csv_path = data_dir + timestamp + "_" + str(ep) + "_" + input_setting + '.csv'
        df.to_csv(csv_path, index=False)

mean_time_frame = np.mean(np.array(time_frame))
print("Game Loop Time: " + str(mean_time_frame) + "s, or " + str(1/mean_time_frame) + " FPS")