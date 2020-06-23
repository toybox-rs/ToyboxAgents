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

    def __init__(self, toybox: Toybox, seed = 1234, action_repeat=1):
        self.toybox = toybox
        self.name = self.__class__.__name__
        self._frame_counter = 0
        self.action_repeat = action_repeat
        self.actions : List[Union[str, int]] = []
        self.states : List[Game] = []
        self._reset_seed(seed)

    def __str__(self):
        return self.__class__.__name__

    def _reset_seed(self, seed):
        self.seed = seed
        self.toybox.set_seed(seed)
        random.seed(seed)

    def next_frame_id(self):
        self._frame_counter += self.action_repeat
        return self._frame_counter

    def _next_file(self, path):
        fc = self.next_frame_id()
        return path + os.sep + self.name + str(fc).zfill(5)

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
        if not path: return
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
        self._frame_counter = 0
        if seed:
            self._reset_seed(seed)

    def step(self, path, write_json_to_file, save_states):
        action = self.get_action()
        self.actions.append(action)

        if action is not None:
            for a in [action] * self.action_repeat:
                if isinstance(a, Input):
                    self.toybox.apply_action(a)
                elif type(a) == int:
                    self.toybox.apply_ale_action(a)
                else: assert False
        
        if write_json_to_file and path:
            self.write_data(path, write_json_to_file, save_states)
        else: self.next_frame_id()

        if save_states:
            self.states.append(state_from_toybox(self.toybox))

    
    def stopping_condition(self, maxsteps, *args, **kwargs):
        return self.toybox.game_over() or self._frame_counter > maxsteps 


    def play(self, path=None, maxsteps=2000, write_json_to_file=True, save_states=False, startstate=None):
        # set the signal handler to save actions when we are interrupted.
        signal.signal(signal.SIGINT, self.kill_and_record(path))
        signal.signal(signal.SIGTERM, self.kill_and_record(path))
        
        if path: os.makedirs(path, exist_ok=True)
        if startstate: self.toybox.write_state_json(startstate.encode())
        self.write_data(path, write_json_to_file, save_states)

        maxsteps = abs(maxsteps) 

        while not self.stopping_condition(maxsteps):
            # if self._frame_counter % 10 == 0: print('STEP', self._frame_counter, maxsteps)
            self.step(path, write_json_to_file, save_states)
        
        if self._frame_counter <= maxsteps:
            self.actions.append(None)
            if save_states: self.states.append(None)
 
        if path: self.save_actions(path)