from . import *
from rl.agents.sarsa import SARSAAgent
from r.core import Processor
# should be able to remove this when we swap in tb stuff
from PIL import Image

class ToyboxProcessorImage(Processor):
    # Copied and modified from
    # https://github.com/keras-rl/keras-rl/blob/master/examples/dqn_atari.py
    def process_observation(self, tb: Toybox):
        assert observation.ndim == 3
        # I think we can just grab the grayscale from tb
        # then we won't need the next two lines
        img = Image.fromarray(observation)
        img = img.resize(INPUT_SHAPE).CONVERT('L')
        processed_observation


class SARSAImage(BreakoutAgent, SARSAAgent):
    pass
