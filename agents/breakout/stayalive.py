from agents.base import Agent
import toybox.interventions.breakout as breakout
from ctoybox import Toybox, Input
from random import random
from numpy.random import shuffle

class StayAlive(Agent):
    """The simplest agent. Reacts deterministically to the x position of the ball."""

    def get_action(self):
        input = Input()
        # Always need to get a new ball, if we've missed
        input.button1 = True
        with breakout.BreakoutIntervention(self.toybox) as intervention:
            game = intervention.game
            ballx = game.balls[0].position.x
            paddlex = game.paddle.position.x
            if ballx < paddlex:
                input.left = True
            elif ballx > paddlex:
                input.right = True
        return input


class SmarterStayAlive(Agent):
    """Still simple, but should toggle less -- reacts to the horizontal direction of the ball."""

    def __init__(self, toybox: Toybox):
        self.prev_ballx = None
        super().__init__(toybox)

    def get_action(self):
        input = Input()
        input.button1 = True

        with breakout.BreakoutIntervention(self.toybox) as intervention:
            game = intervention.game
            ballx = game.balls[0].position.x
            paddlex = game.paddle.position.x

            if self.prev_ballx is None:
                self.prev_ballx = ballx
                        
            if ballx < paddlex and ballx < self.prev_ballx:
                input.left = True
            elif ballx > paddlex and ballx > self.prev_ballx:
                input.right = True

            self.prev_ballx = ballx

        return input


class StayAliveJitter(Agent):
    """Reacts to the x position, with some random chance of not moving."""

    def __init__(self, toybox: Toybox):
        self.jitter = 0.3
        self.prev_ballx = None
        super().__init__(toybox)

    def get_action(self, intervention=None):
        input = Input()
        input.button1 = True

        with (intervention or breakout.BreakoutIntervention(self.toybox)) as intervention:
            game = intervention.game
            ballx = game.balls[0].position.x
            paddlex = game.paddle.position.x


            if self.prev_ballx is None:
                self.prev_ballx = ballx

            if ballx < paddlex and ballx < self.prev_ballx and random() > self.jitter:
                input.left = True
            elif ballx > paddlex and ballx > self.prev_ballx and random() > self.jitter:
                input.right = True

            self.prev_ballx = ballx
            
        return input


class Target(StayAliveJitter):

    def __init__(self, toybox:Toybox):
        self.prev_bally = None
        super().__init__(toybox)

    def get_action(self):
        input = Input()
        input.button1 = True

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

            y_is_close = abs(bally - paddley) < paddle_width
            x_is_close = abs(ballx - paddlex) < paddle_width
            ball_down = self.prev_bally < bally if self.prev_bally else True

            if not (y_is_close and x_is_close and ball_down):
                return super().get_action(intervention=intervention)

            print('TARGET', self.frame_counter)
            # TARGETING TIME
            # get the column with the fewest bricks greater than zero
            # if there is one brick, stop early

            # Start by shuffling the columns
            columns = [intervention.get_column(i) for i in range(intervention.num_columns())]
            shuffle(columns)

            # Get list of potential targets -- i.e., columns that are not yet completed.
            num_alive = [len([int(brick.alive) for brick in this_col]) for this_col in columns]
            targets = sorted([t for t in zip(num_alive, columns) if t[0] > 0], key=lambda t: t[0])

            # Target the column closest to completion
            colx = targets[0][1][0].position.x

            # Predict number of time steps until the ball crosses the x axis
            # We should be heading down from here (otherwise we would have triggered the super method)
            # We know that the ball bounces off the wall, but we are not modeling that for now.
            px_per_frame = abs(self.prev_ballx - ballx)
            steps_until_x_cross = bally // px_per_frame
            ball_move_right = self.prev_ballx < ballx
            projected_x_cross = ballx + (steps_until_x_cross * px_per_frame * (-1 if ball_move_right else 1))
            dx = 3
            # If the ball crosses the x-axis near the target column, just try to align the paddle like normal
            if abs(colx - projected_x_cross) <= dx:
                return super().get_action(intervention=intervention)
            # The target column is to the left
            elif colx < projected_x_cross:
                if steps_until_x_cross < dx:
                    if paddlex == projected_x_cross:
                        if random() > self.jitter:
                            input.right = True
                    # If the paddle is to the left, move to the right
                    elif paddlex < projected_x_cross:
                        input.right = True
                    # Then the paddle is to the right
                    else:
                        # Make sure the paddle isn't too far to the right
                        if paddlex - (0.5 * paddle_width) > projected_x_cross:
                            input.left =  True
                        elif random() > self.jitter:
                            input.left = True
            # The target column is to the right of the projected cross
            else:
                if paddlex == projected_x_cross:
                    if random() > self.jitter:
                        input.left = True
                # If the center of the paddle is to the left of the projected cross
                elif paddlex < projected_x_cross:
                    if paddlex + (0.5 * paddle_width) < projected_x_cross:
                        input.right = True
                    elif random() > self.jitter:
                        input.right = True
                # Paddle is too far to the right
                else:
                    input.left = True


            self.prev_ballx = ballx
            self.prev_bally = bally

            return input


if __name__ == '__main__':
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='Run an agent on a Toybox game.')
    parser.add_argument('output', help='The directory in which to save output (frames and json)')
    parser.add_argument('agentclass', help='The name of the Agent class')
    parser.add_argument('--maxsteps', default=1e7, type=int, help='The maximum number of steps to run.')

    args = parser.parse_args()

    with Toybox('breakout') as tb:
        agent = eval(args.agentclass)(tb)
        # Need to get the ball
        input = Input()
        input.button1 = True
        agent.toybox.apply_action(input)
        # Now play the game
        agent.play(args.output, args.maxsteps)