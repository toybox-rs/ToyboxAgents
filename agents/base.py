from abc import ABC, abstractmethod
from ctoybox import Toybox, Input
import os


class Agent(ABC):

    def __init__(self, toybox: Toybox):
        self.toybox = toybox
        self.name = self.__class__.__name__
        self.frame_counter = 0

    def _next_file(self, path):
        self.frame_counter += 1
        return path + os.sep + self.name + str(self.frame_counter).zfill(5)

    def save_data(self, path: str):
        f = self._next_file(path)
        img = f + '.png'
        json = f + '.json'
        self.toybox.save_frame_image(img)
        with open(json, 'w') as ff:
            ff.write(str(self.toybox.state_to_json()))

    @abstractmethod
    def get_action(self) -> Input: pass

    def play(self, path, maxsteps):
        self.save_data(path)

        while not self.toybox.game_over() and self.frame_counter < maxsteps:
            action = self.get_action()
            if action:
                self.toybox.apply_action(action)
                self.save_data(path)
            else: return 