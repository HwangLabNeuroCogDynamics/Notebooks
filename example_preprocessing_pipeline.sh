#!/usr/bin/env bash

# This is an example script for preprocessing anatomcial and function MRI (BOLD) data
# Note that in practice, we don't write custom scripts like this to do preprocessing anymore.
# Instead, we use two robust and high quality packages: fMRIprep and MRIqc to do most if not all of
# our MRI preprocessing. Those two packages are easy to use, reporducible, and implements current
# best practices for best results. There is really no good reason to re-invent the wheel and do
# your own preprocessing.
# The purpose of this script is to provide examples and resources for you to understand, conceptually,
# how fMRI preprocessing works.

#bash hate spaces. set working directory so we can use full path instead of relative path to minimize error
WD='/data/backed_up/shared/fMRI_Practice/Example_Preprocessing_Pipeline'


### Motion correction of functional data
# For details see https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/MCFLIRT
# Here we explain some of the arguments:
# "-dof 6": Here we use dof of 6, which implements rigid body alignment. This is the most common
# choice for fMRI motion correction, or any kind of alignment within the same imaging modality.
# "-cost "": For cost function, we will use normal correlation, this is typically the default for BOLD fMRI
# "=spline_fianl": We will set the final interpolation to spline (sinc is fine too). That gives the most "crip"
# shaper, final results.
# To understand what final interpolation, cost function, and DOF mean, check out:
# https://www.youtube.com/watch?v=PaZinetFKGY&list=PL_CD549H9kgqJ1GDXAs1BWkgEimAHZeNX&index=2&t=9s
# Finally, we will save the motion parameters with the -mats and -plots options.
# The "reference" image is the mean image across times.

mcflirt -out ${WD}/sub-20200212TEST_task-MB3_run-001_mc_bold.nii.gz \
-in ${WD}/sub-20200212TEST_task-MB3pe0_run-001_bold.nii.gz \
-spline_final \
-cost normcorr \
-dof 6 -meanvol -mats -plots

### Optional step, slice timing correction
# Because BOLD fMRI is slow, often times take 1 to 2 seconds to acquire
# a whole brain image, different image "slices" are acuirqed at different times.
# to crrect for the timing offset between different slices, we can perform
# interpolation between slices. However many labs don't do this step anymore.
# You would first need to create a text file that doucments the timing of
# when each slice was acquired.
# To do that we can look into the data fields recored in the json file created
# during the dicom conversion.
# then feed that text file into 3dTshfit to perform slice timing correction
# for more background, check out https://matthew-brett.github.io/teaching/slice_timing.html
cat sub-20200212TEST_task-MB3pe0_run-001_bold.json | grep SliceTiming | grep -Eo "[0-9]*\.*[0-9]*" > slice_timing.txt
3dTshift -prefix shifted.nii.gz -tpattern @slice_timing.txt sub-20200212TEST_task-MB3pe0_run-001_bold.nii.gz


### Brain extraction
# We need to know what is the spatial exten of the brain in our MRI images.
# for options,see https://www.fmrib.ox.ac.uk/primers/intro_primer/ExBox15/IntroBox15.html
# fMRIprep implements a more effective program using "ANTS", but takes much longer to run.
# we often have to paly around the -f option to decide "how much" brain we want to keep.
bet ${WD}/sub-20200130_T1w.nii.gz ${WD}/T1w_brain.nii.gz -f 0.4


### Tissue segmentation
# create different tissue masks that separate white matter, CSF, and
# gray matter. These masks can be used to extract signals for noise regression, or
# aid image alignment between T1 adn T2 images.
# for details see see: https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FAST#Research_Overview
cd ${WD}/
fast -B ${WD}/T1w_brain.nii.gz
# create the WM mask
3dcalc -a ${WD}/T1w_brain_mixeltype.nii.gz -expr 'equals(a,2)' -prefix ${WD}/T1w_wm.nii.gz


#### Alignment
# First check out the following to understand image registration and alingment
# http://jpeelle.net/mri/image_processing/registration.html
# https://www.youtube.com/watch?v=PaZinetFKGY&list=PL_CD549H9kgqJ1GDXAs1BWkgEimAHZeNX&index=2&t=9s
# https://afni.nimh.nih.gov/pub/dist/edu/latest/afni14_alignment/afni14_alignment.pdf
# https://www.fmrib.ox.ac.uk/primers/intro_primer/ExBox18/IntroBox18.html

### Align BOLD with anatomical
# Here we are using the averaged BOLD (motion correction target) as the input to align with T1
# the script will perform boundary based registration (BBR), for details see:
# https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FLIRT_BBR
# To impelemt BBR, it is necessary to have a gray/white matter boundary.
# We will feed the program the the white matter mask from FAST, with the "--wmseg" option.
# Rest of the input arguments should be pretty self explanatory.
# "--epi" stands for echo planar imaging, which is the sequecne for BOLD, is the input.
# "--t1" and "--t1brain" is the anatomcial image with and without brain extraction. This is the
# target for moving the BOLD to be alinged with.
epi_reg --wmseg=${WD}/T1w_wm.nii.gz --epi=${WD}/sub-20200212TEST_task-MB3_run-001_mc_bold_mean_reg.nii.gz \
--t1=${WD}/sub-20200130_T1w.nii.gz --t1brain=${WD}/T1w_brain.nii.gz --out=${WD}/func2struct


### Align anatomical with MNI atlas
# first we do an affine registration between BOLD and T1,
# we will e using 12 DOF given that we are alinging two different modalities,
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
