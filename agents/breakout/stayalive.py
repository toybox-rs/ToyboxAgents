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

    def get_action(self):
        input = Input()
        input.button1 = True

        with breakout.BreakoutIntervention(self.toybox) as intervention:
            game = intervention.game

            ball = game.balls[0]
            ballx = ball.position.x
            bally = ball.position.y

            paddlex = game.paddle.position.x
            paddley = game.paddle.position.y
            paddle_width = game.paddle_width

            dx = paddle_width // 4

            y_is_close = abs(bally - paddley) < paddle_width
            x_is_close = abs(ballx - paddlex) < paddle_width

            # If the ball isn't close, don't do anything
            if not (x_is_close or y_is_close): return input

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
            colx = targets[0].position.x

            if ballx < paddlex:
                if colx < paddlex:
                    input.left = True
                else: 
                    input.right = True
            elif ballx > paddlex: 
                if colx > paddlex:
                    input.right = True
                else:
                    input.left = True

            return input


if __name__ == '__main__':
    import sys
    framedir = sys.argv[1]
    agentclass = sys.argv[2]
    with Toybox('breakout') as tb:
        agent = eval(agentclass)(tb)
        # Need to get the ball
        input = Input()
        input.button1 = True
        agent.toybox.apply_action(input)
        # Now play the game
        agent.play(framedir, maxsteps=500)
    