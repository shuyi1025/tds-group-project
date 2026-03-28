#PBS -l walltime=4:00:00
#PBS -l select=1:ncpus=1:mem=80gb
#PBS -N extraction

cd "$PBS_O_WORKDIR/extraction_and_recoding/scripts"
#cd /rds/general/project/hda_25-26/live/TDS/TDS_Group8/extraction_and_recoding/scripts

eval "$(~/miniforge3/bin/conda shell.bash hook)"
conda activate r413

ukb_path=/rds/general/project/hda_25-26/live/TDS/General/Data/tabular.tsv

Rscript 2-extract_selected.R $ukb_path 

