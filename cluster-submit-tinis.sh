#!/bin/sh
#PBS -l nodes=1:ppn=32
#PBS -l pmem=32220mb

## -l nodes=1:ppn=16
## -l pmem=3882mb

#PBS -l walltime=48:00:00
#PBS -q fat

#PBS -m ae -M M.Bradbury@warwick.ac.uk
#PBS -N "ILP_SLP_5x5"

oplrun -v -w -deploy -p SLP 5x5
