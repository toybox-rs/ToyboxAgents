from abc import abstractmethod

from agents.base import Agent
from ctoybox import Toybox, Input
import toybox.interventions.breakout as breakout

class BreakoutAgent(Agent):

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

  @abstractmethod
  def get_action(self) -> Input: pass

  def play(self, *args, **kwargs):
    # Breakout needs the agent to ask for a new ball to start the game
    input = Input()
    input.button1 = True
    self.toybox.apply_action(input)
    super().play(*args, **kwargs)