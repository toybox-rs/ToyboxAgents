#!/usr/bin/env python3

import os 
import random
import sys

root = sys.argv[1] if len(sys.argv) > 1 else '.'

for agent in ['StayAlive', 'SmarterStayAlive', 'StayAliveJitter', 'Target']:
    # run for 30 trials each
    for _ in range(30):
        seed = random.randint(0, 1e7)

        with open('scripts/run_%s.sh' % agent, 'w') as f:
            content = """#!/bin/bash
#
#SBATCH —job-name={0}_{2}
#SBATCH --output=logs/{0}_{2}.out
#SBATCH -e logs/{0}_{2}.err 
#SBATCH --nodes=1 
#SBATCH --ntasks=1 
#SBATCH --mem=2048
source .env/bin/activate
pip install -r REQUIREMENTS.txt
mkdir -p {2}/output/{0}/{1}
mkdir -p logs
echo "Running {0} with seed {1}..."
python -m agents --game Breakout --output {2}/output/{0} --agentclass {0} --seed {1}
""".format(agent, seed, root)
            f.write(content)
