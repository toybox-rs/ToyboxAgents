for script in `ls scripts | grep run_`; do
    echo "running $script"
    sbatch scripts/$script
done
