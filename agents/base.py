from abc import ABC, abstractmethod
from ctoybox import Toybox, Input
import os
import ujson 
import random

def action_to_string(action: Input):
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

    @abstractmethod
    def get_action(self) -> Input: pass

    def play(self, path, maxsteps):
        self.save_data(path)

        while not self.toybox.game_over() and self.frame_counter < maxsteps:
            action = self.get_action()
            if action:
                self.toybox.apply_action(action)
                self.save_data(path)
                self.actions.append(action)
            else: break

        assert len(self.actions) == self.frame_counter - 1 

        with open(path + os.sep + self.name + '.act', 'w') as f:
            for action in self.actions:
                f.write(action_to_string(action)+'\n')