# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %% [markdown]
# # Getting Started
# 
# Following the instructions for generating agent data (either [locally](https://github.com/KDL-umass/ToyboxAgents/wiki/Generate-Agent-Data-Locally) or [on a cluster](https://github.com/KDL-umass/ToyboxAgents/wiki/Generate-Agent-Data-on-a-Cluster-Using-Slurm)), you will end up with a directory of saved game states that looks something like this:
# 
# ```
# {output}
# - {AgentClass1}
#   - {seed1}
#     - {AgentClass100001.json}
#     - {AgentClass100001.png}
#     - {AgentClass100002.json}
#     - {AgentClass100002.png}
#     - ...
#   - {seed2}
#     - {AgentClass100001.json}
#     - {AgentClass100001.png}
#     - {AgentClass100002.json}
#     - {AgentClass100002.png}
#     - ...
#   - ...
# - {AgentClass2}
# - ...
# ```
# 
# `output` here refers to the directory provided as the argument to the code that produced the data (run `pythom -m agents --help` in the root directory )
# 
# # Load some data
# The first thing we'd like to do is load in some data. Assuming a gzipped archive called `agents.tar.gz`, we can load the relevant data using the `load_data` function from the local `utils` module:

# %%
from utils import load_data

agent1 = load_data('data/agent1.tgz', load_state=True)
# Warning: loading all four agents takes time! 
# agent2 = load_data('data/agent2.tgz', 'breakout' load_state=True) 
# agent3 = load_data('data/agent3.tgz', 'breakout' load_state=True) 
# agent4 = load_data('data/agent4.tgz', 'breakout' load_state=True) 

# %% [markdown]
# You only need to load the data up once. Cells in notebooks are stateful and they can be run out of order (although in this tutorial, we have written it to be run in order). For interactive data analysis, we'd like to only load the data into memory once. 
# 
# If you'd like to make videos for debugging, you will also need to load in the images and can run the following code; note that you can do this in one pass by additionally supplying the `load_images` argument in the code in the previous cell. 
# 
# This code will create videos for each trial of each agent. Videos are saved in the format `<agentclass>_<seed>.mp4`. You may find these videos helpful for debugging.

# %%
from utils import make_videos
agent1_videos = load_data('data/agent1.tgz', load_images=True)
make_videos(agent1_videos['images'])
del agent1_videos

# %% [markdown]
# 
# 
# # Defining an outcome variable
# 
# Although Breakout appears to be a simple game, there are actually quite a few outcomes variables we could define. For example, an obvious or rudimentary one that would be suitable for an explanation system might be, "Why did you miss the ball?" In our framing of explanation, this query would be converted to: "What would need to have been different for the agent to hit the ball?" Of course, the agent would actually need to have missed the ball at some point for this to be meaningful. 
# 
# A low-level query that ought to be valid for all well-performing agents might be "Why didn't you take action _a_ at time _t_?", since at some point, every agent needs to move. 
# 
# A third possible query might be, "Why didn't you target column _i_ of the board?" 
# 
# ## Why didn't you take action _a_ at time _t_?
# 
# This is the easiest counterfactual query to define. `load_data` returns a dictionary that may contain keys `images`, `states`, and `actions`. The values in these dictionaries are themselves dictionaries, where their keys are the random seeds and the values are the timestamped actions, images, or states. The time-stamped content is not guaranteed to be sorted, so we will need to handle that.

# %%
# First choose the seed; states are organized by the agent's name. 
# agent1 is the `Target` agent.
from typing import List, Tuple
seed = list(agent1['states']['Target'].keys())[0]
states = agent1['states']['Target'][seed]
actions : List[Tuple[str, str]] = agent1['actions']['Target'][seed]

# The state list is a list of tuples. The first first entry in the tuple is 
# the filename, which contains the left-padded frame number.
# The first entry in the action tuple is a left-padded string denoting the 
# frame number that the action is responding to.
states.sort(key=lambda t: t[0])
actions.sort(key=lambda t: t[0])


# %%
# Now get the agent and the action at time step 100.
# Note: Frames are 1-indexed.
state = states[99]
action = actions[99]

# Make sure they match
assert action[0] in state[0]

# Now we have our first outcome:
outcome1 = action[1]

# %% [markdown]
# If we wanted to run experiments for this particular scenario, we'd load up the prior state
# (i.e., `state[1]`), mutate it, load it into the Toybox engine, and then observe the outcome.

# ## Why did you miss the ball?
# Each trial ends either when the agent times out, or misses the ball. Therefore, 
# this query will only be valid on a per-trial basis, so we just need to check what's going
# on in the final state. We can do this easily in python by loading up Toybox state as 
# Python, using the interventions API:

# %%
import toybox.interventions.breakout as breakout

# Grab the last state in the list:
last_state = states[-1]

# But these are tuples, so let's redefine it to be the actual state json:
last_state = last_state[1]

# Now let's load up the object
last_state = breakout.Breakout.decode(None, last_state, breakout.Breakout)

# Now we can see what's defined on this object:
vars(last_state)

# %%
# It turns out that, as soon as the agent misses the ball, it's removed from the state
# information. Given the way we've set up data collection, this means that we can just 
# check whether there are zero current balls:
missed = len(last_state.balls) == 0

# We might want to double check this, though, so let's ensure that in the previous frame,
# the ball's y position is *greater than* the paddle's y position (coordinates are 
# relative to the top left corner of the frame)
penultimate_state = breakout.Breakout.decode(None, states[-2][1], breakout.Breakout)
ball = penultimate_state.balls[0]
paddle = penultimate_state.paddle

# Now we want to see if the ball's y-position is lower than the paddle's y-position:
assert ball.position.y > paddle.position.y
outcome2 = missed


# %% [markdown]
# One of the challenges with this particular outcome is that it is not clear what the window
# of relevant action is. When using experiments to evaluate the counterfactual for the
# purposes of explanation, we have limited ourselves to the window of one time-step. 
# This actually limits the relevant queries for amongst eligible trials where the agents
# missed the ball -- it will only produce an satisfactory explanation if e.g. it did not move,
# or moved in the wrong direction at time t-1. If, instead, the agent was very far away 
# from the ball, no action it could have taken at t-1 would have changed the outcome. 

# ## Why didn't you target column _i_?
# _This example includes a lengthy discussion of the challenges of more complex outcomes. 
# The primary audience for this section is CRA, but would be useful for anyone looking to 
# define more sophisticated outcome variables_.
#
# This query is similar to the previous one, but substantially harder, since there are
# several possible interpretations of it. The first challenge we face is that even the 
# act of measuring the outcome itself is temporally extended, describing a complex 
# behavior. Suppose we had perfect mathematical model of the bounce mechanics in Breakout. 
# Then, given that the ball is traveling downward at time $t$, we could compute where the agent would 
# need to align the paddle in order to hit the first alive brick in the target column.
# The agent would need to move the paddle to this location before the ball crosses the
# x-axis. 
#
# Let the time at which the ball crosses the x-axis be $t'$. Let the current paddle location be 
# $p_t$.
# Assume that there is only one paddle position position at $t'$ that will allow the ball to 
# hit the targeted column, (i.e., only one $p_{t'}$).
# Then if $t' - t < |p_t - p_{t'}|$, it is impossible for the agent to move the paddle to the 
# correct location in time. Since we want $t' - t \geq |p_t -p_{t'}|$, let's choose to measure
# from time $t$ such that that $t \leq t' - |p_t - p_{t'}|$.
#
# First consider the case where $t = t' - |p_t - p_{t'}|$. Let $M$ denote a 
# function that models the bounce mechanics of the environment from time $t$ onward
# (this means that $M$ is conditioned on the state of the game at $t$ and is not defined for 
# inputs that are less than $t$). 
# $M$ outputs the location of the ball at any time $t_i$, and can be used in conjunction
# with the paddle location to compute the appropriate action that moves the paddle toward
# $p_{t'}$: 
# $$ a_{t_i} = \begin{cases}\text{left}, & M(t_i) - p_{t_i} < 0\\\text{right}, & M(t_i) - p_{t_i} > 0\\\text{noop}, &\text{o/w}\end{cases}$$
# This action is optimal at time $t_i$: because we have chosen the smallest $t$ the will allow
# us to hit the ball at the correct paddle location, if we do not take action $a_{t_i}$,
# the ball will not hit any bricks in the column.
#
# We happen to know that $a_{t_i}$ will be the same for the entire period $[t, t']$ 
# (i.e., $\forall t_i\in [t, t'], t_j \in [t, t'], a_{t_i} = a_{t_j}$) because we have 
# specifically chosen $t$ so that there will not be enough time for the agent to move past $t$.
# Therefore, we can just call this single optimal action $a^*$.
#
# Now we can define our outcome variable over the window $[t, t']$. If $a_{t_i}$ is the action the 
# agent actually took for at time $t_i$ some trial, then we are interested in the case where 
# $\exists t_i\in [t, t'], a_{t_i} \not=a^*$, i.e., when the agent chose an action that would cause it 
# to no longer be targeting the column of interest. 
#
# This definition of how to measure whether an agent is "targeting" the ball 
# at a column is incredibly rigid: It has no allowance for any error on the part of the agent. 
# There may be some source of random error in the flow of information from the environment, through the 
# agent's action selection procedure, through the implementation of that action. This errant behavior may 
# disappear upon re-running the agent, or it may only manifest for _this_ particular column or state 
# configuration.  Furhtermore, this definition cannot capture when the agent has learned a model that 
# differs from the true bounce mechanics.
# While we can say with certainty that the agent has not learned $M$, we cannot say that it has not learned
# how to target a column more generally. 
#
# Our definition brings up another problem with this particular outcome: it might be reasonable to believe
# that a human desiring an explanation
# would only ask this counterfactual in cases where they believe the agent has actually learned to target
# the ball. For example, if the human observer sees an agent that is struggling to hit the ball in the
# first place, they might not find a query about targeting a column useful. See the two agents 
# below (you may need to re-execute the code below for the video to display properly).

# %% [HTML]
# <video width="45%" controls>
#   <source src="videos/Target.mp4" type="video/mp4" />
#   <source src="https://raw.githubusercontent.com/KDL-umass/ToyboxAgents/master/analysis/videos/StayAliveJitter.mp4" type="video/mp4" />
# </video>
# <video width="45%" controls>
#   <source src="videos/StayAliveJitter.mp4" type="video/mp4" />
# </video>

# %% [markdown]
# This question of whether "targeting" is an appropriate outcome relates to our intuition that 
# when agents exhibit complex behavior, it is because there is an internal representation or decision 
# that has a mapping to the externally observed behavior, and that 
# that decision procedure can be accurately measured using our
# externally-defined function. We might feel comfortable saying that the agent on the left
# exhibits targeting behavior, but the minor adjustments the agent makes as the ball approaches 
# the paddle would likely make our earlier definition of the behavior insufficient. In fact, 
# because this agent is scripted, we know that it contains some internal estimation of where
# the ball will land. The agent "believes" that it is targeting a specific column. This data
# latent, although it could be recovered via log files. 
#
# We happen to know that the agent on the right does not use any variables that are not 
# available in the recorded state data. We can inspect the code to see that it does not 
# engage in any "targeting," but a human observer might say that it is "targeting" the left-most
# column. Furthermore, it is possible to write an agent that uses similar planning to the agent 
# in the video on the right, but "gets stuck" when targeting the columns on either end of the 
# playing area.
#
# One possible solution to this problem is to include some tolerance in our definition of what 
# it means to be "targeting" a column. A more relaxed version of the definition of this outcome
# would not only address the aforementioned issues with what we mean by "targeting," but it would
# address the fact that:
# 
# * Our assumption that there is exactly one $p_{t'}$ (i.e., x-position of the paddle when the 
# ball crosses the x-axis) may not be true.
# * In practice, selecting $t$ to be exactly equal to $t' - |p_t - p_{t'}|$ may be prohibitively
# expensive, because finding the exact value of $t$ may be expensive.
# 
#
# One way to add some slack is to discretize the paddle. We happen to know that the default
# configuration of the paddle contains five discrete segments. However, if we did not know this,
# we could guess from observing agent behavior that there are at least three segments -- a 
# middle, left, and right. Let $b_{t_i}$ be the ball position at time $t_i$. Paddle 
# x-position (i.e., $p_{t_i}$) is the center of the paddle, so we could easily 
# define a approximation where if $|p_{t_i} - b_{t_i}| < c$, then we are in the middle
# of the paddle, and the sign of the difference determines left and right. 
#
# Note that through this solution, we have side-stepped the temporal natural of this outcome
# by re-defining it using an approximation that can be measured at a single point in time. 
# This single point in time still needs to be calculated back from the inciting event (i.e., 
# hitting a brick in column $j$, rather than column $i$). Our re-framing transforms this query
# into something more like "Why did you miss the ball?" However, rather than reasoning about 
# a _sequence_ of actions, we are now reasoning about a single action. Future work would
# situate our framing in terms of literature on tasks, options, etc. 
#
# We defer computing examples of aiming behavior, since they will either be labor-intensive or
# compute-intensive: without prior knowledge of meaningful queries, we would need to identify
# every relevant time point for this query, and then compute every relevant $(i, j)$ pair.
#
# # Generating CSVs for inference
# We now show how we generate data for a single agent. This is the first pass approach; we 
# will discuss more efficient ways to do this in other tutorials. The purpose of this 
# demonstration is to establish the workflow from raw data, which is important during the 
# exploratory phase.

# %%
# Grab the config; we will need information in here.
from ctoybox import Toybox
from collections import namedtuple
import numpy as np
import math

# Grab the first 10, some middle 10, and the last 10 as an example
bstates = [breakout.Breakout.decode(None, s[1], breakout.Breakout) for s in states[:10] + states[200:210] + states[-10:]]

# We are going to want to use some helper functions from the interventions API.
# To avoid cleaning up TB and having too many indentations, let's provide a dummy TB instance.
query = breakout.BreakoutIntervention(namedtuple('tb', 'game_name')('breakout'), 'breakout')
bactions = [a for (_, a) in actions]

# The agents used the default settings, so we can just grab it from a fresh instance. 
with Toybox('breakout') as tb:
    config = tb.config_to_json()
    query.config = config 

# %%
import csv

initial_paddle_width = None
prev_state = None

with open('dat.csv', 'w') as f:

    datawriter = csv.writer(f, delimiter=',')
    # Write the header
    datawriter.writerow([
        'agent_name', 
        'seed', 
        't', 
        'action', 
        'missed_ball', 
        'xpos_ball', 
        'ypos_ball', 
        'xpos_ball_prev',
        'ypos_ball_prev',
        'xpos_pad',
        'ypos_pad',
        'xpos_pad_prev',
        'ypos_pad_prev',
        'indicators',
        'is_far_left',
        'is_far_right',
        'score',
        'pad_width',
        'ball_speed',
        'ball_down',
        'xdist_ball_pad',
        'ydist_ball_pad',
        'l2_ball_pad',
        'num_bricks_left'])

    timestamps = list(range(10)) + list(range(200, 210)) + list(range(len(states)-10, len(states)))
    for t, state in zip(timestamps, bstates):
        query.game = state
        if t == 0:
            initial_paddle_width = state.paddle_width
        record = ['agent1', seed, t]

        # Record the action at time t
        # action
        action = bactions[t].decode('utf-8').strip() if t < len(actions) - 1 else None
        record.append('noop' if action == 'button1' else action)

        # Record whether the agent missed the ball
        missed_ball = len(state.balls) == 0
        # missed_ball
        record.append(missed_ball)
        
        # Record the x and y coordinates of the ball and paddle at t and t-1
        # Store intermediate values that we use later.
        ball = state.balls[0] if not missed_ball else None
        ball_pos = ball.position if ball else None
        paddle_pos = state.paddle.position

        # xpos_ball
        record.append(ball_pos.x if not missed_ball else None)
        # ypos_ball
        record.append(ball_pos.y if not missed_ball else None)
        # xpos_ball_prev
        record.append(prev_state.balls[0].position.x if prev_state else None)
        # ypos_ball_prev
        record.append(prev_state.balls[0].position.y if prev_state else None)
        # xpos_pad
        record.append(paddle_pos.x)
        # ypos_pad
        record.append(paddle_pos.y)
        # xpos_pad_prev
        record.append(prev_state.paddle.position.x if prev_state else None)
        # ypos_pad_prev
        record.append(prev_state.paddle.position.y if prev_state else None)

        # The binary representation of this number indicates whether the 
        # column at the ith bit is a channel
        indicators = [query.get_column(i) for i in range(query.num_columns())]
        # indicators
        record.append(sum(2**i for i, v in enumerate(indicators) if v))

        # Record whether the paddle is on the far left or far right of the screen
        leftmost_brick = query.get_column(0)[0]
        rightmost_brick = query.get_column(query.num_columns() - 1)[0]
        
        record.append(paddle_pos.x <= (leftmost_brick.position.x - (leftmost_brick.size.x * 0.5)))
        record.append(paddle_pos.x >= (rightmost_brick.position.x + (rightmost_brick.size.x * 0.5)))

        # Record the score
        record.append(state.score)

        # Paddle width can be two sizes
        record.append('big' if state.paddle_width == initial_paddle_width else 'small')

        # Ball speed can have one of two values
        bvelocity = state.balls[0].velocity if ball else None
        speed = math.sqrt(bvelocity.x**2 + bvelocity.y**2) if bvelocity else None
        record.append(None if not speed \
            else 'slow' if math.isclose(speed, config['ball_speed_slow'], rel_tol=0.01) \
            else 'fast')

        # Record whether the ball is travelling downward
        # The origin is the top left, so downward movement increases the value of y
        record.append(None if missed_ball else state.balls[0].velocity.y > 0)

        # Different types of distances between balls and paddles
        record.append(abs(ball_pos.x - paddle_pos.x) if ball_pos else None)
        record.append(abs(ball_pos.y - paddle_pos.y) if ball_pos else None)
        record.append(math.sqrt((ball_pos.x - paddle_pos.x)**2 + (ball_pos.y - paddle_pos.y)**2) if ball_pos else None)

        # Total bricks left
        record.append(sum(int(b.alive) for b in state.bricks))

        # Write the row and set the prev_state to be the current state
        datawriter.writerow(record)
        prev_state = state

# %% 
import pandas as pd
pd.read_csv('dat.csv')

# %%
