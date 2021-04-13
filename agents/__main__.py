import argparse
import sys, os, importlib

from ctoybox import Toybox, Input
from random import random, seed, randint

import agents
import toybox
#from agents import breakout

parser = argparse.ArgumentParser(description='Run an agent on a Toybox game.')
parser.add_argument('--output',     default='.',                               help='The directory in which to save output (frames and json)')
parser.add_argument('--agentclass',                             required=True, help='The name of the Agent class')
parser.add_argument('--game',                                   required=True, help='The name of the game.')
parser.add_argument('--maxsteps',   default=1e7,      type=int,                help='The maximum number of steps to run.')
parser.add_argument('--seed',                         type=int)
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
    intervener = toybox.interventions.get_intervener(game_lower)
    with intervener(tb) as intervention:
        intervention.game.lives = 0    

    path = args.output + (os.sep + str(args.seed) if args.seed else '')

    if game_lower == 'breakout':
        # Need to get the ball (i.e., start the game)
        input = Input()
        input.button1 = True
        tb.apply_action(input)


    agent_str = 'agents.' + game_lower + '.' + args.agentclass.lower() + '.' + args.agentclass
    agent = eval(agent_str)(tb)

    if args.seed:
        agent.reset_seed(args.seed)

    agent.play(path, args.maxsteps)