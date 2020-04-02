#!/usr/bin/env python3
#
#SBATCH job-name=Target
#SBATCH --mem=2048
#SBATCH --time=04:00
source .env/bin/activate
rm $WORK1/ToyboxAgents/Target.csv
python ./scripts/make_csvs.py $WORK1/ToyboxAgents Target
chmod +x $WORK1/ToyboxAgents/Target.csv
