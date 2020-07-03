from . import Composite
from toybox.interventions import Game
from toybox.interventions.core import distr, get_property

import random
import importlib


class TopRowColor(Composite):

  def __init__(self, modelmod):
    super().__init__('top_row_color', modelmod)
    self.atomicvars = []
    for i in range(18):
      self.atomicvars.append('bricks[{}].color.r'.format(i))
      self.atomicvars.append('bricks[{}].color.g'.format(i))
      self.atomicvars.append('bricks[{}].color.b'.format(i))

  def get(self, g:Game):
    row = g.intervention.get_row(0)
    first = row[0]
    return first.color.r << 16 + first.color.g << 8 + first.color.b

  def sample(self, g:Game):
    before = self.get(g)
    after = int(self._sample_composite())
    r = (after & 0xff0000) >> 16
    g = (after & 0x00ff00) >> 8
    b = after & 0x0000ff
    for varname in self.atomicvars:
      get_property(g, varname, setval=r if varname.endswith('r') else g if varname.endswith('g') else b)
    return before, g, after


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
    # sample a distance
    after = self._sample_composite()
    # randomly select which corevar will be set first
    ivar_name = random.choice(self.atomicvars)
    # sample a value for the independent variable
    ivar_value = self._sample_var(ivar_name)
    # compute the two possible values of the dependent variable
    dvar_value_plus  = ivar_value + after
    dvar_value_minus = ivar_value - after
    # randomly select which of the two values we want
    dvar = random.choice([dvar_value_minus, dvar_value_plus])
    
    # set the two variables in the state object
    get_property(g, ivar_name, setval=ivar_value)
    get_property(g, [p for p in self.atomicvars if not p == ivar_name][0], setval=dvar)

    return before, g, after


class YDistanceBallPaddle(Composite):
  
  def __init__(self, modelmod):
    super().__init__('ydist_ball_paddle', modelmod)
    self.atomicvars = [
      'balls[0].position.y',
      'paddle.position.y'
    ]

  def get(self, g:Game):
    return abs(g.balls[0].position.y - g.paddle.position.y)

  def sample(self, g:Game):
    before = self.get(g)
    after = self._sample_composite()
    ivar_name = random.choice(self.atomicvars)
    ivar_value = self._sample_var(ivar_name)
    # paddle must always be lower than the ball
    if 'ball' in ivar_name:
      dvar_value = after + ivar_value
    else:
      dvar_value = ivar_value - after
    get_property(g, ivar_name, setval=ivar_value)
    get_property(g, self.atomicvars[0] if 'paddle' in ivar_name else self.atomicvars[1], setvar=dvar_value)

    return before, g, after


class BoardConfig(Composite):

  def __init__(self, modelmod):
    super().__init__('board_config', modelmod)
    self.atomicvars = ['bricks[{}].alive'.format(i) for i in range(108)]

  def get(self, g:Game):
    return sum([2^i for i, brick in enumerate(g.bricks) if brick.alive])

  def sample(self, g:Game):
    # [0, 7] -- 5 = 101
    before = self.get(g)
    after = min(2**107, max(0, int(self._sample_composite())))
    counter = 0
    shifted = after
    while counter < 108:
      get_property(g, 'bricks[{}].alive'.format(counter), setval=bool(shifted != (shifted >> 1 << 1)))
      shifted >>= 1
      counter += 1
    return before, g, after






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