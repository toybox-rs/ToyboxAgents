from . import *
from .stayalivejitter import StayAliveJitter
from random import random, seed, randint

import logging


class Target(StayAliveJitter):

    def __init__(self, toybox:Toybox):
        self.prev_bally = None
        self.score = 0
        super().__init__(toybox)
        seed(self.seed)

    def get_action(self):
        input = Input()
        with breakout.BreakoutIntervention(self.toybox) as intervention:
            game = intervention.game

            # We missed in the previous round; game over.
            if len(game.balls) == 0: return   

            ball = game.balls[0]
            ballx = ball.position.x
            bally = ball.position.y

            paddlex = game.paddle.position.x
            paddley = game.paddle.position.y
            paddle_width = game.paddle_width

            y_is_close = abs(bally - paddley) < 1.5 * paddle_width
            x_is_close = abs(ballx - paddlex) < 1.5 * paddle_width
            ball_down = self.prev_bally < bally if self.prev_bally else True

            if not (y_is_close and x_is_close and ball_down):
                self.prev_bally = bally
                return super().get_action(intervention=intervention)
            
            logging.info('TARGET', self._frame_counter)
            # TARGETING TIME
            # get the column with the fewest bricks greater than zero
            # if there is one brick, stop early

            # Start by shuffling the columns
            columns = [intervention.get_column(i) for i in range(intervention.num_columns())]

            # Get list of potential targets -- i.e., columns that are not yet completed.
            num_alive = [sum([int(brick.alive) for brick in this_col]) for this_col in columns]
            targets = sorted([t for t in zip(num_alive, columns) if t[0] > 0], key=lambda t: t[0])
            if game.score > self.score:
                self.score = game.score
                if logging.root.level == logging.INFO:
                    for n, c in targets:
                        print('%d bricks in column %d' % (n, c[0].col))

            # Target the column closest to completion
            target_brick = targets[0][1][0]
            colx = target_brick.position.x
            logging.info('Targeting column %d\n\tprev_ballx: %d\tballx: %d\tbally: %d\tpaddlex: %d\tcolx: %d' % (
                    target_brick.col,
                    self.prev_ballx,
                    ballx, bally,
                    paddlex,
                    colx))
            

            # Predict number of time steps until the ball crosses the x axis
            # We should be heading down from here (otherwise we would have triggered the super method)
            # We know that the ball bounces off the wall, but we are not modeling that for now.
            px_per_frame = (abs(self.prev_ballx - ballx) + abs(self.prev_bally - bally)) / 2.
            logging.info('\tPixels per frame', px_per_frame)
            steps_until_x_cross = (paddley - bally) / px_per_frame
            logging.info('\tEstimated number of steps until x crosses the axis', steps_until_x_cross)
            ball_move_right = self.prev_ballx < ballx
            projected_x_cross = ballx + (steps_until_x_cross * px_per_frame * (1 if ball_move_right else -1))
            dx = 4
            logging.info('\tProjected x cross', projected_x_cross)
            # If the ball crosses the x-axis near the target column, just try to align the paddle like normal
            if abs(colx - projected_x_cross) <= dx:
                return super().get_action(intervention=intervention)
            # The target column is to the left
            elif colx < projected_x_cross:
                if steps_until_x_cross < dx:
                    if paddlex == projected_x_cross:
                        if random() > self.jitter:
                            logging.info('Column to left; paddle at cross; Random move right')
                            input.right = True
                    # If the paddle is to the left, move to the right
                    elif paddlex < projected_x_cross:
                        logging.info('Column to left; paddle to left; Move right')
                        input.right = True
                    # Then the paddle is to the right
                    else:
                        # Make sure the paddle isn't too far to the right
                        if paddlex - (0.5 * paddle_width) > projected_x_cross:
                            logging.info('Column to left; paddle too far right; Move left')
                            input.left =  True
                        elif random() > self.jitter:
                            logging.info('Column to left; paddle to right; Random move left.')
                            input.left = True
                else: return super().get_action(intervention=intervention)
            # The target column is to the right of the projected cross
            else:
                if paddlex == projected_x_cross:
                    if random() > self.jitter:
                        logging.info('Column to right; paddle under; random move left.')
                        input.left = True
                # If the center of the paddle is to the left of the projected cross
                elif paddlex < projected_x_cross:
                    if paddlex + (0.5 * paddle_width) < projected_x_cross:
                        logging.info('Column to right; paddle too far left; move right')
                        input.right = True
                    elif random() > self.jitter:
                        logging.info('Column to right; random move right')
                        input.right = True
                # Paddle is too far to the right
                else:
                    logging.info('Column to right; Paddle too far right; move left.')
                    input.left = True


            self.prev_ballx = ballx
            self.prev_bally = bally

            return input