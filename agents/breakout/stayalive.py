from . import *


class StayAlive(BreakoutAgent):
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