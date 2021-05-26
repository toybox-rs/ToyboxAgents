# !/usr/bin/env python3
# farms out deleting pngs on slurm
import os
import argparse
import subprocess

parser = argparse.ArgumentParser()
#parser.add_help('A utility for generating sample data for an agent')
parser.add_argument('--root', help='You probably want your work1 location on swarm and \'.\' on your local machine.')
parser.add_argument('--agent', help='The agent you want to sample from')
args = parser.parse_args()

datadir = '{1}{0}{2}{0}'.format(os.sep, args.root, args.agent)
for seed in os.listdir(datadir):
    subprocess.run(["sbatch", "--wrap=\"rm {}{}{}*.png\"".format(datadir, seed, os.sep)])
