#!/bin/bash 
#
#SBATCH --output=exp_SmarterStayAlive_HitBall.out
#SBATCH -e exp_SmarterStayAlive_HitBall.err
#SBATCH --time=0-11:59

source .env/bin/activate
pip install -r REQUIREMENTS.txt 1> /dev/null

if [ "$1" = "local" ]; then 
  if [ "$2" = "learn" ]; then
    training_data=`ls -d analysis/data/raw/SmarterStayAlive/* | paste -s -d' '`
  fi
  python -m autoexp \
    breakout \
    --model models.breakout.target  \
    --agent SmarterStayAlive \
    --seed 6232020 \
    --maxsteps 2000 \
    --window 64 \
    --outcome HitBall \
    --counterfactual MissedBall \
    --outdir exp/SmarterStayAlive/HitBall \
    --datadir $training_data \
    --constraints 'bricks\[.*?\].*' \
    1> exp_SmarterStayAlive_HitBall.out 2> exp_SmarterStayAlive_HitBall.err
elif [ "$1" = "swarm" ]; then
  echo "Executing on swarm..."
  if [ "$2" = "learn" ]; then 
    training_data=`ls -d $WORK1/ToyboxAgents/SmarterStayAlive/* | paste -s -d' '`
  fi
  python -m autoexp breakout \
    --model models.breakout.target  \
    --agent SmarterStayAlive \
    --outcome HitBall \
    --counterfactual MissedBall \
    --outdir $WORK1/autoexp/exp/SmarterStayAlive/HitBall \
    --seed 6232020 \
    --maxsteps 2000 \
    --window 64 \
    --datadir $training_data
fi
