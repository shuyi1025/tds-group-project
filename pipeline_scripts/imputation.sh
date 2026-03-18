#!/bin/bash
#PBS -l walltime=24:00:00
#PBS -l select=1:ncpus=32:mem=200gb
#PBS -N pred_no_skip

#PBS -l walltime=48:00:00
#PBS -l select=1:ncpus=128:ompthreads=128:mem=200gb
#PBS -N imputation

cd /rds/general/project/hda_25-26/live/TDS/TDS_Group8/pipeline_scripts/

eval "$(~/miniforge3/bin/conda shell.bash hook)"
conda activate r413

Rscript imputation_no_skip.R