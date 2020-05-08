# %%
import argparse
import json
import os

from toybox.interventions.breakout import Breakout, BreakoutIntervention
from ctoybox import Toybox, Input
try:
  from agents.breakout.ppo2 import PPO2
  from agents.breakout.stayalive import StayAlive
  from agents.breakout.target import Target
except ModuleNotFoundError as e:
  if 'agents' in e.msg:
    print(e.msg)
    print('Trying running with PYTHONPATH="."')
    exit()

parser = argparse.ArgumentParser()
parser.add_argument('--train', action='store_true')
parser.add_argument('--datadir', default='analysis/data/raw/StayAlive')
parser.add_argument('--modeldir', default='breakout_models')

args = parser.parse_args()

modelmod = args.modeldir
datadir = args.datadir

os.makedirs(modelmod, exist_ok=True)

if args.train:
# load up some data and test sampling
# test for just one run
  data = []
  #datadir = './analysis/data/raw/StayAlive'
  for seed in os.listdir(datadir)[:2]:
    this_dir = datadir + os.sep + seed
    for dat in os.listdir(this_dir):
      this_file = this_dir + os.sep + dat
      if this_file.endswith('json'):
        with open(this_file, 'r') as f:
          data.append(Breakout.decode(None, json.load(f), Breakout))  

  with Toybox('breakout', withstate=data[0].encode()) as tb:
    with BreakoutIntervention(tb, modelmod=modelmod, data=data) as intervention:
      # separating this out so we can just store the models
      pass

seed=909090
random_state=None
action = Input()
action.button1 = True

with Toybox('breakout', seed=seed) as tb:
  with BreakoutIntervention(tb, modelmod=modelmod) as intervention:
    random_state = intervention.game.sample().encode()


  agent = PPO2(tb, seed, random_state)
  # tb.write_state_json(random_state)
  tb.apply_action(action)
  os.makedirs('random_start_ppo2', exist_ok=True)
  agent.play('random_start_ppo2', 1000)

  exit(0)

with Toybox('breakout', seed=seed) as tb:
  tb.write_state_json(random_state)
  tb.apply_action(action)
  agent = StayAlive(tb)
  os.makedirs('random_start_stayalive', exist_ok=True)
  agent.play('random_start_stayalive', 1000)

with Toybox('breakout', seed=seed) as tb:
  tb.write_state_json(random_state)
  tb.apply_action(action)
  agent = Target(tb)
  os.makedirs('random_start_target', exist_ok=True)
  agent.play('random_start_target', 1000)

print('to view videos, run e.g. `ffmpeg -y -i random_start_ppo2/PPO2%05d.png -framerate 24 -codec mpeg4 ppo2.mp4`')