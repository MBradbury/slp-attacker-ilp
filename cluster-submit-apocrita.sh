#!/bin/sh
#$ -cwd              # Set the working directory for the job to the current directory
#$ -V
#$ -pe smp 12        # Request 24 CPU cores
#$ -l h_rt=01:00:00  # Request 24 hour runtime
#$ -l h_vmem=1G      # Request 1GB RAM per core, i.e. 24GB total
#$ -m ae -M M.Bradbury@warwick.ac.uk
#$ -N "ILP SLP 3x3"
oplrun -v -w -deploy -p SLP 3x3
