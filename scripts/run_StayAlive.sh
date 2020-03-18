#!/bin/bash
#
#SBATCH —job-name=StayAlive_.
#SBATCH --output=logs/StayAlive_..out
#SBATCH -e logs/StayAlive_..err 
#SBATCH --nodes=1 
#SBATCH --ntasks=1 
#SBATCH --mem=2048
source .env/bin/activate
pip install -r REQUIREMENTS.txt
mkdir -p ./output/StayAlive/7595623
mkdir -p logs
echo "Running StayAlive with seed 7595623..."
python -m agents --game Breakout --output ./output/StayAlive --agentclass StayAlive --seed 7595623
