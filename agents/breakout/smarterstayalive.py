from . import *
import random

class SmarterStayAlive(BreakoutAgent):
    """Still simple, but should toggle less -- reacts to the horizontal direction of the ball. Moves randomly when the paddle is aligned under a tunnel."""

    def __init__(self, *args, **kwargs):
        self.prev_ballx = None
        self.jitter = 0.5
        super().__init__(*args, **kwargs)

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
            else:
                columns = [intervention.get_column(i) for i in range(intervention.num_columns())]
                for column in columns:
                    if intervention.is_channel(column):
                        coli = column[0].col 
                        colx = column[0].position.x
                        size = column[0].size
                        # not sure which of these is used for height and which is used for width
                        width = size.x if size.x > size.y else size.y
                        # If it's the far left column, we need to send the ball to the right
                        if coli == 0:
                            input.left = True; break
                        # If it's the far right column, we need to send the ball to the left
                        if coli == len(columns) - 1:
                            input.right = True; break
                        if paddlex > (colx - (width / 2)) and paddlex < (colx + (width / 2)):
                            if random.random() < 0.6:
                                input.left = True
                            elif random.random() < 0.9:
                                input.left = False
                            break


            self.prev_ballx = ballx

        return input
