from random import random, seed, randint
from ctoybox import Input
from . import BreakoutAgent
from toybox.interventions.breakout import BreakoutIntervention


class StayAliveJitter(BreakoutAgent):
    """Reacts to the x position, with some random chance of not moving."""

    def __init__(self, *args, **kwargs):
        self.jitter = 0.3
        self.prev_ballx = None
        super().__init__(*args, **kwargs)
        seed(self.seed)

    def get_action(self, intervention=None):
        input = Input()
        with (intervention or breakout.BreakoutIntervention(self.toybox)) as intervention:
            game = intervention.game
            if len(game.balls) == 0: return input
            ballx = game.balls[0].position.x
            paddlex = game.paddle.position.x


            if self.prev_ballx is None:
                self.prev_ballx = ballx

            if ballx < paddlex and ballx < self.prev_ballx and random() > self.jitter:
                input.left = True
            elif ballx > paddlex and ballx > self.prev_ballx and random() > self.jitter:
                input.right = True
            elif random() < self.jitter:
                if random() < 0.5:
                    input.left = True
                else:
                    input.right = True

            self.prev_ballx = ballx
            
        return input
