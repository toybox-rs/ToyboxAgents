source .env/bin/activate
pip install -r REQUIREMENTS.txt

if [ "$1" = "local" ]; then 
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
    --datadir analysis/data/raw/Target/184758 analysis/data/raw/Target/556150 
    > exp_Target_MissedBall.sh
elif [ "$1" == "swarm" ]; then
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
    --datadir analysis/data/raw/Target/184758 analysis/data/raw/Target/556150 
    > $WORK1/autoexp/exp_Target_MissedBall.txt
fi