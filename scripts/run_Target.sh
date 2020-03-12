#!/bin/bash
#SBATCH —job-name=Target
#SBATCH --output=Target.out
#SBATCH -e Target.err 
#SBATCH --nodes=1 
#SBATCH --ntasks=1 
#SBATCH --mem=2048

source .env/bin/activate
pip install -r REQUIREMENTS.txt
python -m agents.breakout.stayalive output/Target Target
