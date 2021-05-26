#!/usr/bin/env python3

import os 
import random
import sys
import subprocess
import zipfile
import argparse
import time, datetime

parser = argparse.ArgumentParser()
#parser.add_help('A utility for generating sample data for an agent')
parser.add_argument('--root', help='You probably want your work1 location on swarm and \'.\' on your local machine.')
parser.add_argument('--email', help='The email to send notifications to', default=None)
parser.add_argument('--agent', help='The agent you want to sample from')
parser.add_argument('--nepisodes', help='The number of episodes to generate', default=30, type=int)
parser.add_argument('--pngs', help='Record the frames as pngs', default=False)
args = parser.parse_args()
root = args.root

#agents =  ['StayAlive', 'SmarterStayAlive', 'StayAliveJitter', 'Target']
agents = [args.agent]
timestamp = datetime.datetime.now()
time_str = timestamp.strftime('%y%m%d_%H%M')
script_path = 'scripts{0}slurm{0}{1}{0}'.format(os.sep, time_str)

if not os.path.exists(script_path):
    os.makedirs(script_path)

if not os.path.exists('logs'):
    os.makedirs('logs')

seeds = []

for agent in agents:
    # create empty tar file that we will add to in a distributed fashion
    tarfile = root + os.sep + agent + '.zip'
    # print("Creating empty tar: %s" % tarfile)
    # subprocess.run(['tar', '-cf', tarfile, '-T', '/dev/null'])
    print('Creating or overwriting empty zip file: %s' % tarfile)
    with zipfile.ZipFile(tarfile, 'w') as f: pass
    # run for 30 trials each
    for _ in range(args.nepisodes):
        seed = random.randint(0, 1e7)
        seeds.append(seed)
        rmpngs = 'rm {1}{0}{2}{0}{3}{0}{4}{0}*.png'.foramt(os.sep, args.root, agent, seed) if not args.pngs else ""
        cmdfile = '{0}run_{1}_{2}.sh'.format(script_path, agent, seed)

        with open(cmdfile, 'w') as f:
            content = """#!/bin/bash
#
#SBATCH -o logs/{0}_{1}.out
#SBATCH -e logs/{0}_{1}.err 
#SBATCH --nodes=1 
#SBATCH --ntasks=1 
#SBATCH --mem=2048
#SBATCH --time=0-01:00:00
#SBATCH --mail-type=NONE
#SBATCH --mail-user={4}
source .env/bin/activate
pip install -r REQUIREMENTS.txt
mkdir -p {2}/{0}/{1}
# We may be -re-running this script; if so, delete old data
rm {2}/{0}/{1}/*
python -m agents --game Breakout --output {2}/{0} --agentclass {0} --seed {1}
zip {3} {2}/{0}/*
{5}
""".format(agent, seed, root, tarfile, args.email, rmpngs)
            f.write(content)

        try:
            subprocess.run(['sbatch', cmdfile])
        except:
            subprocess.call(['chmod', '+x', cmdfile])
            subprocess.run(cmdfile)
        time.sleep(2)
        
with open(script_path + os.sep + 'seeds.txt', 'w') as f:
    for seed in seeds:
        f.write(str(seed) + '\n')
