#PBS -l walltime=2:00:00
#PBS -l select=1:ncpus=1:mem=80gb
#PBS -N recoding

cd "$PBS_O_WORKDIR/extraction_and_recoding/scripts" || cd /rds/general/project/hda_25-26/live/TDS/TDS_Group8/extraction_and_recoding/scripts || exit 1

eval "$(~/miniforge3/bin/conda shell.bash hook)"
conda activate g8-r413

Rscript 3-recode_variables.R

