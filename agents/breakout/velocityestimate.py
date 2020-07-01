from . import *
from random import random, seed


class VelocityEstimate(BreakoutAgent):
    """
    The paddle does not use the position of the ball to compute the move but estimates where to move based on the
    its velocity. Once paddle computes where to go, it commits to it. While the paddle starts moving,
    it does not estimate the ball's trajectory.
    Once the paddle arrives the estimated location, it waits there or re-compute where to go when the ball bounces
    the wall on either side

    Possible failure:
    the agent assumes that the velocity does not change, but it does once it reaches the orange layer
    """

    def __init__(self,  *args, **kwargs):
        self.prev_bally = None
        self.score = 0
        super().__init__( *args, **kwargs)
        seed(self.seed)
        self.ball_prevY = None
        self.ball_prevX = None
        self.ball_moving_down = None
        self.target_x = None
        self.ball_velocity_x = None

        self.ball_velocity = None  # this is an ERROR (but intentional)! you need to re-compute the velocity of the ball.
        self.paddle_width = None # this is an ERROR (but intentional)! you need to re-compute the width of the paddle.

    def compute_target(self):
        pass

    def get_action(self):
        with breakout.BreakoutIntervention(self.toybox) as intervention:
            game = intervention.game

            ball_y = game.balls[0].position.y # current Y position of the ball
            ball_x = game.balls[0].position.x # current X position of the ball
            if self.paddle_width is None:
                self.paddle_width = game.paddle_width  # the width of the paddle

            game_width = intervention.num_columns() * game.bricks[0].size.x

            # you can intervene the thickness of the walls and this agent will fail
            # but this type of intervention is not in the graph product of states
            X_min = int(self.paddle_width) # the leftmost game frame
            X_max = X_min + game_width # the rightmost game frame

            paddlex = game.paddle.position.x  # get current paddle x position
            paddley = game.paddle.position.y  # get current paddle y position

            if self.ball_prevY is not None:
                self.ball_moving_down = (ball_y > self.ball_prevY) # True is the ball is moving down

            # this agent fails since it assumes the velocity of the ball in Y is constant
            if self.ball_velocity is None and self.ball_prevY is not None:
                self.ball_velocity = ball_y - self.ball_prevY

            if self.ball_prevX is not None:
                self.ball_velocity_x = ball_x - self.ball_prevX

            self.ball_prevY = ball_y
            self.ball_prevX = ball_x

            if self.ball_velocity is not None:
                if self.target_x is None:
                    frames = abs(ball_y - paddley) / self.ball_velocity
                    target_x = int(self.ball_velocity_x * frames + ball_x)
                    self.target_x = max(X_min, min(X_max, target_x))
                else:
                    # there is target and it is not close (input can only control the paddle by +/- 4)
                    if abs(self.target_x - paddlex) > 4:
                        # the paddle is not at the target
                        if self.target_x > paddlex:
                            input.right = True
                        else:
                            input.left = True
                    # compute new target if ball is moving down AND the ball is close to the wall
                    # this needs to be implemented smarter.
                    # right now it allows re-compute as long as you arrive the target.
                    # but the paddle moves much faster than the ball
                    elif self.ball_moving_down:
                        frames = abs(ball_y - paddley) / self.ball_velocity
                        target_x = int(self.ball_velocity_x * frames + ball_x)
                        self.target_x = max(X_min, min(X_max, target_x))
        # print(self.target_x, paddlex, self.ball_moving_down)
        return input