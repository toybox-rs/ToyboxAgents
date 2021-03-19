from agents.base import Agent
from ctoybox import Toybox, Input
import toybox.interventions.amidar as amidar


class AmidarAgent(Agent):

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

  def play(self, *args, **kwargs):
    #input = Input()
    super().play(*args, **kwargs)