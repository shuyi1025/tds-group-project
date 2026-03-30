#!/bin/bash
#PBS -N rf_base
#PBS -l walltime=08:00:00
#PBS -l select=1:ncpus=10:mem=64gb
#PBS -o rf_base.out
#PBS -e rf_base.err

cd "$PBS_O_WORKDIR/pipeline_scripts/Aim4" || cd /rds/general/project/hda_25-26/live/TDS/TDS_Group8/pipeline_scripts/Aim4 || exit 1

mkdir -p ../../pipeline_outputs/aim4_output

eval "$(~/miniforge3/bin/conda shell.bash hook)"
conda activate g8-py312

python rf_baseline_tune.py