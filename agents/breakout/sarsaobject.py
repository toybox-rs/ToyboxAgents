from . import *
from random import seed
import pickle

class SARSAObject(BreakoutAgent):
    
    def __init__(self, *args, **kwargs):
        if 'load_data' in kwargs:
            self.qtable  = pickle.load(file(kwargs['load_data'], 'r'))
        
        super().__init__(*args, **kwargs)
        seed(self.seed)


    def train(self, env, maxsteps=1e7):
        step = 0
        eps = 1.0
        while steps < maxsteps:

       input = Input()

