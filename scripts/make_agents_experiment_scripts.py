#!/usr/bin/env python
"""Generates the bash scripts for running automated experimentation on scripted agents on either your local computer or swarm2."""

import argparse
import os

with open(os.sep.join(['resources', 'seeds.txt']), 'r') as f:
  default_seeds = [int(line) for line in f.readlines()]

parser = argparse.ArgumentParser()

parser.add_argument('--agents',
  required=False,
  nargs='+',
  default=['Target', 'StayAlive', 'StayAliveJitter', 'SmarterStayAlive'],
  help='Agents to generate scripts for; default is all')
parser.add_argument('--outcomes',
  required=False,
  nargs='+',
  default=['Aim left', 'Aim right', 'HitBall', 'MissedBall', 'MoveSame', 'MoveOpposite', 'MoveToward', 'MoveAway']
)
parser.add_argument('--seeds',
  nargs='+',
  default=default_seeds
)
parser.add_argument('--type',
  required=True,
  help='Must be one of: [scripted, deep]'
)
parser.add_argument('--time', default='0-11:59')
parser.add_argument('--partition', default='defq')
parser.add_argument('--model_root', default='models.breakout')
parser.add_argument('--model_path')


args = parser.parse_args()
counterfactuals = {
  'Aim left' : 'Aim right',
  'Aim right' : 'Aim left',
  'HitBall' : 'MissedBall',
  'MissedBall' : 'HitBall',
  'MoveSame' : 'MoveOpposite',
  'MoveOpposite' : 'MoveSame',
  'MoveAway' : 'MoveToward',
  'MoveToward' : 'MoveAway'
}

template_source = 'resources/{}_agents_experiment_template.sh'.format(args.type)

with open(template_source, 'r') as f:
  lines = [line for line in f.readlines() if not line.startswith('##')]
  template = ''.join(lines)
  for agent in args.agents:
    for outcome in args.outcomes:
      for seed in args.seeds:
        outcome_fmt = outcome.replace(' ', '_')
        if args.type == 'scripted':
          instance = template.format(
            agent=agent, 
            outcome_fmt=outcome_fmt,
            time=args.time,
            partition=args.partition,
            model=args.model_root + '.' + agent.lower(),
            seed=seed,
            outcome=outcome,
            counterfactual=counterfactuals[outcome],
           )
          with open(os.sep.join(['scripts', 'experiments', '_'.join(['run', agent, outcome_fmt, str(seed)]) + '.sh']), 'w') as out:
            out.write(instance)
        elif args.type == 'deep':
          for model in os.listdir(args.model_path):
            if model.endswith('model') and model.startswith('BreakoutToybox') and 'ppo2' in model:
              instance = template.format(
                  agent=agent, 
                  outcome_fmt=outcome_fmt,
                  time=args.time,
                  partition=args.partition,
                  model=args.model_root + '.' + agent.lower(),
                  seed=seed,
                  outcome=outcome,
                  counterfactual=counterfactuals[outcome],
                  model_path=args.model_path + os.sep + model
                 )
              with open(os.sep.join(['scripts', 'experiments', '_'.join(['run', agent, outcome_fmt, str(seed)]) + '.sh']), 'w') as out:
                out.write(instance)
