from abc import ABC, abstractmethod
from typing import Union, List
from ctoybox import Toybox, Input
from toybox.envs.atari.constants import ACTION_MEANING
from toybox.interventions import Game, state_from_toybox
import os, signal

try:
    import ujson 
except: 
    import json as ujson

import random

def action_to_string(action: Union[Input, int, str]):
    if action is None: 
        return 'noop'
    if type(action) == str: 
        return action
    if type(action) == int:
        return ACTION_MEANING[action]
    elif isinstance(action, Input):
        if action.left:
            return 'left'
        elif action.right:
            return 'right'
        elif action.up:
            return 'up'
        elif action.down:
            return 'down'
        elif action.button1:
            return 'button1'
        elif action.button2:
            return 'button2'
        else:
            return 'noop'
    else: assert False


def string_to_input(action: str) -> Input:
    actobj = Input()
    if action is None or action == '':
        return actobj
    if action == 'left':
        actobj.left = True
        return actobj
    if action == 'right':
        actobj.right = True
        return actobj
    if action == 'up':
        actobj.up = True
        return actobj
    if action == 'down':
        actobj.down = True
        return actobj
    if action == 'fire' or action == 'button1':
        actobj.button1 = True
        return actobj
    if action == 'button2':
        actobj.button2 = True
        return actobj



class Agent(ABC):

    def __init__(self, toybox: Toybox, seed = 1234):
        self.toybox = toybox
        self.name = self.__class__.__name__
        self.frame_counter = 0
        self.actions : List[Union[str, int]] = []
        self.states : List[Game] = []
        self._reset_seed(seed)

    def _reset_seed(self, seed):
        self.seed = seed
        self.toybox.set_seed(seed)
        random.seed(seed)

    def _next_file(self, path):
        self.frame_counter += 1
        return path + os.sep + self.name + str(self.frame_counter).zfill(5)

    def write_data(self, path: str, write_json_to_file, save_states):
        if write_json_to_file:
            f = self._next_file(path)
            img = f + '.png'
            json = f + '.json'
            self.toybox.save_frame_image(img)
            with open(json, 'w') as ff:
                ujson.dump(self.toybox.state_to_json(), ff)
        

    def save_actions(self, path):
        os.makedirs(path, exist_ok=True)
        with open(path + os.sep + self.name + '.act', 'w') as f:
            for action in self.actions:
                f.write(action_to_string(action)+'\n')

    def kill_and_record(self, path):
        def inner(sig, frame):
            self.save_actions(path)
            exit(0)
        return inner

    @abstractmethod
    def get_action(self) -> Input: pass

    def reset(self, seed=None):
        self.states = []
        self.actions = []
        self.frame_counter = 0
        if seed:
            self._reset_seed(seed)

    def step(self, path, write_json_to_file, save_states):
        action = self.get_action()
        self.actions.append(action)

        if action is not None:
            if isinstance(action, Input):
                self.toybox.apply_action(action)
            elif type(action) == int:
                self.toybox.apply_ale_action(action)
            else: assert False
        
        if write_json_to_file:
            self.write_data(path, write_json_to_file, save_states)
        else: self.frame_counter += 1

        if save_states:
            self.states.append(state_from_toybox(self.toybox))
            


    def play(self, path=None, maxsteps=2000, write_json_to_file=True, save_states=False, startstate=None):
        # set the signal handler to save actions when we are interrupted.
        signal.signal(signal.SIGINT, self.kill_and_record(path))
        signal.signal(signal.SIGTERM, self.kill_and_record(path))
        
        if path: os.makedirs(path, exist_ok=True)
        if startstate: self.toybox.write_state_json(startstate.encode())
        self.write_data(path, write_json_to_file, save_states)

        while not self.toybox.game_over() and self.frame_counter <= maxsteps:
            # print('STEP', self.frame_counter, maxsteps)
            self.step(path, write_json_to_file, save_states)
 
        if path: self.save_actions(path)