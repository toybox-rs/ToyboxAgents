#!/bin/bash 
#
#SBATCH --output=exp_StayAliveJitter_MissedBall.out
#SBATCH -e exp_StayAliveJitter_MissedBall.err
#SBATCH --time=0-11:59

source .env/bin/activate
pip install -r REQUIREMENTS.txt 1> /dev/null

if [ "$1" = "local" ]; then 
  if [ "$2" = "learn" ]; then
    training_data=`ls -d analysis/data/raw/StayAliveJitter/* | paste -s -d' '`
  fi
  python -m autoexp \
    breakout \
    --model models.breakout.target  \
    --agent StayAliveJitter \
    --seed 6232020 \
    --maxsteps 2000 \
    --window 64 \
    --outcome MissedBall \
    --counterfactual HitBall \
    --outdir exp/StayAliveJitter/MissedBall \
    --datadir $training_data \
    --constraints 'bricks\[.*?\].*' \
    1> exp_StayAliveJitter_MissedBall.out 2> exp_StayAliveJitter_MissedBall.err
elif [ "$1" = "swarm" ]; then
  echo "Executing on swarm..."
  if [ "$2" = "learn" ]; then 
    training_data=`ls -d $WORK1/ToyboxAgents/StayAliveJitter/* | paste -s -d' '`
  fi
  python -m autoexp breakout \
    --model models.breakout.target  \
    --agent StayAliveJitter \
    --outcome MissedBall \
    --counterfactual HitBall \
    --outdir $WORK1/autoexp/exp/StayAliveJitter/MissedBall \
    --seed 6232020 \
    --maxsteps 2000 \
    --window 64 \
    --datadir $training_data
fi
