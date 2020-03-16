#!/usr/bin/env python3

import os 
import random
import sys

root = sys.argv[1] if len(sys.argv) > 1 else '.'

for agent in ['StayAlive', 'SmarterStayAlive', 'StayAliveJitter', 'Target']:
    # run for 30 trials each
    for _ in range(30):
        seed = random.randint(0, 1e19)

        with open('scripts/run_%s.sh' % agent, 'w') as f:
            content = """#!/bin/bash
    #
    #SBATCH —job-name={0}
    #SBATCH --output=logs/{0}_{2}.out
    #SBATCH -e logs/{0}_{2}.err 
    #SBATCH --nodes=1 
    #SBATCH --ntasks=1 
    #SBATCH --mem=2048

    source .env/bin/activate
    pip install -r REQUIREMENTS.txt
    mkdir -p {2}/output/{0}/{1}
    mkdir -p logs
    python -m agents.breakout.stayalive {2}/output/{0} {0}
    """.format(agent, seed, root)
            f.write(content)
