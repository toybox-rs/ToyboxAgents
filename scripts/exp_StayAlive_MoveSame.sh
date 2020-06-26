#!/bin/bash 
#
#SBATCH --output=exp_StayAlive_MoveSame.out
#SBATCH -e exp_StayAlive_MoveSame.err
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
    --outcome MoveSame \
    --counterfactual MoveOpposite \
    --outdir exp/StayAlive/MoveSame \
    --datadir $training_data \
    --constraints 'bricks\[.*?\].*' \
    1> exp_StayAlive_MoveSame.out 2> exp_StayAlive_MoveSame.err
elif [ "$1" = "swarm" ]; then
  echo "Executing on swarm..."
  if [ "$2" = "learn" ]; then 
    training_data=`ls -d $WORK1/ToyboxAgents/StayAlive/* | paste -s -d' '`
  fi
  python -m autoexp breakout \
    --model models.breakout.target  \
    --agent StayAlive \
    --outcome MoveSame \
    --counterfactual MoveOpposite \
    --outdir $WORK1/autoexp/exp/StayAlive/MoveSame \
    --seed 6232020 \
    --maxsteps 2000 \
    --window 64 \
    --datadir $training_data
fi
