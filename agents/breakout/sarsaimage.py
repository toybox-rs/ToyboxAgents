from . import *
from rl.agents.sarsa import SARSAAgent
from r.core import Processor
# should be able to remove this when we swap in tb stuff
from PIL import Image

class ToyboxProcessorImage(Processor):
    # Copied and modified from
    # https://github.com/keras-rl/keras-rl/blob/master/examples/dqn_atari.py
    def process_observation(self, tb: Toybox):
        processed_observation = 


class SARSAImage(BreakoutAgent, SARSAAgent):
    pass
