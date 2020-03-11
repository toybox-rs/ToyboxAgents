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

            if len(game.balls) == 0:
                # We missed in the previous round; game over.
                return   
            ball = game.balls[0]
            ballx = ball.position.x
            bally = ball.position.y

            paddlex = game.paddle.position.x
            paddley = game.paddle.position.y
            paddle_width = game.paddle_width

            #dx = paddle_width // 4

            y_is_close = abs(bally - paddley) < 1.5 * paddle_width
            x_is_close = abs(ballx - paddlex) < 1.5 * paddle_width

            # If the ball isn't close, don't do anything
            if not (x_is_close or y_is_close): 
                self.prev_ballx = ballx
                self.prev_bally = bally
                return input

            if intervention.num_bricks_remaining() == intervention.num_bricks():
                # if we haven't hit anything yet and the ball isn't close, default to StayAliveJitter
                return super().get_action(intervention=intervention)


            # TARGETING TIME
            # get the column with the fewest bricks greater than zero
            # if there is one brick, stop early

            # Start by shuffling the columns
            columns = [intervention.get_column(i) for i in range(intervention.num_columns())]
            shuffle(columns)
            num_alive = [len([int(brick.alive) for brick in this_col]) for this_col in columns]
            # Get list of potential targets -- i.e., columns that are not yet completed.
            targets = sorted([t for t in zip(num_alive, columns) if t[0] > 0], key=lambda t: t[0])
            # Target the column closest to completion
            colx = targets[0][1][0].position.x

            print(self.frame_counter)
            if ballx < paddlex:
                if ballx < self.prev_ballx:
                    if self.prev_ballx < colx:
                        print('A')
                        input.right = True
                    else:
                        print('B')
                        input.left = True
                else: 
                    print('C')
                    input.left = True
            else: 
                if ballx > self.prev_ballx:
                    print('D')
                    input.right = True
                else:
                    if self.prev_ballx < colx:
                        print('E')
                        input.left = True
                    else:
                        print('F')
                        input.right = True

            self.prev_ballx = ballx
            self.prev_bally = bally

            return input


if __name__ == '__main__':
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='Run an agent on a Toybox game.')
    parser.add_argument('output', help='The directory in which to save output (frames and json)')
    parser.add_argument('agentclass', help='The name of the Agent class')
    parser.add_argument('--maxsteps', default=1e7, help='The maximum number of steps to run.')

    args = parser.parse_args()

    with Toybox('breakout') as tb:
        agent = eval(args.agentclass)(tb)
        # Need to get the ball
        input = Input()
        input.button1 = True
        agent.toybox.apply_action(input)
        # Now play the game
        agent.play(args.output, args.maxsteps)
    