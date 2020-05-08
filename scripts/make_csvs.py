#!/usr/bin/env python3
import sys, os
import argparse
import csv
import math
from tqdm import tqdm
import ujson as json
import toybox.interventions.breakout as breakout
from collections import namedtuple
from ctoybox import Toybox

def run(args):
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
        'board_alive',
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
    
        for seed in tqdm(os.listdir(args.outdir + os.sep + args.agent)):
            this_dir = args.outdir + os.sep + args.agent + os.sep + seed

            
            with open(this_dir + os.sep + args.agent + '.act', 'r') as action_file:
                actions = action_file.readlines()


            prev_state = None
            prev_t = 0
            timesteps_this_seed = []

            for f in sorted(os.listdir(this_dir)):
                if not f.endswith('json'): continue
                t = int(f[-10:-5])
                # Frames are 1-indexed.
                assert t != 0 
                assert t == prev_t + 1
                with open(this_dir + os.sep + f, 'r') as state_file:
                    state = breakout.Breakout.decode(None, json.load(state_file), breakout.Breakout)
                query.game = state
                if t == 1:
                    initial_paddle_width = state.paddle_width
                record = [args.agent, seed, t]
                
                record.append(actions[t-1].strip() if t < len(actions) -2 else None)
                
                missed_ball = len(state.balls) == 0
                # missed_ball
                record.append(missed_ball)
                    
                # Record the x and y coordinates of the ball and paddle at t and t-1
                # Store intermediate values that we use later.
                ball = state.balls[0] if not missed_ball else None
                ball_pos = ball.position if ball else None
                paddle_pos = state.paddle.position
                            
                # xpos_ball
                record.append(ball_pos.x if ball else None)
                # ypos_ball
                record.append(ball_pos.y if ball else None)
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
                
                # Had considered changing this to be the count for each column.
                # Then the tradeoff would be either 7 variables that range from 
                # 0 to 2^18-1 or 18 variables that range from 0 to 6. 
                # Solution: punt on this and just return a single number that encodes
                # the whole board.
                board_alive = 0
                nrows = query.num_rows()
                ncols = query.num_columns()
                for i in range(ncols):
                    for j, brick in enumerate(query.get_column(i)):
                        if brick.alive:
                            board_alive += 2**(i*nrows + j)
                record.append(board_alive)
                
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
                bvelocity = ball.velocity if ball else None
                speed = math.sqrt(bvelocity.x**2 + bvelocity.y**2) if bvelocity else None
                record.append(None if not speed \
                              else 'slow' if math.isclose(speed, config['ball_speed_slow'], rel_tol=0.01) \
                              else 'fast')

                # Record whether the ball is travelling downward
                # The origin is the top left, so downward movement increases the value of y
                record.append(bvelocity.y > 0 if bvelocity else None)

                # Different types of distances between balls and paddles
                record.append(abs(ball_pos.x - paddle_pos.x) if ball_pos else None)
                record.append(abs(ball_pos.y - paddle_pos.y) if ball_pos else None)
                record.append(math.sqrt((ball_pos.x - paddle_pos.x)**2 + (ball_pos.y - paddle_pos.y)**2) if ball_pos else None)
                
                # Total bricks left
                record.append(sum(int(b.alive) for b in state.bricks))
                timesteps_this_seed.append(record)
                prev_t = t
                prev_state = state

            datwriter.writerows(timesteps_this_seed)


if __name__ == '__main__':
    # I usually run this with outdir = $WORK1/ToyboxAgents/output
    parser = argparse.ArgumentParser()
    parser.add_argument('outdir')
    parser.add_argument('agent')

    args = parser.parse_args()
    run(args)
