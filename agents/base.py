from abc import ABC, abstractmethod
from ctoybox import Toybox, Input

_frame_counter = 0

class Agent(ABC):

    def __init__(self, toybox: Toybox):
        self.toybox = toybox
        self.name = self.__class__.__name__

    @abstractmethod
    def get_action(self) -> Input: pass

    def play(self, path, maxsteps=100):
        import os

        def next_file():
            global _frame_counter 
            _frame_counter += 1
            return path + os.sep + self.name + str(_frame_counter).zfill(5) + '.png'

        self.toybox.save_frame_image(next_file())
        while not self.toybox.game_over() and _frame_counter < maxsteps:
            action = self.get_action()
            self.toybox.apply_action(action)
            self.toybox.save_frame_image(next_file())