#!/bin/bash
#PBS -l walltime=24:00:00
#PBS -l select=1:ncpus=32:mem=100gb
#PBS -N imputation

cd /rds/general/project/hda_25-26/live/TDS/TDS_Group8

eval "$(~/miniforge3/bin/conda shell.bash hook)"
conda activate r413

Rscript imputation_sr.R


