## NOT AN EXECUTABLE!!
## This file should not be run as an executable. 
## The .sh extension is only here to trigger syntax 
## highlighting in an IDE
#!/bin/bash 
#
#SBATCH --output=$WORK1/ToyboxAgents/run_{agent}_{outcome_fmt}.out
#SBATCH -e $WORK1/ToyboxAgents/run_{agent}_{outcome_fmt}.err
#SBATCH --time={time}
#SBATCH --partition={partition}

source .env/bin/activate
pip install -r REQUIREMENTS.txt 1> /dev/null

if [ "$1" = "local" ]; then 
  if [ "$2" = "learn" ]; then
    training_data=`ls -d analysis/data/raw/{agent}/* | paste -s -d' '`
  fi
  python -m autoexp \
    breakout \
    --model {model}  \
    --agent {agent} \
    --seed {seed} \
    --maxsteps 2000 \
    --window 64 \
    --outcome {outcome} \
    --counterfactual {counterfactual} \
    --outdir exp/{agent}/{outcome_fmt} \
    --datadir $training_data \
    --constraints 'bricks\[.*?\].*' \
    1> run_{agent}_{outcome}.out 2> run_{agent}_{outcome_fmt}.err
elif [ "$1" = "swarm" ]; then
  echo "Executing on swarm..."
  if [ "$2" = "learn" ]; then 
    training_data=`ls -d $WORK1/ToyboxAgents/{agent}/* | paste -s -d' '`
  fi
  python -m autoexp breakout \
    --model {model}  \
    --agent {agent} \
    --outcome {outcome} \
    --counterfactual {counterfactual} \
    --outdir $WORK1/autoexp/exp/{agent}/{outcome_fmt} \
    --seed {seed} \
    --maxsteps 2000 \
    --window 64 \
    --datadir $training_data
fi
