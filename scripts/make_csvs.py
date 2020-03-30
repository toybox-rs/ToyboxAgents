import sys, os
import argparse
import csv
import math
import ujson as json
import toybox.interventions.breakout as breakout
from typing import List
from collections import namedtuple
from ctoybox import Toybox
# I usually run this with outdir = $WORK1/ToyboxAgents/output

parser = argparse.ArgumentParser()
parser.add_argument('outdir')
parser.add_argument('agent')

args = parser.parse_args()

with open(args.outdir + os.sep + args.agent + os.sep + args.agent + '.act', 'r') as action_file:
    actions : List[str]  = action_file.readlines()

query = breakout.BreakoutIntervention(namedtuple('tb', 'game_name')('breakout'), 'breakout')
with Toybox('breakout') as tb:
    config = tb.config_to_json()
    query.config = config 

with open(args.outdir + os.sep + args.agent + '.csv', 'w') as outfile:

    datwriter = csv.writer(outfile, delimiter=',')
    # write the header
    datwriter.writerow([
        'agent_name', 
        'seed', 
        't', 
        'action', 
        'missed_ball', 
        'xpos_ball', 
        'ypos_ball', 
        'xpos_ball_prev',
        'ypos_ball_prev',
        'xpos_pad',
        'ypos_pad',
        'xpos_pad_prev',
        'ypos_pad_prev',
        'indicators',
        'is_far_left',
        'is_far_right',
        'score',
        'pad_width',
        'ball_speed',
        'ball_down',
        'xdist_ball_pad',
        'ydist_ball_pad',
        'l2_ball_pad',
        'num_bricks_left'])

    initial_paddle_width = None
    
    for seed in os.listdir(args.outdir + os.sep + args.agent):
        this_dir = args.outdir + os.sep + args.agent + os.sep + seed

        prev_state = None
        prev_t = 0
        records : List[List] = []

        for f in sorted(os.listdir(this_dir)):
            if f.endswith('json'):
                t = int(f[-9:-4])
                # Frames are 1-indexed.
                assert t != 0 
                assert t == prev_t + 1
                with open(this_dir + os.sep + f, 'r') as state_file:
                    state = breakout.Breakout.decode(None, json.load(state_file), breakout.Breakout)
                    query.game = state
                    if t == 1:
                        initial_paddle_width = state.paddle_width
                    record = [args.agent, seed, t]

                    record.append(actions[t])

                    missed_ball = len(state.balls) == 0
                    # missed_ball
                    record.append(missed_ball)
        
                    # Record the x and y coordinates of the ball and paddle at t and t-1
                    # Store intermediate values that we use later.
                    ball_pos = state.balls[0].position
                    paddle_pos = state.paddle.position

                    # xpos_ball
                    record.append(ball_pos.x if not missed_ball else None)
                    # ypos_ball
                    record.append(ball_pos.y if not missed_ball else None)
                    # xpos_ball_prev
                    record.append(prev_state.balls[0].position.x if prev_state else None)
                    # ypos_ball_prev
                    record.append(prev_state.balls[0].position.y if prev_state else None)
                    # xpos_pad
                    record.append(paddle_pos.x)
                    # ypos_pad
                    record.append(paddle_pos.y)
                    # xpos_pad_prev
                    record.append(prev_state.paddle.position.x if prev_state else None)
                    # ypos_pad_prev
                    record.append(prev_state.paddle.position.y if prev_state else None)

                    # The binary representation of this number indicates whether the 
                    # column at the ith bit is a channel
                    indicators = [query.get_column(i) for i in range(query.num_columns())]
                    # indicators
                    record.append(sum(2**i for i, v in enumerate(indicators) if v))

                    # Record whether the paddle is on the far left or far right of the screen
                    leftmost_brick = query.get_column(0)[0]
                    rightmost_brick = query.get_column(query.num_columns() - 1)[0]

                    record.append(paddle_pos.x <= (leftmost_brick.position.x - (leftmost_brick.size.x * 0.5)))
                    record.append(paddle_pos.x >= (rightmost_brick.position.x + (rightmost_brick.size.x * 0.5)))

                    # Record the score
                    record.append(state.score)

                    # Paddle width can be two sizes
                    record.append('big' if state.paddle_width == initial_paddle_width else 'small')

                    # Ball speed can have one of two values
                    record.append(None if missed_ball else \
                        'slow' if math.isclose(state.balls[0].position.y, 
                                               config['ball_speed_slow'], 
                                               rel_tol=0.1) \
                        else 'fast')

                    # Record whether the ball is travelling downward
                    # The origin is the top left, so downward movement increases the value of y
                    record.append(None if missed_ball else state.balls[0].velocity.y > 0)

                    # Different types of distances between balls and paddles
                    record.append(abs(ball_pos.x - paddle_pos.x))
                    record.append(abs(ball_pos.y - paddle_pos.y))
                    record.append(math.sqrt((ball_pos.x - paddle_pos.x)**2 + (ball_pos.y - paddle_pos.y)**2))

                    # Total bricks left
                    record.append(sum(int(b.alive) for b in state.bricks))

                    records.append(record)
                    prev_t = t
                    prev_t = state

        datwriter.writerows(records)