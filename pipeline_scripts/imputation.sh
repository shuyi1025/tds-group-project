#!/bin/bash
#PBS -l walltime=24:00:00
#PBS -l select=1:ncpus=128:ompthreads=128:mem=200gb
#PBS -N imputation

eval "$(~/miniforge3/bin/conda shell.bash hook)"
conda activate r413

Rscript pipeline_scripts/imputation.R