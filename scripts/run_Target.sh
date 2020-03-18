#!/bin/bash
#
#SBATCH —job-name=Target_.
#SBATCH --output=logs/Target_..out
#SBATCH -e logs/Target_..err 
#SBATCH --nodes=1 
#SBATCH --ntasks=1 
#SBATCH --mem=2048
source .env/bin/activate
pip install -r REQUIREMENTS.txt
mkdir -p ./output/Target/4557141
mkdir -p logs
echo "Running Target with seed 4557141..."
python -m agents --game Breakout --output ./output/Target --agentclass Target --seed 4557141
