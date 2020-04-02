
#!/bin/bash
#
#SBATCH -job-name=compress
#SBATCH --output=compress.out
#SBATCH -e logs/compress.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --mem=1024
tar -czf 
