#!/bin/bash 

source .env/bin/activate
pip install -r REQUIREMENTS.txt

if [ "$1" = "local" ]; then 
  if [ "$2" = "learn" ]; then
    training_data=`ls -d analysis/data/raw/Target/*`
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
    --datadir $training_data
    > exp_Target_MissedBall.sh
elif [ "$1" = "swarm" ]; then
  if [ "$2" = "learn" ]; then 
    training_data=`ls -d $WORK1/ToyboxAgents/Target/*`
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
    --outdir $WORK1/autoexp/exp/Target/MissedBall \
    --datadir $training_data
    > $WORK1/autoexp/exp_Target_MissedBall.txt
fi
