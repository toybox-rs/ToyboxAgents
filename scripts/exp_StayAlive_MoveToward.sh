#!/bin/bash 
#
#SBATCH --output=exp_StayAlive_MoveToward.out
#SBATCH -e exp_StayAlive_MoveToward.err
#SBATCH --time=12:00:00

source .env/bin/activate
pip install -r REQUIREMENTS.txt 1> /dev/null

if [ "$1" = "local" ]; then 
  if [ "$2" = "learn" ]; then
    training_data=`ls -d analysis/data/raw/StayAlive/* | paste -s -d' '`
  fi
  python -m autoexp \
    breakout \
    --model models.breakout.target  \
    --agent StayAlive \
    --seed 6232020 \
    --maxsteps 2000 \
    --window 64 \
    --outcome MoveToward \
    --counterfactual MoveAway \
    --outdir exp/StayAlive/MoveToward \
    --datadir $training_data \
    --constraints 'bricks\[.*?\].*' \
    1> exp_StayAlive_MoveToward.out 2> exp_StayAlive_MoveToward.err
elif [ "$1" = "swarm" ]; then
  echo "Executing on swarm..."
  if [ "$2" = "learn" ]; then 
    training_data=`ls -d $WORK1/ToyboxAgents/StayAlive/* | paste -s -d' '`
  fi
  python -m autoexp breakout \
    --model models.breakout.target  \
    --agent StayAlive \
    --outcome MoveToward \
    --counterfactual MoveAway \
    --outdir $WORK1/autoexp/exp/StayAlive/MoveToward \
    --seed 6232020 \
    --maxsteps 2000 \
    --window 64 \
    --datadir $training_data
fi
