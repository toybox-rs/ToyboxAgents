from . import Composite
from toybox.interventions import Game
from toybox.interventions.breakout import query_hack
from toybox.interventions.core import distr, get_property

import random
import importlib

class XDistanceBallPaddle(Composite):

  def __init__(self, modelmod):
    super().__init__('xdist_ball_paddle', modelmod)
    # later change this so it is automatically generated
    self.atomicvars = [
      'balls[0].position.x',
      'paddle.position.x'
    ]
    
  def get(self, g: Game):
    return abs(g.balls[0].position.x - g.paddle.position.x)

  def sample(self, g: Game):
    before = self.get(g)
    # This is basically a likelihood function
    mod = importlib.import_module(self.modelmod + '.' + self.name)
    # sample a distance
    after = mod.sample()
    # randomly select which corevar will be set first
    ivar_name = random.choice(self.corevars)
    # sample a value for the independent variable
    ivar = importlib.import_module(self.modelmod + '.' + query_hack(ivar_name))
    ivar_value = ivar.sample()
    # compute the two possible values of the dependent variable
    dvar_value_plus  = ivar_value + after
    dvar_value_minus = ivar_value - after
    # randomly select which of the two values we want
    dvar = random.choice([dvar_value_minus, dvar_value_plus])
    
    # set the two variables in the state object
    get_property(g, ivar_name, setval=ivar_value)
    get_property(g, [p for p in self.corevars if not p == ivar_name][0], setval=dvar)

    return before, g, after


class LeftmostBrick(Composite):

  def __init__(self, modelmod):
    self.atomicvars


# have a var for each color
# example of aggregating over an attribute, e.g. brick color or row color
# discussion of the mechanistic aspect of r vs rgb (color)



        
#             col_channels = int("".join([int(query.is_channel(col)) for col in [query.get_column(i) for i in range(len(query.num_columns()))]]), 2)
#             leftmost_brick = query.get_column(0)[0]
#             rightmost_brick = query.get_column(query.num_columns() - 1)[0]
#             paddle_far_left = paddlex <= (leftmost_brick.position.x - (leftmost_brick.size.x if leftmost_brick.size.x > leftmost_brick.size.y else leftmost_brick.y))
#             paddle_far_right = paddlex >= (rightmost_brick.position.x - (rightmost_brick.size.x if rightmost_brick.size.x > rightmost_brick.size.y else rightmost_brick.y))
#             xdist_ball_paddle = abs(ballx - paddlex)
#             ydist_ball_paddle = abs(bally - paddley)
#             l2_ball_paddle = math.sqrt(xdist_ball_paddle^2 + ydist_ball_paddle^2)
#             bricks_alive = sum([int(b.alive) for b in state.bricks])