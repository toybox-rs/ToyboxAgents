import argparse
import os

from ctoybox import Input, Toybox
from . import learn_models


parser = argparse.ArgumentParser(description='Search for explanations')

parser.add_argument('game')
parser.add_argument('--model', 
  required=True, 
  help='The directory or module where the model information lives')
parser.add_argument('--datadir', 
  required=False,
  nargs='*',
  help='The directory/directories where we store data for training the sampler')
parser.add_argument('--agent',
  required=True,
  nargs='*',
  help='The agent class for this experiment.')
parser.add_argument('--seed', 
  default=642020,
  type=int)
parser.add_argument('--max_steps',
  default=2000,
  help='For generating on-policy states and identifying outcomes.')
parser.add_argument('--window',
  default=32,
  help='The maximum window before the outcome that we should consider for intervention.')
parser.add_argument('--outcome',
  required=True,
  nargs='+',
  help='The outcome class')

args = parser.parse_args()
start = Input()
start.button1 = True


modelmod = args.model.replace(os.sep, '.')
outcome = eval(args.outcome[0])(*args.outcome[1:])
agent = eval(args.agent[0])(Toybox(args.game, seed=args.seed), *args.agent[1:])


if args.datadir: 
  print('Learning models for {} on {}'.format(args.agent, args.game))
  # ignore the states returned
  learn_models(args.datadir, args.modelmod, args.game)

