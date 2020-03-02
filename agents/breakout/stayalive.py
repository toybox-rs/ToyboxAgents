from agents.base import Agent
import toybox.interventions.breakout as breakout
from ctoybox import Toybox, Input
from random import random

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

        return input


class StayAliveJitter(Agent):
    """Reacts to the x position, with some random chance of not moving."""

    def __init__(self, toybox: Toybox):
        self.jitter = 0.3
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

            if ballx < paddlex and ballx < self.prev_ballx and random() > self.jitter:
                input.left = True
            elif ballx > paddlex and ballx > self.prev_ballx and random() > self.jitter:
                input.right = True
        return input


class Target(StayAliveJitter):

    def get_action(self):
        input = Input()
        input.button1 = True

        with breakout.BreakoutIntervention(self.toybox) as intervention:
            # if we haven't hit anything yet and the ball isn't close, default to StayAliveJitter
            game = intervention.game

            ball = game.balls[0]
            ballx = ball.position.x
            bally = ball.position.y

            paddlex = game.paddle.position.x
            paddley = game.paddle.position.y
            paddle_width = game.paddle_width

            is_close = abs(bally - paddley) < 0.2 * paddle_width

            if intervention.num_bricks_remaining() == intervention.num_bricks() or not is_close:
                return super().get_action()


            # TARGETING TIME
            print('TARGET TIME')
            # get the column with the fewest bricks greater than zero
            # if there is one brick, stop early
            target_col = None
            num_target_col_alive = -1

            for i in range(intervention.num_columns()):
                this_col = intervention.get_column(i)
                num_this_col_alive = len([int(brick.alive) for brick in this_col])

                # set the first column
                if target_col is None:
                    target_col = this_col
                    num_target_col_alive = len([int(brick.alive) for brick in target_col])
                # don't want the target col to be an already-formed channel
                elif num_target_col_alive == 0:
                    target_col = this_col
                    num_target_col_alive = num_this_col_alive
                # don't want to set the target column to an already-formed channel
                elif num_this_col_alive == 0:
                    continue
                elif num_this_col_alive < num_target_col_alive:
                    target_col = this_col 
                    num_target_col_alive = num_this_col_alive

                if num_target_col_alive == 1:
                    break

            colx = target_col[0].position.x

            if ballx < paddlex and colx < paddlex:
                input.left = True
            elif ballx > paddlex and colx > paddlex:
                input.right = True

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
    