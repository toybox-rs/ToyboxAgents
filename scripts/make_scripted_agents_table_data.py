#!/usr/bin/env python

# For making report data from swarm

import os
from collections import Counter
expdir = '/mnt/nfs/work1/jensen/etosch/autoexp'

dat = {}

for f in os.listdir(expdir):
  if f.endswith('out'):
    pieces = f.split('_')
    agent = pieces[1]
    outcome = pieces[2] if len(pieces) == 4 else pieces[2] + ' ' + pieces[3]
    if agent not in dat:
      dat[agent] = {}
    if outcome not in dat[agent]:
      dat[agent][outcome] = {
        'explanations': Counter(),
      }
    dat2 = dat[agent][outcome]
    with open(expdir + '/' + f, 'r') as exp:
      for line in exp.readlines():
        if line.startswith('Original and intervened outcome differ for property'):
          explanation = line.split(' ')[-1]
          dat2['explanations'][explanation] += 1
        if line.startswith('Num interventions attempted'):
          dat2['interventions'] = line.split(' ')[-1]
        if line.startswith('Elapsed time'):
          dat2['time'] = line.split(' ')[-1]

print(dat)
