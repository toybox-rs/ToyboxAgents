import argparse
import sys, os, importlib

from ctoybox import Toybox, Input
from random import random, seed, randint

import agents
import toybox
#from agents import breakout

parser = argparse.ArgumentParser(description='Run an agent on a Toybox game.')
parser.add_argument('--output', help='The directory in which to save output (frames and json)')
parser.add_argument('--agentclass', help='The name of the Agent class')
parser.add_argument('--game', help='The name of the game. Must Be CamelCase.')
parser.add_argument('--maxsteps', default=1e7, type=int, help='The maximum number of steps to run.')
#parser.add_argument('--trials', default=30, type=int, help='The number of games this agent should play (with one life)')
parser.add_argument('--seed', default=0, type=int)
args = parser.parse_args()

game_lower = args.game.lower()

with Toybox(game_lower) as tb:
    importlib.import_module('agents.' + game_lower + '.' + args.agentclass.lower())
    importlib.import_module('toybox.interventions.' + game_lower)

    # First reset the random seed
    if args.seed:
        tb.set_seed(args.seed)
        tb.new_game()

    # Run with only one life
    intervention_str = 'toybox.interventions.{0}.{1}Intervention'.format(
        game_lower,
        args.game
    )
    with eval(intervention_str)(tb) as intervention:
        intervention.game.lives = 1    

    path = args.output + os.sep + str(args.seed)

    # Need to get the ball (i.e., start the game)
    input = Input()
    input.button1 = True
    tb.apply_action(input)  


    agent_str = 'agents.' + game_lower + '.' + args.agentclass.lower() + '.' + args.agentclass
    agent = eval(agent_str)(tb)
    agent.play(path, args.maxsteps)