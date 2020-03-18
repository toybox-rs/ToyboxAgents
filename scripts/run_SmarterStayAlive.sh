#!/bin/bash
#
#SBATCH —job-name=SmarterStayAlive_.
#SBATCH --output=logs/SmarterStayAlive_..out
#SBATCH -e logs/SmarterStayAlive_..err 
#SBATCH --nodes=1 
#SBATCH --ntasks=1 
#SBATCH --mem=2048
source .env/bin/activate
pip install -r REQUIREMENTS.txt
mkdir -p ./output/SmarterStayAlive/5085822
mkdir -p logs
echo "Running SmarterStayAlive with seed 5085822..."
python -m agents --game Breakout --output ./output/SmarterStayAlive --agentclass SmarterStayAlive --seed 5085822
