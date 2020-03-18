#!/bin/bash
#
#SBATCH —job-name=StayAliveJitter_.
#SBATCH --output=logs/StayAliveJitter_..out
#SBATCH -e logs/StayAliveJitter_..err 
#SBATCH --nodes=1 
#SBATCH --ntasks=1 
#SBATCH --mem=2048
source .env/bin/activate
pip install -r REQUIREMENTS.txt
mkdir -p ./output/StayAliveJitter/656625
mkdir -p logs
echo "Running StayAliveJitter with seed 656625..."
python -m agents --game Breakout --output ./output/StayAliveJitter --agentclass StayAliveJitter --seed 656625
