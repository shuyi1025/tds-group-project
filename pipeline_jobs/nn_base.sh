#PBS -N nn_base
#PBS -l select=1:ncpus=10:mem=64gb
#PBS -l walltime=24:00:00
#PBS -j oe
#PBS -o nn_base.out
#PBS -e nn_base.err

cd "$PBS_O_WORKDIR/pipeline_scripts/Aim4" || cd /rds/general/project/hda_25-26/live/TDS/TDS_Group8/pipeline_scripts/Aim4 || exit 1

eval "$(~/miniforge3/bin/conda shell.bash hook)"
conda activate g8-py312

python nn_baseline.py
