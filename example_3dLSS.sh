
# 3dDecovolve prep
for subject in 10054; do
    echo "Starting 3dDeconvolve on $subject"
    cd /data/backed_up/shared/ThalHi_MRI_2020/3dDeconvolve/sub-${subject}/

    # 3dmask_tool -input $(find /data/backed_up/shared/ThalHi_MRI_2020/fmriprep/sub-${subject}/func/*mask.nii.gz)

    outputpath="/data/backed_up/shared/ThalHi_MRI_2020/3dDeconvolve/sub-${subject}"
    data="/data/backed_up/shared/ThalHi_MRI_2020/fmriprep/sub-${subject}/func"
    cd $outputpath

    # run 3dDeconvolve in two steps
    # because 3dLSS will not take more than one "input", we need a clever way to concatenate the runs.
    # So we first run a nuisance regression (3dTproject) and use the residuals for model fitting. Here the residuals are "denoised" data
    3dTproject -input $(ls ${data}/sub-${subject}_task-ThalHi_run-*space-MNI152NLin2009cAsym_desc-preproc_bold*.nii.gz | sort -V) \
    -mask combined_mask+tlrc.BRIK \
    -polort 3 \
    -ort nuisance.1D \
    -prefix errts.nii.gz

    # step 2, run 3dDeconvolve to setup design matrix
    # because the errts.nii.gz file is a concatenation of all 8 runs. We need to manually setup a -concat to tell 3dDeconvolve where are the run breaks,
    # otherwise "local times" won't work properly. Also not that if you have a subject with different number of runs or different run length, you will have to set this up differntly.
    # As for the stim_times, here we are going to pull out single trial betas for the "dcb" condition, while putting all other conditions in the model.
    # We will have to do iterate through this 8  times, each time using a different condtion for the stim_times_IM option, while leaving the others in the stim_times column.
    # As for the basis function, we would have to think about whether TENT is appropriate.
    3dDeconvolve -input errts.nii.gz \
    -concat '1D: 0 216 432 648 864 1080 1296 1512' \
    -mask combined_mask+tlrc.BRIK \
    -censor censor.1D \
    -x1D dcb.xmat.1D \
    -local_times \
    -num_stimts 8 \
    -stim_times_IM  1 dcb.1D.txt 'TENT(6, 20.4, 9)' -stim_label 1 dcb \
    -stim_times  2 fcb.1D.txt 'TENT(6, 20.4, 9)' -stim_label 2 fcb \
    -stim_times  3 dpb.1D.txt 'TENT(6, 20.4, 9)' -stim_label 3 dpb \
    -stim_times  4 fpb.1D.txt 'TENT(6, 20.4, 9)' -stim_label 4 fpb \
    -stim_times  5 dcr.1D.txt 'TENT(6, 20.4, 9)' -stim_label 5 dcr \
    -stim_times  6 fcr.1D.txt 'TENT(6, 20.4, 9)' -stim_label 6 fcr \
    -stim_times  7 dpr.1D.txt 'TENT(6, 20.4, 9)' -stim_label 7 dpr \
    -stim_times  8 fpr.1D.txt 'TENT(6, 20.4, 9)' -stim_label 8 fpr \
    -x1D_stop \
    -allzero_OK \
    -jobs 4

    # step 3 3dLSS and run it. Again remember we will have to do this 8 diff times, each time using a different .xmat.1D file from the previous step.
    3dLSS -input errts.nii.gz \
    -matrix dcb.xmat.1D \
    -prefix dcb.LSS \
    -overwrite -verb

done
