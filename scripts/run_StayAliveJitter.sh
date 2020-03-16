#!/bin/bash
#SBATCH —job-name=StayAliveJitter
#SBATCH --output=StayAliveJitter.out
#SBATCH -e StayAliveJitter.err 
#SBATCH --nodes=1 
#SBATCH --ntasks=1 
#SBATCH --mem=2048

source .env/bin/activate
pip install -r REQUIREMENTS.txt
echo "StayAliveJitter"
python -m agents.breakout.stayalive output/StayAliveJitter StayAliveJitter
