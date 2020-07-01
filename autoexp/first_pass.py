#%% [markdown]

# This tutorial covers the basic pipeline of how to use the `autoexp` tool. 
# We assume you have already recorded data from agent runs. 
#
# The first run of this tutorial will need to build samplers for the data. 
# Depending on how much data you have, this can take some time. I (Emma)
# recommend setting aside about an hour to run the basic version of this 
# tutorial. If you'd like to play around with using more data or agents, 
# recommend setting aside an afternoon.

# # Preliminaries
# Before we can run any experiments, we need to 
# (task 2) select an outcome we want to explain (task 1) from a 
# particular trace of a particular agent playing Breakout, and (task 3) learn a
# model for sampling the core features of the game state. 
#
#
# `autoexp/outcomes.py` contains several outcomes for Breakout. 
# We are going to start by looking at three agents whose behavior 
# want to explain: Target, PPO2, and StayAliveJitter. 
#
#
# In an ideal world, we would watch an agent play, hit pause, and then 
# ask the agent to explain a particular behavior. This process might include 
# collecting sequences of game state and labels for the behavior. We would
# then train a classifier to identify the behavior over a sliding window.
# Such a classifier is similar to what has been proposed for SC2, for task
# identification. 
#
# In the meantime, we will use hand-crafted functions to identify when 
# an agent engages in a particular behavior and will verify that behavior
# by observing videos. The intent here is to ensure that all positive 
# instances of the outcome variable are correct, and to tolerate missing
# instances. Thus, the outcome-detecting funcations can be used for training
# with observational data, since the number of negative instances will
# dwarf any missing positive instances. The greater challenge will be
# identifying sufficient positive instances to adequately train the model.
# We recommend collecting more data, using the methods described elsewhere
# in this repository. 
# 
# For now we will proceed with a smaller set of training data than would
# be ideal.
# 
# Operationally, this amounts to selecting a subset of the trace of 
# particular run (with a _known seed_) that ends with a positive instance
# of the outcome variable. Let's generate this data by actually running
# the agents.
# 
# We start by setting some global variables we are going to use throughout
# this tutorial: 
# 
# * `exp_seed` We have the ability to control randomness, so we should. We set the
#    seed for any component that allows us to do so. This is an arbitrary number. 
#    I picked the date for when I started writing this tutorial in its current form.
# * `max_steps` We want to run the agents long enough to be reasonable certain that
#    we will detect the outcome. However, we do not want to run them for too long.
# * `window` This is the window of context before the outcome. Some outcomes are 
#    computed over a fixed window of time (e.g., we only need the last two states
#    to detect whether the agent has missed the ball.) Other outcomes 
#    will effectively have an upper bound on the window (e.g., the HitBall outcome
#    only allows the ball to be hit once in the window). 
# * `data` This variable will hold the window of states that lead up to an outcome,
#    for each agent. 

# %%
from agents.base import Agent, action_to_string
from ctoybox import Input
from toybox.interventions.core import Game

from typing import *
from autoexp.outcomes.breakout import *


exp_seed  = 5202020
max_steps = 2000 # We don't want to wait forever!
window    = 64  # So we can try out the backwards search

data : Dict[str, Dict[str, List[Game]]] = {}

# %% [markdown]
# Our next step is to instantiate the outcomes:

# %% 

missed = MissedBall()
hit = HitBall()
oppo = MoveOpposite()
move_same = MoveSame()
away = MoveAway()
toward = MoveToward()
aim_right = Aim('right')
aim_left = Aim('left')

outcomes : Dict[str, Outcome] = {
    # 'MissedBall'  : (missed, hit),
    'HitBall'     : (hit, missed),
    # 'MoveOpposite': (oppo, move_same),
    # 'MoveAway'    : (away, toward),
    # 'AimRight'    : (aim_right, aim_left),
    # 'AimLeft'     : (aim_left, aim_right)
}

# %% [markdown]

# Now instantiate some agents.

# %%
from agents.breakout.target import Target
from agents.breakout.ppo2 import PPO2
from agents.breakout.stayalivejitter import StayAliveJitter
from agents.breakout.stayalive import StayAlive
from ctoybox import Toybox

# We will need to feed the agent class and arguments for initialization
# into the Experiment object later
agents = [
  Target(Toybox('breakout', seed=exp_seed)),
  PPO2(Toybox('breakout', seed=exp_seed)),
  # StayAlive(Toybox('breakout', seed=exp_seed)),
  # StayAliveJitter(Toybox('breakout', seed=exp_seed))
]

# %% [markdown]
# The next thing we need to do is learn the marginal distributions of
# the core variables. If we want conditional distributions, we will 
# need to partition the data and save multiple models.

# %% [shell]

# mkdir models
# touch models/__init__.py

# %% [markdown]
# Now we have a destintion directory for the models. 
# 

# %% 
import json
import os
from toybox.interventions import get_intervener
from toybox.interventions.breakout import BreakoutIntervention

states : List[Game] = []
model_root = 'models.breakout'


# for agent in agents[:0]:
#   name = agent.__class__.__name__
#   with Toybox('breakout') as tb:
#     root = os.path.sep.join(['analysis', 'data', 'raw', name])
#     print('Loading data from', root)
#     modelmod = model_root + '.' + name.lower()
#     print('Creating module', modelmod)
#     for seed in sorted(os.listdir(root)):
#       if seed.startswith('.'): continue
#       trial = root + os.sep + seed
#       for f in sorted(os.listdir(trial))[:500]:
#         if f.endswith('json'):
#           with open(trial + os.sep + f, 'r') as state:
#             state = Breakout.decode(BreakoutIntervention(tb), json.load(state), Breakout)
#             states.append(state) 
#       # We are only going to learn from 1 trial, since this 
#       # is a demonstration, and we don't want it to take too much time.
#       # Comment out this break to use all of the data
#       break

    
#     intervener = get_intervener('breakout')
#     with intervener(tb, modelmod=modelmod, data=states): pass
#   # We need to clean up for any agents that use tensorflow
#   del(agent)


# %% [markdown]
# Some of the agents log additional information (e.g., the Target agent logs the values 
# of its internal variables it uses to make decisions). Let's turn those off.

# %%
# We don't want too much output from the agents, 
# so set the logging level very high.
import logging
logging.basicConfig(level=logging.CRITICAL)

# %% [markdown]
# 
# Now we can generate data for each agent and outcome.

# %% 

from toybox.interventions.breakout import BreakoutIntervention
from utils import find_outcome_window

for agentname, agent in [(a.__class__.__name__, a) for a in agents]:
  data[agentname] = {}

  for oname, (outcome, counterfactual) in outcomes.items():
    print('Testing agent {} for outcome {}'.format(agentname, oname))
    tb = agent.toybox

    # Reset Toybox
    tb.new_game()
    agent.reset(exp_seed)

    found_o = False
    found_c = False

    # first play the agent for the requisite number of steps
    agent.play(maxsteps=window, write_json_to_file=False, save_states=True)
    step = len(agent.states)
    print(agent.__class__.__name__, agent.action_repeat, step)

    while (not tb.game_over()) and (step < max_steps) and (not agent.done if hasattr(agent, 'done') else True):
      # Test to see if we have observed the outcome yet
      get_data = lambda o: find_outcome_window(outcome, list(zip(agent.states, agent.actions)), window)
      outcome_sapairs = get_data(outcome)
      counterfactual_sapairs = get_data(counterfactual)

      if outcome_sapairs and not found_o:
        data[agentname][oname] = outcome_sapairs
        print('Found outcome {} for {} during window [{}, {}]!'.format(oname, agentname, max(step - window, 0), step))
        found_o = True
        if found_c: break

      if counterfactual_sapairs and not found_c:
        print('Found counterfactual {} for {} during window [{}, {}]!'.format(counterfactual.__class__.__name__, agentname, max(step - window, 0), step))
        found_c = True
        if found_o: break

      # If we didn't break, take one step
      # This more or less copies the play method of the base agent
      # reproduced here to bring the agent up to speed.
      agent.step('/dev/null', False, True)
      step += agent.action_repeat
    if not found_o: 
      print('Ran {} for {} steps; did not find outcome {}'.format(agent.__class__.__name__, step, oname))
    if not found_c:
      data[agentname][oname] = []
      print('Ran {} for {} steps; did not find counterfactual {}'.format(agent.__class__.__name__, step, str(counterfactual)))

# %% [markdown]
# Instantiate an experiment for each of the outcomes we 
# want to explain.


# %%
from autoexp.driver import Experiment
from autoexp.vars.derived.breakout import XDistanceBallPaddle

exps : Dict[str, Experiment] = {}

for agent in agents:
  agentname = agent.__class__.__name__
  outcome = data[agentname]
  agent.reset(seed=exp_seed)
  for oname, trace in outcome.items():
    modelmod = 'models.breakout.' + agentname.lower()
    sample_data_dir = os.path.sep.join(['analysis', 'data', 'raw', agentname])
    with Toybox('breakout', withstate=trace[0][0].encode()) as tb:
      tb.save_frame_image('begin_{}_{}.png'.format(oname, agent.__class__.__name__))
    with Toybox('breakout', withstate=trace[-1][0].encode()) as tb:
      tb.save_frame_image('end_{}_{}.png'.format(oname, agent.__class__.__name__))
    if len(trace):
      exp = Experiment(
        game_name='breakout',
        seed=exp_seed,
        modelmod=modelmod,
        outcome_var=outcomes[oname][0],        
        counterfactual=outcomes[oname][1],
        core_constraints={
          # r'bricks\[\d+?\]\.size\..*', 
          # r'bricks\[\d+?\]\.position\..*',
          # r'bricks\[\d+?\]\.color\..*',
          # r'bricks\[\d+?\]\.[(col)|(row)|(points)|(depth)]',
          r'bricks.*',
          r'.*\.y$'
        },
        derived_vars={
          XDistanceBallPaddle(modelmod)
        },
        sample_data_dir=sample_data_dir,
        trace=trace,
        agent=agent,
        outdir = os.sep.join(['exp', agentname, oname])
      )
      intervened_state, intervened_outcome = exp.run()
      print(intervened_state, intervened_outcome)
      exps[oname] = exp
    else: 
      print('\nNo instances of {} found'.format(oname))


# %% [shell]



# %%


# # How to handle context
# The examples in this tutorial all assume the set of context variables is empty.
# Core variable values are sampled from the marginal empirical probability 
# distribution of the available trace (i.e, conditioned on the agent's policy).
# If we wanted to constrain the states used for the empirical probability
# distribution, we would filter the states by defining variables similar to the 
# outcome variables, and applying them across the sliding window.

# # Including derived features.
# This pipeline only illustrates intervention for core features. Derived features
# would be added iteratively by the user. Since the definition of derived features
# necessarily depends on core features, we would remove the core features from
# the set of variables to be manipulated upon the addition of dependent derived 
# features. 
#
# 1. Add the ability to monitor whether there is heterogeneity in the effect  



# %%
