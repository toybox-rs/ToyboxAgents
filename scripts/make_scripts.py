#!/usr/bin/env python3

import os 
import random
import sys
import subprocess
import zipfile

root = sys.argv[1] if len(sys.argv) > 1 else '.'
agents =  ['StayAlive', 'SmarterStayAlive', 'StayAliveJitter', 'Target']
agents = agents[:-1]

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
#SBATCH --output=logs/{0}_{2}.out
#SBATCH -e logs/{0}_{2}.err 
#SBATCH --nodes=1 
#SBATCH --ntasks=1 
#SBATCH --mem=2048
source .env/bin/activate
pip install -r REQUIREMENTS.txt
mkdir -p {2}/output/{0}/{1}
# We may be -re-running this script; if so, delete old data
rm {2}/output/{0}/{1}/*
mkdir -p logs
python -m agents --game Breakout --output {2}/output/{0} --agentclass {0} --seed {1}
zip --ur --file={3} {2}/output/{0}/{1}/*
""".format(agent, seed, root, tarfile)
            f.write(content)

        subprocess.run(['sbatch', cmdfile])
