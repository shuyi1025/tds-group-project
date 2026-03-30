#PBS -N nn_bio
#PBS -l select=1:ncpus=10:mem=64gb
#PBS -l walltime=24:00:00
#PBS -j oe
#PBS -o nn_bio.log
#PBS -e nn_bio.log

cd "$PBS_O_WORKDIR/pipeline_scripts/Aim4" || cd /rds/general/project/hda_25-26/live/TDS/TDS_Group8/pipeline_scripts/Aim4 || exit 1

eval "$(~/miniforge3/bin/conda shell.bash hook)"
conda activate torch_env

python nn_biomarker.py
