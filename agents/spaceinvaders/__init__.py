from abc import abstractmethod

from agents.base import Agent
from ctoybox import Toybox, Input
import toybox.interventions.space_invaders as spaceinvaders

class SpaceInvadersAgent(Agent):

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

  @abstractmethod
  def get_action(self) -> Input: pass

  def play(self, *args, **kwargs):
    #input = Input()
    super().play(*args, **kwargs)