#!/bin/bash
#SBATCH --job-name test
#SBATCH --cpus-per-task 6
#SBATCH --output /projects/ovcare/classification/cchen/ml/slurm/test.%j.out
#SBATCH --error  /projects/ovcare/classification/cchen/ml/slurm/test.%j.out
#SBATCH -w {w}
#SBATCH -p {p}
#SBATCH --gres=gpu:1
#SBATCH --time=3-00:00:00
#SBATCH --chdir /projects/ovcare/classification/cchen/ml/singularity_create_groups
#SBATCH --mem=30G

DLHOST04_SINGULARITY=/opt/singularity-3.4.0/bin
if [[ -d "$DLHOST04_SINGULARITY" ]]; then
    PATH="{$PATH}:{$DLHOST04_SINGULARITY}"
fi
if [[ -d /projects/ovcare/classification/cchen ]]; then
    cd /projects/ovcare/classification/cchen/ml/singularity_create_groups
    source /projects/ovcare/classification/cchen/{pyenv}
fi

if [[ ! -d create_groups/tests/mock ]]; then
    tar xvzf create_groups/tests/mock.tar.gz -C create_groups/tests/
fi

mkdir -p create_groups/tests/outputs

# pytest -s -vv create_groups/tests/test_create_groups.py::TestCreateGroups::test_parse_args_1
# pytest -s -vv create_groups/tests/test_auxiliary.py
# pytest -s -vv create_groups/tests/test_create_groups.py
# pytest -s -vv create_groups/tests/test_balance_groups.py

pytest -s -vv create_groups/tests