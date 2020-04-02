#!/usr/bin/env python3

import os 
import random
import sys
import subprocess
import zipfile
import argparse
import time

parser = argparse.ArgumentParser()
parser.add_argument('root', help='You probably want your work1 location on swarm and \'.\' on your local machine.')
args = parser.parse_args()
root = args.root

agents =  ['StayAlive', 'SmarterStayAlive', 'StayAliveJitter', 'Target']

for agent in agents:
    # create empty tar file that we will add to in a distributed fashion
    tarfile = root + os.sep + agent + '.zip'
    # print("Creating empty tar: %s" % tarfile)
    # subprocess.run(['tar', '-cf', tarfile, '-T', '/dev/null'])
    print('Creating empty zip file: %s' % tarfile)
    with zipfile.ZipFile(tarfile, 'w') as f:
        pass
    # run for 30 trials each
    for _ in range(30):
        seed = random.randint(0, 1e7)
        cmdfile = 'scripts/run_%s_%d.sh' % (agent, seed)

        with open(cmdfile, 'w') as f:
            content = """#!/bin/bash
#
#SBATCH —job-name={0}_{1}
#SBATCH --output=logs/{0}_{1}.out
#SBATCH -e logs/{0}_{1}.err 
#SBATCH --nodes=1 
#SBATCH --ntasks=1 
#SBATCH --mem=2048
#SBATCH --time=04:00
source .env/bin/activate
pip install -r REQUIREMENTS.txt
mkdir -p {2}/{0}/{1}
# We may be -re-running this script; if so, delete old data
rm {2}/{0}/{1}/*
mkdir -p logs
python -m agents --game Breakout --output {2}/{0} --agentclass {0} --seed {1}
zip -ur --file={3} {2}/{0}/*
""".format(agent, seed, root, tarfile)
            f.write(content)

        subprocess.run(['sbatch', cmdfile])
        time.sleep(2)
