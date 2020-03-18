for script in `ls scripts | grep run`; do
    sbatch scripts/$script
done
