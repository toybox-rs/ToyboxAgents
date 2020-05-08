from abc import ABC, abstractmethod
from typing import Union
from ctoybox import Toybox, Input
from toybox.envs.atari.constants import ACTION_MEANING
import os, signal

try:
    import ujson 
except: 
    import json as ujson

import random

def action_to_string(action: Union[Input, int]):
    if type(action) == int:
        return ACTION_MEANING[action]
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
    else: assert False


class Agent(ABC):

    def __init__(self, toybox: Toybox):
        self.toybox = toybox
        self.name = self.__class__.__name__
        self.frame_counter = 0
        self.actions = []
        self.seed = 1234

    def reset_seed(self, seed):
        self.seed = seed
        random.seed(seed)


    def _next_file(self, path):
        self.frame_counter += 1
        return path + os.sep + self.name + str(self.frame_counter).zfill(5)

    def save_data(self, path: str):
        f = self._next_file(path)
        img = f + '.png'
        json = f + '.json'
        self.toybox.save_frame_image(img)
        with open(json, 'w') as ff:
            ujson.dump(self.toybox.state_to_json(), ff)

    def save_actions(self, path):
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

    def play(self, path, maxsteps):
        # set the signal handler to save actions when we are interrupted.
        signal.signal(signal.SIGINT, self.kill_and_record(path))
        signal.signal(signal.SIGTERM, self.kill_and_record(path))
        #signal.signal(signal.SIGKILL, self.kill_and_record(path))
        self.save_data(path)

        while not self.toybox.game_over() and self.frame_counter < maxsteps:
            action = self.get_action()
            if action is not None:
                if isinstance(action, Input):
                    self.toybox.apply_action(action)
                elif type(action) == int:
                    self.toybox.apply_ale_action(action)
                else: assert False
            else: break
            self.save_data(path)
            self.actions.append(action)

        assert len(self.actions) == self.frame_counter - 1 
        self.save_actions(path)