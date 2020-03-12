#!/bin/bash
#SBATCH —job-name=StayAlive
#SBATCH --output=StayAlive.out
#SBATCH -e StayAlive.err 
#SBATCH --nodes=1 
#SBATCH --ntasks=1 
#SBATCH --mem=2048

source .env/bin/activate
pip install -r REQUIREMENTS.txt
echo "StayAlive"
python -m agents.breakout.stayalive output/StayAlive StayAlive
