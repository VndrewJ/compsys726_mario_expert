"""
This the primary class for the Mario Expert agent. It contains the logic for the Mario Expert agent to play the game and choose actions.

Your goal is to implement the functions and methods required to enable choose_action to select the best action for the agent to take.

Original Mario Manual: https://www.thegameisafootarcade.com/wp-content/uploads/2017/04/Super-Mario-Land-Game-Manual.pdf
"""

import json
import logging
import random

import cv2
import numpy as np
from mario_environment import MarioEnvironment
from pyboy.utils import WindowEvent


class MarioController(MarioEnvironment):
    """
    The MarioController class represents a controller for the Mario game environment.

    You can build upon this class all you want to implement your Mario Expert agent.

    Args:
        act_freq (int): The frequency at which actions are performed. Defaults to 10.
        emulation_speed (int): The speed of the game emulation. Defaults to 0.
        headless (bool): Whether to run the game in headless mode. Defaults to False.
    """

    def __init__(
        self,
        emulation_speed: int = 1,
        headless: bool = False,
    ) -> None:
        super().__init__(
            emulation_speed=emulation_speed,
            headless=headless,
        )

        # Example of valid actions based purely on the buttons you can press
        valid_actions: list[WindowEvent] = [
            WindowEvent.PRESS_ARROW_DOWN,
            WindowEvent.PRESS_ARROW_LEFT,
            WindowEvent.PRESS_ARROW_RIGHT,
            WindowEvent.PRESS_ARROW_UP,
            WindowEvent.PRESS_BUTTON_A,
            WindowEvent.PRESS_BUTTON_B,
        ]

        release_button: list[WindowEvent] = [
            WindowEvent.RELEASE_ARROW_DOWN,
            WindowEvent.RELEASE_ARROW_LEFT,
            WindowEvent.RELEASE_ARROW_RIGHT,
            WindowEvent.RELEASE_ARROW_UP,
            WindowEvent.RELEASE_BUTTON_A,
            WindowEvent.RELEASE_BUTTON_B,
        ]

        self.valid_actions = valid_actions
        self.release_button = release_button

    def run_action(self, action: int, hold_freq = 1) -> None:
        """
        This is a very basic example of how this function could be implemented

        As part of this assignment your job is to modify this function to better suit your needs

        You can change the action type to whatever you want or need just remember the base control of the game is pushing buttons
        """
        if action == 6:
            self.pyboy.send_input(self.valid_actions[2])
            self.pyboy.send_input(self.valid_actions[4])

            for _ in range(hold_freq):
                self.pyboy.tick()

            self.pyboy.send_input(self.release_button[2])
            self.pyboy.send_input(self.release_button[4])

        # Simply toggles the buttons being on or off for a duration of hold_freq
        else:
            self.pyboy.send_input(self.valid_actions[action])

            for _ in range(hold_freq):
                self.pyboy.tick()

        # self.pyboy.tick()

            self.pyboy.send_input(self.release_button[action])
        # Tick one more time for some reason or otherwise jumping doesnt work
        self.pyboy.tick()

    def release_action(self, action: int) -> None:
        self.pyboy.send_input(self.release_button[action])

class MarioExpert:
    """
    The MarioExpert class represents an expert agent for playing the Mario game.

    Edit this class to implement the logic for the Mario Expert agent to play the game.

    Do NOT edit the input parameters for the __init__ method.

    Args:
        results_path (str): The path to save the results and video of the gameplay.
        headless (bool, optional): Whether to run the game in headless mode. Defaults to False.
    """
    # State/action variables
    mario_state = ["DEFAULT", 
                   "OBSTACLE", 
                   "ENEMIES", 
                   "GOOMBA ABOVE", 
                   "GOOMBA BELOW",
                   "GAP",
                   "JUMPING BUG",
                   "UNDER + GOOMBA"
                   ]
    
    previous_action = None

    def __init__(self, results_path: str, headless=False):
        self.results_path = results_path
        self.environment = MarioController(headless=headless)
        self.video = None
        self.current_state = "DEFAULT"

        # Initialize class attributes for storing positions and obstacles
        self.mario_row = -1
        self.mario_col = -1
        self.obstacles_np = None
        self.goombas_np = None
        self.jumping_bug_np = None

    def scan_frame(self):
        """
        Updates the Mario position, obstacles, and goombas based on the current game area.
        """
        game_area = self.environment.game_area()
        game_area_np = np.array(game_area)

        # Clear obstacle arrays
        self.obstacles_np = None
        self.goombas_np = None
        self.gaps_np = None

        print(game_area)

        # Update Mario's position
        mario_positions = np.where(game_area_np == 1)
        if mario_positions[0].size > 0:
            self.mario_row = mario_positions[0][0] + 1
            self.mario_col = mario_positions[1][0] + 1
            print(f"Mario at Row: {self.mario_row}, Col: {self.mario_col}")

        # Update obstacles (10 or 14)
        obstacle_positions_10 = np.where(game_area_np == 10)
        obstacle_positions_14 = np.where(game_area_np == 14)
        self.obstacles_np = np.column_stack((
            np.concatenate((obstacle_positions_10[0], obstacle_positions_14[0])),
            np.concatenate((obstacle_positions_10[1], obstacle_positions_14[1]))
        ))

        # Update gaps (0) that are below and in front of Mario
        gap_positions = np.where(game_area_np == 0)
        self.gaps_np = np.column_stack((gap_positions[0], gap_positions[1]))
        # Filter gaps to only include those below or in front of Mario
        self.gaps_np = self.gaps_np[(self.gaps_np[:, 0] > self.mario_row) & 
                                    (self.gaps_np[:, 1] > self.mario_col)]

        # Update goombas (15) and koopas (16)
        goomba_positions = np.where(game_area_np == 15)
        koopa_positions = np.where(game_area_np == 16)
        # Combine Goomba and Koopa positions
        combined_positions = np.column_stack((
            np.concatenate((goomba_positions[0], koopa_positions[0])),
            np.concatenate((goomba_positions[1], koopa_positions[1]))
        ))
        # Save combined positions as goombas_np
        self.goombas_np = combined_positions

        # Update jumping bug (18) array
        jumping_bug_positions = np.where(game_area_np == 18)
        self.jumping_bug_np = np.column_stack(jumping_bug_positions)


    def fsm_transition(self):
        # Edge case
        print(self.environment.get_x_position())
        if self.environment.get_x_position() > 1670 and self.environment.get_x_position() < 1680:
            return "UNDER + GOOMBA"

        # Check for obstacles in front of Mario
        # if np.any((self.obstacles_np[:, 0] == self.mario_row) & 
        #         (self.obstacles_np[:, 1] == self.mario_col + 1)) or \
        # np.any((self.obstacles_np[:, 0] == self.mario_row - 1) & 
        #         (self.obstacles_np[:, 1] == self.mario_col + 1)):
        #     return "OBSTACLE"
        
        if np.any((self.obstacles_np[:, 0] == self.mario_row ) & 
                (self.obstacles_np[:, 1] == self.mario_col + 1)): 
            return "OBSTACLE"
        
        # Only check if mario is within the game board (aka not dead)
        if self.mario_row < 16:
            # Check if Mario is currently on top of a block (either 10 or 14)
            block_below_mario = self.environment.game_area()[self.mario_row + 1][self.mario_col]
            if block_below_mario in [10, 14]:
                # Check for a gap directly below and 1 block in front of Mario using gaps_np
                gap_below_and_front = (self.gaps_np[:, 0] == self.mario_row + 1) & \
                                    (self.gaps_np[:, 1] == self.mario_col + 1)
                if np.any(gap_below_and_front):
                    return "GAP"
                
        # Check if the jumping bug is there
        if len(self.jumping_bug_np) != 0 and any(self.jumping_bug_np[:, 1] > self.mario_col):
            return "JUMPING BUG"
        
        # Switch to enemies state
        if self.current_state == "DEFAULT":
            
            if len(self.goombas_np) != 0:
                return "ENEMIES"
            
        # Check whether enemies are above or below mario
        elif self.current_state == "ENEMIES" or "GOOMBA ABOVE":
            for goomba_row, goomba_col in self.goombas_np:
                print(f"Goomba at Row: {goomba_row}, Col: {goomba_col}")
                if goomba_row < self.mario_row - 1:
                    return "GOOMBA ABOVE"
                elif goomba_row > self.mario_row:
                    return "GOOMBA BELOW"
            return "ENEMIES"
        
        return "DEFAULT"
            
    def choose_action(self, action = 2):
        # Update the game state with the latest information
        self.scan_frame()
        state = self.environment.game_state()
        frame = self.environment.grab_frame()

        # FSM Transition
        self.current_state = self.fsm_transition()
        print(self.current_state)

        # Default hold freq
        hold_freq = 10

        # Evaluates what action to do
        # Default jumping actions
        if self.current_state == "UNDER + GOOMBA":
            action = 6
            hold_freq = 100

        if self.current_state == "OBSTACLE":
            hold_freq = 15
            action = 4
        
        if self.current_state == "GAP":
            hold_freq = 30
            action = 6

        if self.current_state == "ENEMIES":
            for goomba_row, goomba_col in self.goombas_np:
                if goomba_col - self.mario_col < 3 and goomba_col >= self.mario_col:
                    hold_freq = 15 # for some reason need this or "GAP" doesnt work
                    action = 4  

        # If a goomba is above mario
        elif self.current_state == "GOOMBA ABOVE":
        # Move forward until 4 blocks from a wall if Goomba is above
            wall_in_front = False
            for obstacle_row, obstacle_col in self.obstacles_np:
                if obstacle_row == self.mario_row and (obstacle_col - self.mario_col) <= 6:
                    wall_in_front = True
                    print("the wall is in front")
                    break
            
            if wall_in_front:
                print("Pausing, waiting for Goomba to drop")
                action = -1  # Pause action
                #self.current_state = "ENEMIES"  # Change state back to ENEMIES
            else:
                # print("Moving forward to avoid Goomba above")
                action = 2  # Move forward action
                hold_freq = 1
        
        # If a goomba is below
        elif self.current_state == "GOOMBA BELOW":
            for goomba_row, goomba_col in self.goombas_np:
                hold_freq = 1
                #if goomba is on the right
                if goomba_col > self.mario_col:
                    print("moving right")
                    action = 2
                # If the goomba is to the left of mario, move left so mario lands on it unless the goomba is too far
                elif goomba_col - 1 < self.mario_col and self.mario_col - goomba_col < 2 :
                    print("moving left")
                    action = 1
                else:
                    print("stomping")
                    action = -1

        # Jumping bug stuff
        elif self.current_state == "JUMPING BUG":
            for bug_row, bug_col in self.jumping_bug_np:
                if bug_col - self.mario_col < 3 and bug_col >= self.mario_col:
                    hold_freq = 15 # for some reason need this or "GAP" doesnt work
                    action = 4  
                

        print(action)
        # action = -1 #uncomment for manual mode
        return action, hold_freq


    def step(self):
        """
        Modify this function as required to implement the Mario Expert agent's logic.

        This is just a very basic example
        """

        # Choose an action - button press or other...
        action, hold_freq = self.choose_action()

        # Run the action on the environment
        self.environment.run_action(action, hold_freq)
        self.previous_action = action

    def play(self):
        """
        Do NOT edit this method.
        """
        self.environment.reset()

        frame = self.environment.grab_frame()
        height, width, _ = frame.shape

        self.start_video(f"{self.results_path}/mario_expert.mp4", width, height)

        while not self.environment.get_game_over():
            frame = self.environment.grab_frame()
            self.video.write(frame)

            self.step()

        final_stats = self.environment.game_state()
        logging.info(f"Final Stats: {final_stats}")

        with open(f"{self.results_path}/results.json", "w", encoding="utf-8") as file:
            json.dump(final_stats, file)

        self.stop_video()

    def start_video(self, video_name, width, height, fps=30):
        """
        Do NOT edit this method.
        """
        self.video = cv2.VideoWriter(
            video_name, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
        )

    def stop_video(self) -> None:
        """
        Do NOT edit this method.
        """
        self.video.release()
