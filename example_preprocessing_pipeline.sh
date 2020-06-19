#!/usr/bin/env bash

# An example script for preprocessing anatomcial and function MRI (BOLD) data
# Note, in practice, we don't write custom scripts like this anymore.
# Instead, we use two robust and high quality packages, fMRIprep and MRIqc to do
# our MRI preprocessing. Those two packages are easy to use, reporducible, and adopt
# best practices for best results.
# The purpose of this script is to provide examples and resources for you to understand, conceptually
# how preprocessing works.

#bash hate spaces. set working directory so we can use full path instead of relative path to minimize error
WD='/data/backed_up/shared/fMRI_Practice/Example_Preprocessing_Pipeline'


### Step 1, motion correction of functional data
# For details https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/MCFLIRT
# Here we use dof of 6, which indicates rigid body alignment. This is the most appropriate
# choice for motion correction, or any kind of alignment within the same imaging modality.
# We will set the final interpolation to spline (since is fine too). That gives the most "crip"
# final results.
# For cost function, we will use normal correlation.
# to understand what final interpolation, cost function, and DOF means. Check out:
# https://www.youtube.com/watch?v=PaZinetFKGY&list=PL_CD549H9kgqJ1GDXAs1BWkgEimAHZeNX&index=2&t=9s
# We will save the motion parameters with the -mats and -plots options.
# The "reference" image is the mean image across times.

mcflirt -out ${WD}/sub-20200212TEST_task-MB3_run-001_mc_bold.nii.gz \
-in ${WD}/sub-20200212TEST_task-MB3pe0_run-001_bold.nii.gz \
-spline_final \
-cost normcorr \
-dof 6 -meanvol -mats -plots


#### Brain extraction
#for options,see https://www.fmrib.ox.ac.uk/primers/intro_primer/ExBox15/IntroBox15.html
#fMRIprep implements a more effective program, but takes much longer to run.
# we often have to paly around the -f option to decide "how much" brain we want to keep.
bet ${WD}/sub-20200130_T1w.nii.gz ${WD}/T1w_brain.nii.gz -f 0.4

### Tissue segmentation, create different tissue masks
# see: https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FAST#Research_Overview
cd ${WD}/
fast -B ${WD}/T1w_brain.nii.gz
# create the WM mask
3dcalc -a ${WD}/T1w_brain_mixeltype.nii.gz -expr 'equals(a,2)' -prefix ${WD}/T1w_wm.nii.gz


#### Alignment
# check out the following to understand these steps better
# http://jpeelle.net/mri/image_processing/registration.html
# https://www.youtube.com/watch?v=PaZinetFKGY&list=PL_CD549H9kgqJ1GDXAs1BWkgEimAHZeNX&index=2&t=9s
# https://afni.nimh.nih.gov/pub/dist/edu/latest/afni14_alignment/afni14_alignment.pdf
# https://www.fmrib.ox.ac.uk/primers/intro_primer/ExBox18/IntroBox18.html

### Align BOLD with anatomical
# Here we are using the averaged BOLD (motion correction target) as the input to align with T1
# the script will perform boundary based registration (BBR), see:
# https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FLIRT_BBR
epi_reg --wmseg=${WD}/T1w_wm.nii.gz --epi=${WD}/sub-20200212TEST_task-MB3_run-001_mc_bold_mean_reg.nii.gz \
--t1=${WD}/sub-20200130_T1w.nii.gz --t1brain=${WD}/T1w_brain.nii.gz --out=${WD}/func2struct


### Align anatomical with MNI atlas
# first we do an affine registration between BOLD and T1,
# we will e using 12 DOF given that we are alinging two different modalities
# then we will refine the alignment using nonlinear transformation,
# the "warping" parameters will be saved to _warp.nii.gz
# the target of the alignment is the MNI atlas
flirt -in ${WD}/T1w_brain.nii.gz -ref $FSLDIR/data/standard/MNI152_T1_2mm_brain.nii.gz \
-dof 12 -out ${WD}/T1toMNIlin.nii.gz -omat ${WD}/T1toMNIlin.mat
fnirt --in=${WD}/T1w_brain.nii.gz --aff=${WD}/T1toMNIlin.mat \
--config=${WD}/T1_2_MNI152_2mm.cnf --iout=${WD}/T1toMNInonlin.nii.gz \
--cout=${WD}/T1toMNI_coef.nii.gz --fout=${WD}/T1toMNI_warp.nii.gz


### Project BOLD into MNI space
# Here, we will combine the BOLD_to_T1 transformation matrix with the T1_to_MNI warping into one transformation
# and apply that to the motion corrected functional data. We will use spline interpolation for sharper results.
applywarp --ref=$FSLDIR/data/standard/MNI152_T1_2mm_brain.nii.gz \
--in=${WD}/sub-20200212TEST_task-MB3_run-001_mc_bold.nii.gz \
--warp=${WD}/T1toMNI_warp.nii.gz --premat=${WD}/func2struct.mat \
--interp=spline \
--out=sub-20200212TEST_task-MB3_run-001_mc_MNI_bold.nii.gz


### Intensity scaling. Convert signal to percent of signal change relative the mean.
# BOLD signal do not have absolute scale, so we need to normalize the scale to facilitate comparison.
# see https://sscc.nimh.nih.gov/sscc/gangc/TempNorm.html
3dTstat -prefix meanBOLD_MNI.nii.gz sub-20200212TEST_task-MB3_run-001_mc_MNI_bold.nii.gz
3dcalc -a sub-20200212TEST_task-MB3_run-001_mc_MNI_bold.nii.gz -b meanBOLD_MNI.nii.gz \
       -expr '(a/b*100)*step(a)*step(b)'       \
       -prefix sub-20200212TEST_task-MB3_run-001_mc_MNI_scaled_bold.nii.gz


### Spatial smoothing
# we don't often do this anymore. Historically, it is often considered a good idea
# to do spatial smoothing and make signals from nearby voxels look more alike.
# see: http://jpeelle.net/mri/image_processing/smoothing.html
3dmerge -1blur_fwhm 4 -doall -prefix sub-20200212TEST_task-MB3_run-001_mc_MNI_scaled_bold_sm4.nii.gz \
               sub-20200212TEST_task-MB3_run-001_mc_MNI_scaled_bold.nii.gz
