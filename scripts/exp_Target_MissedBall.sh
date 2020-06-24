#!/bin/bash 
#
#SBATCH --output=exp_Target_MissedBall.out
#SBATCH -e exp_Target_MissedBall.err

source .env/bin/activate
pip install -r REQUIREMENTS.txt 1> /dev/null

if [ "$1" = "local" ]; then 
  if [ "$2" = "learn" ]; then
    training_data=`ls -d analysis/data/raw/Target/* | paste -s -d' '`
  fi
  python -m autoexp \
    breakout \
    --model models.breakout.target  \
    --agent Target \
    --seed 6232020 \
    --maxsteps 2000 \
    --window 64 \
    --outcome MissedBall \
    --counterfactual HitBall \
    --outdir exp/Target/MissedBall \
    --datadir $training_data \
    1> exp_Target_MissedBall.out 2> exp_Target_MissedBall.err
elif [ "$1" = "swarm" ]; then
  echo "Executing on swarm..."
  if [ "$2" = "learn" ]; then 
    training_data=`ls -d $WORK1/ToyboxAgents/Target/* | paste -s -d' '`
  fi
  python -m autoexp breakout \
    --model models.breakout.target  \
    --agent Target \
    --outcome MissedBall \
    --counterfactual HitBall \
    --outdir $WORK1/autoexp/exp/Target/MissedBall \
    --seed 6232020 \
    --maxsteps 2000 \
    --window 64 \
    --datadir $training_data
fi
