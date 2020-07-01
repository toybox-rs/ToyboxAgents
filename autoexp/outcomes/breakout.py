# Outcomes may not be valid at every timestep.
# Outcomes must be binary
import json
from typing import List, Tuple, Optional

from ctoybox import Toybox
from toybox.interventions.breakout import Breakout
from toybox.envs.atari.base import ACTION_MEANING

from . import *
from agents.base import action_to_string

class StagnantBall(OutcomeException):

    def __init__(self, frames: List[Breakout], window):
        super().__init__('No change in ball y position for {} consecutive states.'.format(window))
        self.frames = frames
        self.window = window

    def write_frame_images(self):
        for i, frame in enumerate(self.frames):
            f = 'debug_stagnant_ball_' + str(i).zfill(3) + '.png'
            Toybox('breakout', withstate=frame.encode()).save_frame_image(f)

    def write_frame_state(self):
        for i, frame in enumerate(self.frames):
            with open('debug_stagnant_ball_' + str(i).zfill(3) + '.json', 'w') as f:
                json.dump(frame.encode(), f)


def direction(pairs) -> Optional[int]:
    """Returns the direction the ball is travelling in.

    Semantics of return values:
    - None: The ball changed direction in this window
    - 0: The ball did not move in the window
    - +1: The ball moved to the right
    - -1: The ball moved to the left
    """
    ball_dir = 0

    for i, (s1, _) in enumerate(pairs[:-1]):
      s2 = pairs[i+1][0]

      if len(s1.balls) and len(s2.balls):
        diff = s2.balls[0].position.x - s1.balls[0].position.x  
        if ball_dir == 0: 
          ball_dir = sign(diff)
          continue  
        if diff == 0: continue  
        if (ball_dir > 0 and diff < 0) or (ball_dir < 0 and diff > 0):
          # ball changed direction
          return None
        
        ball_dir = sign(diff)
    
    return ball_dir


class ActionTaken(Outcome):

    def __init__(self, action):
        super().__init__(1)
        self.action = action

    def outcomep(self, pairs):
        InadequateWindowError.check_window(pairs, self.minwindow, ActionTaken)
        return pairs[0][1] == self.action


class MissedBall(Outcome):

    def __init__(self):
        super().__init__(2)

    def outcomep(self, pairs):
        # We need at least two states in order to tell if we've missed
        InadequateWindowError.check_window(pairs, self.minwindow, MissedBall)
        # If we have 0 balls at tn, but we had at least one
        # at tn-1, then we have missed
        last_state = pairs[-1][0]
        pen_state = pairs[-2][0]
        if last_state is None:
            return True
        elif len(last_state.balls) == 0:
            return len(pen_state.balls) > 0
        else:
            pen_ball_y = pen_state.balls[0].position.y 
            pen_pad_y  = pen_state.paddle.position.y
            last_ball_y = last_state.balls[0].position.y 
            last_pad_y = last_state.paddle.position.y
            return  pen_ball_y > pen_pad_y and last_ball_y > last_pad_y

class HitBall(Outcome):

    def __init__(self):
        super().__init__(3)

    def outcomep(self, pairs):
        # We need at least three states in order to tell if we've hit the ball
        InadequateWindowError.check_window(pairs, self.minwindow, HitBall)
        # before: heading down
        # after: heading up
        states = [p[0] for p in pairs]
        # heading down --> positive diff
        # heading up --> negative diff
        # don't want multiple hits
        heading_down = None
        diffs = []
        for s1, s2 in zip(states[:-1], states[1:]):

            # We have missed the ball; therefore, we have not hit the ball
            if not (len(s1.balls) and len(s2.balls)): 
                return False

            diff = s2.balls[0].position.y - s1.balls[0].position.y
            diffs.append(diff)

            if heading_down is None: # not yet set               
                if diff < 0: 
                    return False # heading up at the start
                if diff > 0: 
                    heading_down = True    
            elif heading_down is True:
                if diff < 0: 
                    heading_down = False
            elif heading_down is False:
                if diff > 0: 
                    return False # window too big   

        if all([d == 0 for d in diffs]):
            e = StagnantBall([t[0] for t in pairs], len(pairs))
            e.write_frame_images()
            e.write_frame_state()
            raise e 
        return heading_down is False 

class MoveSame(Outcome):

    def __init__(self):
        # 1/ 3^4 ~= 0.01
        super().__init__(4)

    def outcomep(self, pairs):
        InadequateWindowError.check_window(pairs, self.minwindow, MoveSame)

        prevs = [p[0] for p in pairs[:-1]]
        states = [p[0] for p in pairs[1:]]
        actions = [p[1] for p in pairs[1:]]    
        ball_dir = direction(pairs)
        same_dir = 0   

        # Either the window is too big, or the paddle and ball 
        # made contact; either way, this is not an appropriate 
        # outcome for that context.
        if ball_dir is None or ball_dir == 0: return False
    
        for s1, s2, a in zip(prevs, states, actions):
          a = action_to_string(a)

          if len(s1.balls) and len(s2.balls):
            if ball_dir > 0: # ball is moving right
              if a.upper().strip() == 'RIGHT': same_dir += 1
            elif ball_dir < 0:
              if a.upper().strip() == 'LEFT': same_dir += 1  
        return same_dir > (len(pairs) / 2.)



class MoveOpposite(Outcome):
    # cases where the ball is traveling in one direction, 
    # but the agent moves in the opposite direction,
    # for over 50% of the pairs

  def __init__(self):
    super().__init__(4)

  def outcomep(self, pairs):
    # ball must be moving in the same direction for the whole window

    # We need at least two states to determine direction 
    InadequateWindowError.check_window(pairs, self.minwindow, MoveOpposite)

    prevs = [p[0] for p in pairs[:-1]]
    states = [p[0] for p in pairs[1:]]
    actions = [p[1] for p in pairs[1:]]    
    ball_dir = direction(pairs)
    against_dir = 0    
    
    if ball_dir is None or ball_dir == 0: return False
    
    for s1, s2, a in zip(prevs, states, actions):
      a = action_to_string(a)

      if len(s1.balls) and len(s2.balls):
        if ball_dir > 0: # ball is moving right
          if a.upper().strip() == 'LEFT': against_dir += 1
        elif ball_dir < 0:
          if a.upper().strip() == 'RIGHT': against_dir += 1  
    return against_dir > (len(pairs) / 2.)


class MoveAway(Outcome):
    # Move Opposite + distance increasing

  def __init__(self):
    super().__init__(4)

  def outcomep(self, pairs):
    InadequateWindowError.check_window(pairs, self.minwindow, MoveAway)

    if MoveOpposite().outcomep(pairs):
    
        away_dir = 0  

        for i, (s1, a) in enumerate(pairs[:-1]):
          s2 = pairs[i+1][0]

          if len(s1.balls) and len(s2.balls):
            diff1 = abs(s1.balls[0].position.x - s1.paddle.position.x)
            diff2 = abs(s2.balls[0].position.x - s2.paddle.position.x)
            diff = diff2 - diff1
            moving = s1.paddle.position.x - s2.paddle.position.x

            if diff > 0 and moving:
              away_dir += 1

        return away_dir > (len(pairs) / 2.)
        
    else: return False


class MoveToward(Outcome):

    def __init__(self):
        super().__init__(4)

    def outcomep(self, pairs):
        InadequateWindowError.check_window(pairs, self.minwindow, MoveToward)

        tow_dir = 0  

        for i, (s1, a) in enumerate(pairs[:-1]):
          s2 = pairs[i+1][0]

          if len(s1.balls) and len(s2.balls):
            diff1 = abs(s1.balls[0].position.x - s1.paddle.position.x)
            diff2 = abs(s2.balls[0].position.x - s2.paddle.position.x)
            diff = diff2 - diff1
            moving = s1.paddle.position.x - s2.paddle.position.x

            if diff < 0 and moving:
              tow_dir += 1

        return tow_dir > (len(pairs) / 2.)


class Aim(Outcome):
    """An agent is aiming if the region of interest of the paddle remains within some epsilon of the ball's x position."""

    def __init__(self, location):
        super().__init__(2)
        self.location = location

    def __str__(self):
        return self.__class__.__name__ + self.location.capitalize()

    def compute_center(self, state):
        if self.location == 'up':
            return state.paddle.position.x
        elif self.location == 'left':
            return state.paddle.position.x - (state.paddle_width / 2)
        elif self.location == 'right':
            return state.paddle.position.x + (state.paddle_width / 2)
        else: assert False

    def outcomep(self, pairs):
        # Two data points seems too small, but we can update this later
        InadequateWindowError.check_window(pairs, self.minwindow, Aim)
        for s, _ in pairs:
            if not len(s.balls): continue
            eps = s.paddle_width / 4.
            paddle_center = self.compute_center(s)
            ballx = s.balls[0].position.x
            diff = abs(paddle_center - ballx)
            if diff > eps: return False
        return True


if __name__ == "__main__":
    # load up data from Target agent
    from ctoybox import Toybox
    from typing import Dict
    import os, json

    with Toybox('breakout') as tb:
        target_dir = 'analysis/data/raw/Target'
        data : List[Breakout] = []
        agent = 'Target'
        actions : List[str] = []
        for seed in sorted(os.listdir(target_dir)):
            for f in sorted(os.listdir(target_dir + os.sep + agent + os.sep + seed)):
                fullname = target_dir + os.sep + seed + os.sep + f
                if f.endswith('json'):
                    with open(fullname, 'r') as js:  
                        data.append(Breakout.decode(tb, json.load(js), Breakout))
                if f.endswith('act'):
                    with open(fullname, 'r') as acts:
                        actions = acts.readlines()

            sapairs = list(zip(data, actions if len(actions) == len(data) else actions + ['']))
            for i in range(len(sapairs) - 4):
                missed = MissedBall()
                hit = HitBall()
                oppo = MoveOpposite()
                away = MoveAway()
                aim_right = Aim('right')
                aim_left = Aim('left')
                

                this_slice = sapairs[i:i+5]
                assert len(this_slice) == 5

                outcomes = [
                    ('MissedBall', missed),
                    ('HitBall', hit),
                    ('MoveOpposite', oppo),
                    ('MoveAway', away),
                    ('AimRight', aim_right),
                    ('AimLeft', aim_left)
                ]

                for (name, outcome) in outcomes:
                    if outcome.outcomep(this_slice):
                        path = 'outcomes' + os.sep + name + os.sep + seed + os.sep + str(i)
                        os.makedirs(path, exist_ok=True)
                        for j, (state, _) in enumerate(this_slice):
                            tb.write_state_json(state.encode())
                            tb.save_frame_image(path + os.sep + str(j).zfill(5) + '.png')
            
