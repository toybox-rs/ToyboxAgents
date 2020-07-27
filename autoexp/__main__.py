"""Entry point for running a single agent explanation search.

For information, use with argument --help.
"""
import argparse
import importlib
import os
import sys

from timeit import default_timer as timer
from typing import Optional, List, Tuple, Set


from ctoybox import Input, Toybox
from toybox.interventions import Game


import autoexp.outcomes as outcomes
import agents
import autoexp

from autoexp import learn_models, load_states, find_outcome_window
from autoexp.driver import Experiment
from autoexp.vars.composite import Composite

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
  nargs='+',
  help='The agent class for this experiment.')
parser.add_argument('--seed', 
  default=6232020,
  type=int)
parser.add_argument('--maxsteps',
  default=2000,
  type=int,
  help='For generating on-policy states and identifying outcomes.')
parser.add_argument('--window',
  default=64,
  type=int,
  help='The maximum window before the outcome that we should consider for intervention.')
parser.add_argument('--outcome',
  required=True,
  nargs='+',
  help='The outcome class.')
parser.add_argument('--counterfactual',
  required=True,
  nargs='+',
  help='The counterfactual class.')
parser.add_argument('--outcome_dir',
  required=False,
  type=str,
  help='The directory that contains the state json sequence for explaining an outcome')
parser.add_argument('--vars', 
  required=False,
  nargs='+',
  default=set(),
  help='The composite attributes to include in experiments.')
parser.add_argument('--constraints',
  required=False,
  default=set(),
  nargs='+',
  help='The constraints we want to apply to the atomic attributes.')
parser.add_argument('--record_json',
  default=False,
  action='store_true',
  help='Flag that, when used, records the state json for every experiment.')
parser.add_argument('--outdir',
  required=True,
  help='Where to store the logged experiment data.')
parser.add_argument('--learnvarsonly', 
  action='store_true',
  help='Only learn empirical probability distributions for the composite variables.'
  )

args = parser.parse_args()

modelmod = args.model.replace(os.sep, '.')

importlib.import_module('autoexp.outcomes.' + args.game)
outcome = eval('outcomes.' + args.game + '.' + args.outcome[0])(*args.outcome[1:])
counterfactual = eval('outcomes.' + args.game + '.' + args.counterfactual[0])(*args.counterfactual[1:])

agent_mod = '.'.join(['agents', args.game, args.agent[0].lower()])
importlib.import_module(agent_mod)
tb = Toybox(args.game, seed=args.seed)
arglist = []
kwargs = {}
for term in args.agent[1:]:
  if '=' in term:
    k, v = term.split('=')
    kwargs[k] = v
  else:
    arglist.append(term)
agent = eval(agent_mod + '.' + args.agent[0])(tb, *arglist, seed=args.seed, **kwargs)

composite_vars : Set[Composite] = set()
if args.vars:
  importlib.import_module('.vars.composite.' + args.game, package='autoexp')
  composite_vars = set([eval('autoexp.vars.composite.' + args.game + '.' + v)(args.model) for v in args.vars])

if args.datadir: 
  print('Learning models for {} on {} from {}'.format(str(agent), args.game, args.datadir))
  training_states = []
  for d in args.datadir:
    print('Loading states from', d)
    training_states.extend(load_states(d, args.game))
  if not args.learnvarsonly:
    print('Learning marginals for atomic attributes.')
    learn_models(training_states, args.model, args.game)
  for var in composite_vars:
    print('Learning marginal for', str(var))
    var.make_models(args.model, training_states)

trace: Optional[List[Tuple[Game, str]]] = None

if args.outcome_dir:
  # load up the outcome data 
  print('Loading {} trace for {} from {}'.format(outcome.__name__, agent.__name__, args.outcome_dir))
  trace = load_states(args.outcome_dir, args.game)
else:
  # search for the outcome under normal gameplay

  # new_game is now being called in the agent.reset method
  # tb = agent.toybox
  # tb.new_game() 
  agent.reset(args.seed)
  
  found_o, found_c = False, False
  
  agent.play(maxsteps=args.window, write_json_to_file=args.record_json, save_states=True) #, path='ppo2_stuff')
  
  step = len(agent.states)

  while True:
    action_window = agent.actions[-1 * args.window:]
    state_window  = agent.states[-1 * args.window:]
    states        = list(zip(state_window, action_window))

    try:
      outcome_sapairs        = find_outcome_window(outcome,        states, args.window)
      counterfactual_sapairs = find_outcome_window(counterfactual, states, args.window)
    except outcomes.OutcomeException as e:
      print(e, file=sys.stderr)
      print('\tPredicate applied over time steps [{}, {}]'.format(len(agent.states) - args.window - 1, len(agent.states) - 1), file=sys.stderr)
      outcome_sapairs, counterfactual_sapairs = [], []
            
    
    if outcome_sapairs and not found_o: 
      print('Found outcome {} for {} during window [{}, {}]!'.format(
          outcome.__class__.__name__, 
          agent.__class__.__name__, 
          max(step - args.window, 0), 
          step))
      # Want to make sure we don't pick an outcome too early in the game.
      if len(outcome_sapairs) >= 2 * outcome.minwindow:
        Toybox(args.game, withstate=outcome_sapairs[0][0].encode()).save_frame_image('outcome_{}_{}_begin.png'.format(str(outcome), str(agent)))
        Toybox(args.game, withstate=outcome_sapairs[-1][0].encode()).save_frame_image('outcome_{}_{}_end.png'.format(str(outcome), str(agent)))
        found_o = True
        trace = outcome_sapairs
        if found_c: break

    if counterfactual_sapairs and not found_c: 
      print('Found counterfactual {} for {} during window [{}, {}]!'.format(
          counterfactual.__class__.__name__, 
          agent.__class__.__name__, 
          max(step - args.window, 0), 
          step))
      Toybox(args.game, withstate=counterfactual_sapairs[0][0].encode()).save_frame_image('counterfactual_{}_{}_begin.png'.format(str(counterfactual), str(agent)))
      Toybox(args.game, withstate=counterfactual_sapairs[-1][0].encode()).save_frame_image('counterfactual_{}_{}_end.png'.format(str(counterfactual), str(agent)))
      found_c = True
      if found_o: break

    if agent.stopping_condition(args.maxsteps): break
    # advance by one step until we find the outcome and counterfactual
    agent.step('/dev/null', False, True)
    #agent.step('ppo2_stuff', True, True)
    step += agent.action_repeat

  if not found_o: 
    print('Ran {} for {} steps; did not find outcome {}'.format(str(agent), step, str(outcome)))
    exit(0)
  if not found_c:
    print('Ran {} for {} steps; did not find counterfactual {}'.format(str(agent), step, str(counterfactual)))
    exit(0)

# Now run the experiment
agent.reset(seed=args.seed)

exp = Experiment(
  game_name=args.game,
  seed=args.seed,
  modelmod=args.model,
  outcome_var=outcome,
  counterfactual=counterfactual,
  atomic_constraints=set(args.constraints),
  composite_vars=composite_vars,
  trace=trace,
  agent=agent, 
  outdir=args.outdir,
  discretization_cutoff=3
)
num_mut_pts = len(exp.mutation_points)
start = timer()
intervened_state, intervened_outcome = exp.run()
end = timer()
print('Num mutation points: {}'.format(num_mut_pts))
print('Num interventions attempted: {}'.format(sum(len(items) for items in exp.interventions.values())))
print('Elapsed time: {}'.format(end - start))
