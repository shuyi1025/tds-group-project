#!/bin/bash
#PBS -N aim2_3
#PBS -l walltime=08:00:00
#PBS -l select=1:ncpus=4:mem=60gb
#PBS -j oe

cd "$PBS_O_WORKDIR/pipeline_scripts" || cd /rds/general/project/hda_25-26/live/TDS/TDS_Group8/pipeline_scripts || exit 1

eval "$(~/miniforge3/bin/conda shell.bash hook)"
conda activate g8-r413

Rscript -e "rmarkdown::render('Aim2_3.Rmd', output_format = 'html_document')"