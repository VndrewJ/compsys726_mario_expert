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
        act_freq: int = 10,
        emulation_speed: int = 1,
        headless: bool = False,
    ) -> None:
        super().__init__(
            act_freq=act_freq,
            emulation_speed=emulation_speed,
            headless=headless,
        )

        self.act_freq = act_freq

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

    def run_action(self, action: int) -> None:
        """
        This is a very basic example of how this function could be implemented

        As part of this assignment your job is to modify this function to better suit your needs

        You can change the action type to whatever you want or need just remember the base control of the game is pushing buttons
        """

        # Simply toggles the buttons being on or off for a duration of act_freq
        self.pyboy.send_input(self.valid_actions[action])

        for _ in range(self.act_freq):
            self.pyboy.tick()

        self.pyboy.send_input(self.release_button[action])

        # for _ in range(5):
        #     self.pyboy.tick()


class MarioExpert:
    """
    The MarioExpert class represents an expert agent for playing the Mario game.

    Edit this class to implement the logic for the Mario Expert agent to play the game.

    Do NOT edit the input parameters for the __init__ method.

    Args:
        results_path (str): The path to save the results and video of the gameplay.
        headless (bool, optional): Whether to run the game in headless mode. Defaults to False.
    """

    def __init__(self, results_path: str, headless=False):
        self.results_path = results_path

        self.environment = MarioController(headless=headless)

        self.video = None

    def choose_action(self, action = 2):
        state = self.environment.game_state()
        frame = self.environment.grab_frame()
        game_area = self.environment.game_area()
        mario_row = -1
        mario_col = -1
        question_blocks = []
        obstacles = []

        # Implement your code here to choose the best action
        # time.sleep(0.1)
        print(game_area)

        #convert game area to numpy array 
        game_area_np = np.array(game_area)

        #find mario's position
        mario_positions = np.where(game_area_np == 1)
        if mario_positions[0].size > 0 and mario_row == -1:
            mario_row = mario_positions[0][0] + 1
            mario_col = mario_positions[1][0] + 1
            print(f"Mario at Row: {mario_row}, Col: {mario_col}")

        # Track obstacles (10 or 14)
        obstacle_positions_10 = np.where(game_area_np == 10)
        obstacle_positions_14 = np.where(game_area_np == 14)
        # Combine the positions into a single array
        obstacles_np = np.column_stack((
            np.concatenate((obstacle_positions_10[0], obstacle_positions_14[0])),
            np.concatenate((obstacle_positions_10[1], obstacle_positions_14[1]))
        ))

        # Track goombas (15)
        goomba_positions = np.where(game_area_np == 15)
        goombas_np = goombas_np = np.column_stack((goomba_positions[0], goomba_positions[1]))

        #obstacle actions
        # for obstacle in obstacles:
        #     obstacle_row, obstacle_col = obstacle

        #     #jump over obstacle
        #     if obstacle_col == mario_col + 1 and (obstacle_row == mario_row - 2 or obstacle_row == mario_row - 1):
        #         action = 4
        #         break

        jump_needed = np.any(
            (obstacles_np[:, 1] == mario_col + 1) & 
            ((obstacles_np[:, 0] == mario_row - 1) | (obstacles_np[:, 0] == mario_row - 2))
        )

        if jump_needed:
            action = 4

        #goomba action, takes higher prio than obstacles
        for goomba in goombas_np:
            goomba_row, goomba_col = goomba

            #check if goomba is in front of mario between a range
            if goomba_col < mario_col + 5 and goomba_col > mario_col:
                #check if goomba is above do nothing until goomba falls down
                if goomba_row > mario_row:
                    action = -1

                #check if goomba is below
                if goomba_row < mario_row:
                    #idk bruh this ones hard
                    action = 2

                #check if goomba is same row
                if goomba_row == mario_row:
                    action = 4
            
        return action

        # Implement your code here to choose the best action
        # time.sleep(0.1)
        # return random.randint(0, len(self.environment.valid_actions) - 1)

    def step(self):
        """
        Modify this function as required to implement the Mario Expert agent's logic.

        This is just a very basic example
        """

        # Choose an action - button press or other...
        action = self.choose_action()

        # Run the action on the environment
        self.environment.run_action(action)

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
