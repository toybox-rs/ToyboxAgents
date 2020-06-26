#!/bin/bash 
#
#SBATCH --output=exp_Target_MoveSame.out
#SBATCH -e exp_Target_MoveSame.err
#SBATCH --time=0-11:59

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
    --outcome MoveSame \
    --counterfactual MoveOpposite \
    --outdir exp/Target/MoveSame \
    --datadir $training_data \
    --constraints 'bricks\[.*?\].*' \
    1> exp_Target_MoveSame.out 2> exp_Target_MoveSame.err
elif [ "$1" = "swarm" ]; then
  echo "Executing on swarm..."
  if [ "$2" = "learn" ]; then 
    training_data=`ls -d $WORK1/ToyboxAgents/Target/* | paste -s -d' '`
  fi
  python -m autoexp breakout \
    --model models.breakout.target  \
    --agent Target \
    --outcome MoveSame \
    --counterfactual MoveOpposite \
    --outdir $WORK1/autoexp/exp/Target/MoveSame \
    --seed 6232020 \
    --maxsteps 2000 \
    --window 64 \
    --datadir $training_data
fi
