#!/bin/bash
#
#SBATCH -job-name=CSVs
#SBATCH -o logs/make_csvs.out
#SBATCH -e logs/make_csvs.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --time=05:00

agents="Target StayAlive StayAliveJitter SmarterStayAlive"

while true; do
    jobs=`squeue -uetosch | grep defq | wc -l`
    if [ -z $jobs ]; then
        for agent in $agents; do
            sbatch --time=0-11:59 make_csvs.py $WORK1/ToyboxAgents $agent
        done
        exit
    fi
    sleep(1000)
done