from . import *
from random import random, seed


class MoveOnlyFalling(BreakoutAgent):
    """
    Try to stay alive when the (1st) ball is moving downward.

    Potential Failure: when the ball bounces in an acute angle, the agent needs to move while the ball is moving upwards
    """

    def __init__(*args, **kwargs):
        super().__init__(*args, **kwargs)
        seed(self.seed)
        self.ball_moving_down = None
        self.ball_prevY = None

    def get_action(self):
        input = Input()
        input.button1 = True  # push a button so it starts

        with breakout.BreakoutIntervention(self.toybox) as intervention:
            game = intervention.game
            bally = game.balls[0].position.y

            if self.ball_prevY is not None:
                self.ball_moving_down = (bally > self.ball_prevY)
            self.ball_prevY = bally

            if self.ball_moving_down:
                # stay alive when the ball is moving down
                ballx = game.balls[0].position.x
                paddlex = game.paddle.position.x
                if ballx < paddlex:
                    input.left = True
                elif ballx > paddlex:
                    input.right = True

        return input