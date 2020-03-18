from . import *

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
