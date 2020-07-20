from . import Composite, Atomic
from ctoybox import Toybox
from toybox.interventions import Game
from toybox.interventions.core import distr, get_property
from toybox.interventions.breakout import BreakoutIntervention

import importlib
import random
import math

from typing import Tuple


class TopRowColor(Composite):

  def __init__(self, modelmod):
    super().__init__('top_row_color', modelmod)
    self.atomicvars = []
    for i in range(18):
      self.atomicvars.append('bricks[{}].color.r'.format(i))
      self.atomicvars.append('bricks[{}].color.g'.format(i))
      self.atomicvars.append('bricks[{}].color.b'.format(i))

  def get(self, g:Game):
    row = [b for b in g.bricks if b.row == 0]
    first = row[0]
    return first.color.r << 16 + first.color.g << 8 + first.color.b

  def set(self, v: Tuple[int, int, int], g: Game):
    red, green, blue = v
    for varname in self.atomicvars:
      get_property(g, varname, setval=red if varname.endswith('r') else green if varname.endswith('g') else blue)

  def make_models(self, d): pass

  def sample(self, g:Game):
    before = self.get(g)
    # after = int(self._sample_composite())
    # red = (after & 0xff0000) >> 16
    # green = (after & 0x00ff00) >> 8
    # blue = after & 0x0000ff
    # self.set((red, green, blue), g)
    red = Atomic(self.modelmod, 'bricks[0].color.r').sample(g)
    green = Atomic(self.modelmod, 'bricks[0].color.g').sample(g)
    blue = Atomic(self.modelmod, 'bricks[0].color.b').sample(g)
    self.set((red, green, blue), g)
    after = self.get(g)
    return before, after


class XDistanceBallPaddle(Composite):

  def __init__(self, modelmod):
    super().__init__('xdist_ball_paddle', modelmod)
    # later change this so it is automatically generated
    self.atomicvars = [
      'balls[0].position.x',
      'paddle.position.x'
    ]
    
  def get(self, g: Game):
    if len(g.balls):
      return abs(g.balls[0].position.x - g.paddle.position.x)
    else: return -1

  def set(self, v: int, g: Game):
    # randomly select which corevar will be set first
    ivar_name = random.choice(self.atomicvars)
    # sample a value for the independent variable
    ivar_value = self._sample_var(ivar_name)
    # compute the two possible values of the dependent variable
    dvar_value_plus  = ivar_value + v
    dvar_value_minus = ivar_value - v
    # randomly select which of the two values we want
    dvar = random.choice([dvar_value_minus, dvar_value_plus])
    
    # set the two variables in the state object
    get_property(g, ivar_name, setval=ivar_value)
    get_property(g, [p for p in self.atomicvars if not p == ivar_name][0], setval=dvar)


  def sample(self, g: Game):
    before = self.get(g)
    # This is basically a likelihood function
    # sample a distance
    after = self._sample_composite()
    self.set(after, g)
    return before, after


class YDistanceBallPaddle(Composite):
  
  def __init__(self, modelmod):
    super().__init__('ydist_ball_paddle', modelmod)
    self.atomicvars = [
      'balls[0].position.y',
      'paddle.position.y'
    ]

  def get(self, g:Game):
    if len(g.balls):
      return abs(g.balls[0].position.y - g.paddle.position.y)
    else: return -1

  def set(self, v:int, g:Game):
    ivar_name = random.choice(self.atomicvars)
    ivar_value = self._sample_var(ivar_name)
    # paddle must always be lower than the ball
    if 'ball' in ivar_name:
      dvar_value = v + ivar_value
    else:
      dvar_value = ivar_value - v
    get_property(g, ivar_name, setval=ivar_value)
    get_property(g, self.atomicvars[0] if 'paddle' in ivar_name else self.atomicvars[1], setval=dvar_value)


  def sample(self, g:Game):
    before = self.get(g)
    after = self._sample_composite()
    self.set(after, g)
    return before, after


class BoardConfig(Composite):

  def __init__(self, modelmod):
    super().__init__('board_config', modelmod)
    with Toybox('breakout') as tb:
      with BreakoutIntervention(tb) as intervention:
        bricks = intervention.game.bricks
        self.atomicvars = ['bricks[{}].alive'.format(i) for i in range(len(bricks))]

  def get(self, g:Game):
    return sum([2**i for i, brick in enumerate(g.bricks) if brick.alive])

  def set(self, v:int, g:Game):
    counter = 0
    shifted = v
    while counter < len(g.bricks):
      get_property(g, 'bricks[{}].alive'.format(counter), setval=bool(shifted != (shifted >> 1 << 1)))
      shifted >>= 1
      counter += 1    
  
  def sample(self, g:Game):
    before = self.get(g)
    after = min(2**108-1, max(0, int(self._sample_composite())))
    self.set(after, g)
    return before, after


def L2DistanceBallPaddle(Composite):

  def __init__(self, modelmod):
    super().__init__('l2dist_ball_paddle', modelmod)
    self.compositevars = [
        XDistanceBallPaddle(self.modelmod),
        YDistanceBallPaddle(self.modelmod)
      ]
    self.atomicvars = super()._get_atomic_from_composite()

  def get(self, g:Game):
    xdist = self._get_composite(XDistanceBallPaddle)
    ydist = self._get_composite(YDistanceBallPaddle)
    return (xdist.get()**2 + ydist.get()**2)**(1/2)

  def set(self, v:int, g:Game):
    random.shuffle(self.compositevars)
    ivar_obj, dvar_obj = self.compositevars
    # This will set the ivar in the process
    _, _, ivar = ivar_obj.sample(g)
    # Now we just need to set the dvar
    if random.random() < 0.5:
      dvar_obj.set(ivar + v, g)
    else:
      dvar_obj.set(ivar - v, g)


  def sample(self, g:Game):
    before = self.get(g)
    after = self._sample_composite()
    self.set(after, g)
    return before, after

if __name__ == '__main__':
  bc = BoardConfig('models.breakout.target')
  # check inversion
  with Toybox('breakout') as tb:
    with BreakoutIntervention(tb) as intervention:
      game = intervention.game
      full_board = 2**108 - 1
      to_set = 12345

      assert bc.get(game) == full_board

      bc.set(to_set, game)
      assert bc.get(game) == to_set
      
      bc.set(full_board, game)
      set_to = bc.get(game)
      assert set_to == full_board, '{} vs {} (diff: {})'.format(set_to, full_board, set_to - full_board)

     


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