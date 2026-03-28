#!/bin/bash
#PBS -l walltime=00:30:00
#PBS -l select=1:ncpus=1:mem=20gb
#PBS -N preprocessing

cd "$PBS_O_WORKDIR/pipeline_scripts"
#cd /rds/general/project/hda_25-26/live/TDS/TDS_Group8/pipeline_scripts

eval "$(~/miniforge3/bin/conda shell.bash hook)"
conda activate r413

Rscript -e "rmarkdown::render('final_preprocessing.Rmd', output_format = 'html_document')"