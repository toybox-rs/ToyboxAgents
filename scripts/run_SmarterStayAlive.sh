#!/bin/bash
#SBATCH —job-name=SmarterStayAlive
#SBATCH --output=SmarterStayAlive.out
#SBATCH -e SmarterStayAlive.err 
#SBATCH --nodes=1 
#SBATCH --ntasks=1 
#SBATCH --mem=2048

source .env/bin/activate
pip install -r REQUIREMENTS.txt
echo "SmarterStayAlive"
python -m agents.breakout.stayalive output/SmarterStayAlive SmarterStayAlive
