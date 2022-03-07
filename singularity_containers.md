# Singularity Containers

## fmriprep

> SINGULARITY_TMPDIR=/mnt/nfs/lss/lss_kahwang_hpc/tmp/ singularity build fmriprep-{version}.simg docker://nipreps/fmriprep:{version}

where {version} should be replaced with the desired version of fMRIPrep that you want to download. Setting the other tmp directory is neccesary because the /tmp directory gets too full and the build fails.

More info here:  
https://fmriprep.org/en/1.5.1/singularity.html

## mriqc

> SINGULARITY_TMPDIR=/mnt/nfs/lss/lss_kahwang_hpc/tmp/ singularity build mriqc.simg docker://nipreps/mriqc:latest

## afni

> SINGULARITY_TMPDIR=/mnt/nfs/lss/lss_kahwang_hpc/tmp/ singularity build fmriprep-{version}.simg docker://afni/afni
