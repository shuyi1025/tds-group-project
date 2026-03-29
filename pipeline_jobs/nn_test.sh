#!/bin/bash
#PBS -l walltime=10:00:00
#PBS -l select=1:ncpus=1:mem=120gb
#PBS -N tuning

cd "$PBS_O_WORKDIR/pipeline_scripts/Aim4/NN"
#cd /rds/general/project/hda_25-26/live/TDS/TDS_Group8/pipeline_scripts/Aim4/NN

eval "$(~/miniforge3/bin/conda shell.bash hook)"
conda activate torch_env

# Run the Python script
python nn_baseline_params.py


