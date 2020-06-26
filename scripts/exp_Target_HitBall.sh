#!/bin/bash 
#
#SBATCH --output=exp_Target_HitBall.out
#SBATCH -e exp_Target_HitBall.err

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
    --outcome HitBall \
    --counterfactual MissedBall \
    --outdir exp/Target/HitBall \
    --datadir $training_data \
    --constraints 'bricks\[.*?\].*' \
    1> exp_Target_HitBall.out 2> exp_Target_HitBall.err
elif [ "$1" = "swarm" ]; then
  echo "Executing on swarm..."
  if [ "$2" = "learn" ]; then 
    training_data=`ls -d $WORK1/ToyboxAgents/Target/* | paste -s -d' '`
  fi
  python -m autoexp breakout \
    --model models.breakout.target  \
    --agent Target \
    --outcome HitBall \
    --counterfactual MissedBall \
    --outdir $WORK1/autoexp/exp/Target/HitBall \
    --seed 6232020 \
    --maxsteps 2000 \
    --window 64 \
    --datadir $training_data
fi
