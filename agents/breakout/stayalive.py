from . import *


class StayAlive(BreakoutAgent):
    """The simplest agent. Reacts deterministically to the x position of the ball."""

    def get_action(self):
        with breakout.BreakoutIntervention(self.toybox) as intervention:
            game = intervention.game
            ballx = game.balls[0].position.x
            paddlex = game.paddle.position.x
            if ballx < paddlex:
                input.left = True
            elif ballx > paddlex:
                input.right = True
        return input