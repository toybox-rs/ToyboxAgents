#!/usr/bin/env python

# For making report data from swarm

import os
from collections import Counter
from tabulate import tabulate
expdir = '/mnt/nfs/work1/jensen/etosch/autoexp'

dat = {}

for f in os.listdir(expdir):
  if f.endswith('out'):
    pieces = f.split('_')
    agent = pieces[1]
    outcome = pieces[2] if len(pieces) == 4 else pieces[2] + ' ' + pieces[3]
    seed = pieces[-1].split('.')[0]
    if agent not in dat:
      dat[agent] = {}
    if outcome not in dat[agent]:
      dat[agent][outcome] = {}
    with open(expdir + '/' + f, 'r') as exp:
      explanation = ''
      num_interventions = 0
      time = 0
      for line in exp.readlines():
        if line.startswith('Original and intervened outcome differ for property'):
          explanation = line.split(' ')[-1]
        if line.startswith('Num interventions attempted'):
          num_interventions = line.split(' ')[-1]
        if line.startswith('Elapsed time'):
          time = line.split(' ')[-1]
      dat[agent][outcome][seed] = (explanation, num_interventions, time)

for agent, stuff in dat.items():
  print('-----------------------------------------------------------------------------------------------------------------')
  for outcome, stuff2 in stuff.items():
    for seed, (explanation, num_interventions, time) in stuff2.items():
      print('Agent {} tested {} interventions over {}m for outcome {} and found {} changed the outcome for seed {}'.format(
        agent, 
        int(num_interventions), 
        float(time) / 60, 
        outcome,
        explanation.strip() or 'nothing',
        seed))
