#!/bin/bash
#PBS -N rf_ee
#PBS -l walltime=08:00:00
#PBS -l select=1:ncpus=10:mem=64gb
#PBS -o rf_ee.out
#PBS -e rf_ee.err

cd "$PBS_O_WORKDIR/pipeline_scripts/Aim4" || cd /rds/general/project/hda_25-26/live/TDS/TDS_Group8/pipeline_scripts/Aim4 || exit 1

mkdir -p ../../pipeline_outputs/aim4_output

eval "$(~/miniforge3/bin/conda shell.bash hook)"
conda activate g8-py312

python rf_ee_tune.py