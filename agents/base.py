from abc import ABC, abstractmethod
from ctoybox import Toybox, Input

class Agent(ABC):

    def __init__(self, toybox: Toybox):
        self.toybox = toybox

    @abstractmethod
    def get_action(self) -> Input: pass

    def play(self, path):
        self.toybox.save_frame_image(path)
        while not self.toybox.game_over():
            action = self.get_action()
            self.toybox.apply_action(action)
            self.toybox.save_frame_image(path)