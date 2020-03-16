#!/usr/bin/env python3

import os 
import random

for agent in ['StayAlive', 'SmarterStayAlive', 'StayAliveJitter', 'Target']:
    # run for 30 trials each
    for _ in range(30):
        seed = random.randint(0, 1e19)

        with open('scripts/run_%s.sh' % agent, 'w') as f:
            content = """#!/bin/bash
    #SBATCH —job-name={0}
    #SBATCH --output={0}.out
    #SBATCH -e {0}.err 
    #SBATCH --nodes=1 
    #SBATCH --ntasks=1 
    #SBATCH --mem=2048

    source .env/bin/activate
    pip install -r REQUIREMENTS.txt
    mkdir -p output/{0}/{1}
    python -m agents.breakout.stayalive output/{0} {0}
    """.format(agent, seed)
            f.write(content)
