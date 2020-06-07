from record import Record
import toybox.interventions.breakout as breakout
from typing import List
from collections import namedtuple
import math
from ctoybox import Toybox

# start super basic

class Derived(ABV)

# def make_data(agentid: str, seed: int, states: List[breakout.Breakout], actions: List[str]):
#     with Toybox('breakout') as tb:
#         config = tb.config_to_json()
#     with open('dat.csv', 'w') as f:
#         query = breakout.BreakoutIntervention(namedtuple('tb', 'game_name')('breakout'), 'breakout')
#         initial_paddle_width = states[0].paddle_width
#         for t in range(states):
#             state = states[t]
#             query.game = state
#             # covariates
#             action = action[t]
#             missed_ball = len(state.balls) > 0
#             ballx = state.balls[0].position.x if not missed_ball else None
#             bally = state.balls[0].position.y if not missed_ball else None
#             prev_ballx = states[t-1].balls[0].position.x if t > 0 and len(state[t-1].balls) > 0 else None
#             prev_bally = states[t-1].balls[0].position.y if t > 0 and len(state[t-1].balls) > 0 else None
#             paddlex = states[t].paddle.position.x
#             paddley = states[t].paddle.position.y
#             col_channels = int("".join([int(query.is_channel(col)) for col in [query.get_column(i) for i in range(len(query.num_columns()))]]), 2)
#             leftmost_brick = query.get_column(0)[0]
#             rightmost_brick = query.get_column(query.num_columns() - 1)[0]
#             paddle_far_left = paddlex <= (leftmost_brick.position.x - (leftmost_brick.size.x if leftmost_brick.size.x > leftmost_brick.size.y else leftmost_brick.y))
#             paddle_far_right = paddlex >= (rightmost_brick.position.x - (rightmost_brick.size.x if rightmost_brick.size.x > rightmost_brick.size.y else rightmost_brick.y))
#             score = state.score
#             paddle_width = 'big' if state.paddle_width == initial_paddle_width else 'small'
#             ball_speed = None if missed_ball else 'slow' if math.isclose(state.balls[0].velocity.y, config['ball_speed_slow']) else 'fast'
#             downward = None if missed_ball else state.balls[0].velocity.y > 1
#             xdist_ball_paddle = abs(ballx - paddlex)
#             ydist_ball_paddle = abs(bally - paddley)
#             l2_ball_paddle = math.sqrt(xdist_ball_paddle^2 + ydist_ball_paddle^2)
#             bricks_alive = sum([int(b.alive) for b in state.bricks])
#             record = [agentid, seed, t, action, missed_ball, ballx, bally, prev_ballx, prev_bally, paddlex, col_channels, paddle_far_left, paddle_far_right, score, paddle_width, ball_speed, downward, l2_ball_paddle, ydist_ball_paddle, xdist_ball_paddle, bricks_alive]
#             f.write(','.join(record))