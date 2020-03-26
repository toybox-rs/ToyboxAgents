#!/usr/bin/env python3

import os 
import random
import sys
import subprocess

root = sys.argv[1] if len(sys.argv) > 1 else '.'

for agent in ['StayAlive', 'SmarterStayAlive', 'StayAliveJitter', 'Target']:
    # create empty tar file that we will add to in a distributed fashion
    tarfile = root + os.sep + agent + '.tar'
    echo "Creating empty tar: %s" % tarfile
    subprocess.run(['tar', '-cf', tarfile, '-T', '/dev/null'])
    # run for 30 trials each
    for _ in range(30):
        seed = random.randint(0, 1e7)

        with open('scripts/run_%s_%d.sh' % (agent, seed), 'w') as f:
            content = """#!/bin/bash
#
#SBATCH —job-name=ToyboxAgents_{0}_{1}
#SBATCH --output=logs/{0}_{2}.out
#SBATCH -e logs/{0}_{2}.err 
#SBATCH --nodes=1 
#SBATCH --ntasks=1 
#SBATCH --mem=2048
source .env/bin/activate
pip install -r REQUIREMENTS.txt
mkdir -p {2}/output/{0}/{1}
# We may be -re-running this script; if so, delete old data
rm {2}/output/{1}/{1}/*
mkdir -p logs
python -m agents --game Breakout --output {2}/output/{0} --agentclass {0} --seed {1}
tar --append --file={3} {2}/output/{0}/*
""".format(agent, seed, root, tarfile)
            f.write(content)
