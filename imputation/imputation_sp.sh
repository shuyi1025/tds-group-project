#PBS -l walltime=24:00:00
#PBS -l select=1:ncpus=128:mem=100gb
#PBS -N imputation

cd /rds/general/project/hda_25-26/live/TDS/TDS_Group8/imputation

eval "$(~/anaconda3/bin/conda shell.bash hook)"
source activate r413

Rscript imputation_sp.R

