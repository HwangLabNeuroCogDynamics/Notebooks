#!/usr/bin/env bash

# This is an example script for preprocessing anatomcial and function MRI (BOLD) data.
# Note that in practice, we don't write custom scripts like this to do preprocessing anymore.
# Instead, we use two robust and high quality packages: fMRIprep and mriqc, to do most, if not all of
# our MRI data preprocessing. These two packages are easy to use, reporducible, and implements current
# best practices to achieve best results. In most casese, there is no need to re-invent the wheel and do
# your own preprocessing.
#
# The purpose of this script is to provide examples and resources for you to understand, conceptually,
# how preprocessing works. We use both AFNI and FSL tools.
# https://afni.nimh.nih.gov/
# https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FSL


# Set the working directory so we can use full path instead of relative path to minimize error
WD='/data/backed_up/shared/fMRI_Practice/Example_Preprocessing_Pipeline'

### Data quality check
# This step is now mostly acomplished by mriqc.
# We will search for outlier datapoints using 3dToutcount, it will count the "number of" voxels that show
# intensity greater than a predefined range, typically outside of 3 median absolute deviation (MAD):
# https://en.wikipedia.org/wiki/Median_absolute_deviation
3dToutcount -automask -fraction -polort 3 -legendre                     \
    ${WD}/sub-20200212TEST_task-MB3pe0_run-001_bold.nii.gz > ${WD}/outcount.1D

# You can then plot the results saved in outocunt.1D. In afni lingo, 1D file is a text file vector sof datapoints.
# You can consider remove datapoints with large number of outliers in later processing.
1dplot ${WD}/outcount.1D

# We can also "despike" data to interplote data from nearby timepoints to replace outliers
3dDespike -NEW -nomask -prefix ${WD}/sub-20200212TEST_task-MB3pe0_run-001_ds_bold.nii.gz \
    ${WD}/sub-20200212TEST_task-MB3pe0_run-001_bold.nii.gz


### Motion correction
# To do motion correction, we use AFNI's 3dvolreg:
# https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dvolreg.html
# This program implements 6 parameter rigid body alignment. This is the most common
# choice for fMRI motion correction, or any kind of alignment within the same imaging modality.
# Finally, we will save the motion parameters with the -1d flat
# The "reference" image is the mean image across times, we will move all volumes to be aligned with the reference.
# The reference image is calculated using 3dTstat

3dTstat -prefix ${WD}/Tmean.nii.gz ${WD}/sub-20200212TEST_task-MB3pe0_run-001_ds_bold.nii.gz
3dvolreg -verbose -zpad 1 -base ${WD}/Tmean.nii.gz \
    -1Dfile motion.1D -prefix ${WD}/sub-20200212TEST_task-MB3pe0_run-001_mc_bold.nii.gz \
    -cubic \
    -maxdisp1D maxdisp.1D \
    ${WD}/sub-20200212TEST_task-MB3pe0_run-001_ds_bold.nii.gz

# The motion paramter file has 6 different columns, which represents the 6 paramter rigid body paramters.
# They are: roll pitch yaw dS  dL  dP
# we can plot the motion parameters, and calculate "euclidean norm" to get a measure of how much subjects
# move time point to timepoint. The calcualtion of this is slightly different from mriqc's "frame-wise displacement" FD,
# but conceptually similar.
1dplot ${WD}/motion.1D

1d_tool.py -infile ${WD}/motion.1D \
    -derivative  -collapse_cols euclidean_norm  \
    -write enorm.1D

1dplot ${WD}/enorm.1D

# Altogether, enorm.1D, outocunt.1D can help us decide if there are timepoints we should consider remove from the data


### Optional step, slice timing correction
# Because BOLD fMRI is slow, often times take 1 to 2 seconds to acquire,
# different image "slices" are acuirqed at different times.
# to crrect for the timing offset between different slices, we can perform
# interpolation between slices. However many labs don't do this step anymore.
# You would first need to create a text file that doucments the timing of
# when each slice was acquired.
# To do that we can look into the data fields recored in the json file created
# during the dicom conversion.
# then feed that text file into 3dTshfit to perform slice timing correction
# for more background, check out:
# https://matthew-brett.github.io/teaching/slice_timing.html
cat sub-20200212TEST_task-MB3pe0_run-001_bold.json | grep SliceTiming | grep -Eo "[0-9]*\.*[0-9]*" > slice_timing.txt
3dTshift -prefix shifted.nii.gz -tpattern @slice_timing.txt sub-20200212TEST_task-MB3pe0_run-001_bold.nii.gz
# You will notice we did not use the shifted.nii.gz in the later steps. If yo wish to incoroporate this step
# you should use that file as the input to your later processing calls.

### Brain extraction
# We need to know what is the spatial exten of the brain in our MRI images, and "extract"
# The brai from it. This step is necessary because we need to align the functional data
# with the brain, not the skull.
# For options,see https://www.fmrib.ox.ac.uk/primers/intro_primer/ExBox15/IntroBox15.html
# fMRIprep implements a more effective program using "ANTS", but takes much longer to run.
# we often have to paly around the -f option to decide "how much" brain we want to keep.
bet ${WD}/sub-20200130_T1w.nii.gz ${WD}/T1w_brain.nii.gz -f 0.4


### Tissue segmentation
# This step creates different tissue masks that separate white matter, CSF, and
# gray matter. These masks can be used to extract signals for noise regression, or
# aid image alignment between T1 adn T2 images.
# for details see see: https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FAST#Research_Overview
cd ${WD}/
fast -B ${WD}/T1w_brain.nii.gz
# create the WM mask
3dcalc -a ${WD}/T1w_brain_mixeltype.nii.gz -expr 'equals(a,2)' -prefix ${WD}/T1w_wm.nii.gz


#### Alignment / Registration / Spatial normalization
# First check out the following to understand image registration and alingment
# http://jpeelle.net/mri/image_processing/registration.html
# https://www.youtube.com/watch?v=PaZinetFKGY&list=PL_CD549H9kgqJ1GDXAs1BWkgEimAHZeNX&index=2&t=9s
# https://afni.nimh.nih.gov/pub/dist/edu/latest/afni14_alignment/afni14_alignment.pdf
# https://www.fmrib.ox.ac.uk/primers/intro_primer/ExBox18/IntroBox18.html

### Align BOLD with anatomical
# Here we are using the averaged BOLD (motion correction target) as the input to align with T1.
# This step will perform the boundary based registration (BBR), for details see:
# https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FLIRT_BBR
# To impelemt BBR, it is necessary to have a gray/white matter boundary.
# We will therefore feed the program the the white matter mask we obtained from FAST,
# with the "--wmseg" option.
# Rest of the input arguments should be pretty self explanatory.
# "--epi" stands for echo planar imaging, which is the sequecne for BOLD, is the input.
# "--t1" and "--t1brain" is the anatomcial image with and without brain extraction. This is the
# target for moving the BOLD to be alinged with.
epi_reg --wmseg=${WD}/T1w_wm.nii.gz --epi=${WD}/Tmean.nii.gz \
    --t1=${WD}/sub-20200130_T1w.nii.gz --t1brain=${WD}/T1w_brain.nii.gz --out=${WD}/func2struct


### Align anatomical with MNI atlas
# First we do an affine registration between BOLD and T1.
# We do affine instead of rigid body is because BOLD image often have spatial distortions.
# Thus, we will e using 12 DOF given that we are alinging two different modalities,
# then we will refine the alignment using a nonlinear transformation procedure to
# warp and deform the images so they match up between T1 and T2.
# The "warping" parameters will be saved to _warp.nii.gz
# the target of the alignment is the MNI atlas
# For more details, see
# http://web.mit.edu/fsl_v5.0.10/fsl/doc/wiki/FNIRT(2f)UserGuide.html
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


### Intensity scaling. Convert signal to percent of signal change that is relative the temporal mean.
# BOLD signal do not have absolute scale, so we need to normalize the scale to facilitate comparison
# between scans and between subjects.
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
