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
# * `max_steps` We want to run the agnets long enough to be reasonable certain that
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
from toybox.interventions.core import Game

from typing import *
from autoexp.outcomes import *


exp_seed  = 5202020
max_steps = 2000 # We don't want to wait forever!
window    = -32   # So we can try out the backwards search

data : Dict[Agent, Dict[Outcome, List[Game]]] = {}

# %% [markdown]
# Our next step is to instantiate the outcomes:

# %% 

missed = MissedBall()
hit = HitBall()
oppo = MoveOpposite()
away = MoveAway()
aim_right = Aim('right')
aim_left = Aim('left')

outcomes : Dict[str, Outcome] = {
    'MissedBall'  : missed,
    'HitBall'     : hit,
    'MoveOpposite': oppo,
    'MoveAway'    : away,
    'AimRight'    : aim_right,
    'AimLeft'     : aim_left
}

# %% [markdown]

# Now instantiate some agents.

# %%
from agents.breakout.target import Target
from agents.breakout.ppo2 import PPO2
from agents.breakout.stayalivejitter import StayAliveJitter
from ctoybox import Toybox, Input

# We will need to feed the agent class and arguments for initialization
# into the Experiment object later
agents = {
  'target' : {'agentclass': Target         , 'agentargs': [Toybox('breakout', seed=exp_seed)], 'agentkwargs' : {}},
  'ppo2'   : {'agentclass': PPO2           , 'agentargs': [Toybox('breakout', seed=exp_seed)], 'agentkwargs' : {}},
  'jitter' : {'agentclass': StayAliveJitter, 'agentargs': [Toybox('breakout', seed=exp_seed)], 'agentkwargs' : {}}
}

# %% [markdown]
# The next thing we need to do is learn the marginal distributions of
# the core variables. If we want conditional distributions, we will 
# need to partition the data and save multiple models. Note that 
# partitioning the data will lead to 

# %% [shell]

# mkdir models
# touch models/__init__.py

# %% 
import json
import os
from toybox.interventions import get_intervener

states : List[Game] = []
model_root = 'models.breakout'


for agent in [a['agentclass'](*a['agentargs'], **a['agentkwargs']) for a in agents.values()][:0]:
  name = agent.__class__.__name__
  with Toybox('breakout') as tb:
    root = os.path.sep.join(['analysis', 'data', 'raw', name])
    modelmod = model_root + '.' + name.lower()
    for seed in os.listdir(root):
      trial = root + os.sep + seed
      for f in os.listdir(trial):
        if f.endswith('json'):
          with open(trial + os.sep + f, 'r') as state:
            states.append(Breakout.decode(None, json.load(state), Breakout)) 
      # We are only going to learn from 1 trial, since this 
      # is a demonstration, and we don't want it to take too much time.
      # Comment out this break to use all of the data
      break
    
    intervener = get_intervener('breakout')
    with intervener(tb, modelmod=modelmod, data=states): pass # this should just make the model
  # We need to clean up for any agents that use tensorflow
  del(agent)


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

for agentname, agent in [(k, v['agentclass'](*v['agentargs'], **v['agentkwargs'])) for k, v in agents.items()]:
  data[agentname] = {}

  for oname, outcome in outcomes.items():
    print('Testing agent {} for outcome {}'.format(agent.__class__.__name__, oname))
    tb = agent.toybox

    # Reset Toybox
    tb.new_game()
    agent.reset(exp_seed)

    # Need to get the ball (i.e., start the game)
    input = Input()
    input.button1 = True
    tb.apply_action(input)  

    step = 0
    states = []

    while (not tb.game_over()) and (step < max_steps):
      if step > abs(window):
        # Test to see if we have observed the outcome yet
        action_window = agent.actions[window:]
        state_window = states[window:]
        assert len(action_window) == 32, '{} <> {} at {}'.format(len(action_window), 32, step)
        assert len(state_window)  == 32, '{} <> {} at {}'.format(len(state_window) , 32, step)
        sapairs = list(zip(state_window, action_window))
        if outcome.outcomep(sapairs):
          data[agentname][oname] = sapairs
          break

      # If we didn't break, continue as usual.
      # This more or less copies the play method of the base agent.
      action = agent.get_action()

      if action is not None:
        agent.actions.append(action_to_string(action))
        if isinstance(action, Input):
          tb.apply_action(action)
        elif type(action) == int:
          tb.apply_ale_action(action)
        else: assert False
      else: break
      
      with BreakoutIntervention(tb, modelmod='models.breakout.' + agent.__class__.__name__.lower()) as intervention:
        states.append(Breakout.decode(intervention, tb.state_to_json(), Breakout))

      step += 1

# %% [markdown]
# Instantiate an experiment for each of the outcomes we 
# want to explain.


# %%
from autoexp.driver import Experiment

exps : Dict[str, Experiment] = {}

for agentname, outcome in data.items():
  for oname, trace in outcome.items():
    if len(trace):
      print('Found positive instance of {} for {}'.format(oname, agent.__class__.__name__))
      adat = agents[agentname]
      exp = Experiment(
        game_name='breakout',
        seed=exp_seed,
        outcome_var=outcomes[oname],        
        trace=trace,
        agentclass=adat['agentclass'],
        agentargs=adat['agentargs'],
        agentkwargs=adat['agentkwargs'],
        outdir = os.sep.join(['exp', adat['agentclass'].__name__, oname])
      )
      intervened_state, intervened_outcome = exp.run()
      exps[oname] = exp

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
