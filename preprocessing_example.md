# Introduction
This is an example script for preprocessing anatomical and function MRI (BOLD) data. Note that in practice, we don't write custom scripts like this to do preprocessing anymore. Instead, we use two robust and high quality packages: fMRIprep and mriqc, to do most, if not all of our MRI data preprocessing. These two packages are easy to use, reproducible, and implements current best practices to achieve best results. In most cases, there is no need to re-invent the wheel and do your own preprocessing. The purpose of this script is to provide examples and resources for you to understand, conceptually, how preprocessing works. We use both AFNI and FSL tools
https://afni.nimh.nih.gov/ \
https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FSL

### In the script
First we set the working directory so we can use full path instead of relative path to minimize error. Whenever possible, try to use the full path instead of the relative path


    WD='/data/backed_up/shared/fMRI_Practice/Example_Preprocessing_Pipeline'


### Data quality check
This step is now mostly acomplished by mriqc. We will search for outlier data points using 3dToutcount, it will count the "number of" voxels that have values that exceed a predefined range, typically outside of 3 median absolute deviation (MAD):
https://en.wikipedia.org/wiki/Median_absolute_deviation

    3dToutcount -automask \
      -fraction -polort 3 -legendre \
      ${WD}/sub-20200212TEST_task-MB3pe0_run-001_bold.nii.gz > ${WD}/outcount.1D

You can then plot the results saved in outocunt.1D. In afni lingo, 1D file is a text file used to store vectors of data. You can plot this file with function "1dplot", and can consider remove datapoints with large number of outliers in later processing.

    1dplot ${WD}/outcount.1D

We can also "despike" data to interpolate data from nearby timepoints to replace outliers.

    3dDespike -NEW -nomask \
      -prefix ${WD}/sub-20200212TEST_task-MB3pe0_run-001_ds_bold.nii.gz \
      ${WD}/sub-20200212TEST_task-MB3pe0_run-001_bold.nii.gz

### Motion correction
We use AFNI's 3dvolreg for motion correction \
https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dvolreg.html
This program implements 6 parameter rigid body alignment. This is the most common choice for fMRI motion correction, or any kind of alignment within the same imaging modality. \
We will save the motion parameters with the -1d flag. \
The "reference" image is the mean image across times, we will move all volumes to be aligned with the reference. The reference image is calculated using 3dTstat.

    3dTstat -prefix ${WD}/Tmean.nii.gz \
      ${WD}/sub-20200212TEST_task-MB3pe0_run-001_ds_bold.nii.gz

    3dvolreg -verbose -zpad 1 \
      -base ${WD}/Tmean.nii.gz \
      -1Dfile motion.1D \
      -prefix ${WD}/sub-20200212TEST_task-MB3pe0_run-001_mc_bold.nii.gz \
      -cubic \
      -maxdisp1D maxdisp.1D \
      ${WD}/sub-20200212TEST_task-MB3pe0_run-001_ds_bold.nii.gz

The motion parameter file "motion.1D" has 6 different columns, each represents the one of the rigid body parameters. \
They are: roll pitch yaw displacement:S-I  displacement:L-R  displacement:A-P\
We can use 1dplot to plot the timecourse of motion parameters.

    1dplot ${WD}/motion.1D

From these parameters, we can calculate an "euclidean norm" to get a measure of how much subjects move from one time point to another. Or, in AFNI's definition, "how much
the subject moved between successive TRs." This calculation is slightly different from mriqc's "frame-wise displacement" FD, but conceptually similar.

    1d_tool.py -infile ${WD}/motion.1D \
      -derivative  -collapse_cols euclidean_norm  \
      -write enorm.1D

    1dplot ${WD}/enorm.1D

Altogether, data from enorm.1D, outocunt.1D can help us decide if there are timepoints we should consider remove from the data. The user will, however, decide the criteria.


### Slice timing correction (optional)
Because fMRI acquisition is slow, often times take 1 to 2 seconds to acquire, different image "slices" are acquired at different time points, which could introduce systematic offset into the signals. To correct for this timing offset between different slices, we can run interpolation between slices.\
You would first need to create a text file that records the timing of when each slice was acquired.
To do that we can look into the data fields saved in the json file created during the dicom to nifti conversion. We then feed this text file into AFNI's 3dTshfit to perform slice timing correction. \
for more background, check out:\
https://matthew-brett.github.io/teaching/slice_timing.html

    cat sub-20200212TEST_task-MB3pe0_run-001_bold.json | grep SliceTiming | grep -Eo "[0-9]+\.*[0-9]*" > slice_timing.txt

The "grep" command above uses regular expression to extract data that matches the pattern we specified. For a brief intro, see: \
https://regexr.com/

    3dTshift -prefix shifted.nii.gz \
      -tpattern @slice_timing.txt \
      sub-20200212TEST_task-MB3pe0_run-001_bold.nii.gz

You will notice that we did not use the output file shifted.nii.gz in the later steps. If yo wish to incorporate this step you should use that file as the input to your later processing calls.

### Brain extraction
We need to know what is the spatial exten of the brain in our MRI images, and "extract" the brain from it. This step is necessary because we need to align the BOLD data with the brain, not the skull.
For details, see: \
https://www.fmrib.ox.ac.uk/primers/intro_primer/ExBox15/IntroBox15.html

fMRIprep implements a more effective program using "ANTS" (https://github.com/ANTsX/ANTs), that is not as easy to use and takes much longer to run. In this example we are going to use a FSL's BET, which is faster. We had to play around the -f option to decide "how much" brain we want to keep.

    bet ${WD}/sub-20200130_T1w.nii.gz ${WD}/T1w_brain.nii.gz -f 0.4


### Tissue segmentation
This step creates different tissue masks that separate white matter, CSF, and gray matter. These masks can then be used to extract noise signals for nuisance regression, and aid image alignment between T1 and T2 images. For details see see: \ https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FAST#Research_Overview

    fast -B ${WD}/T1w_brain.nii.gz

    # create the WM mask for BBR (see below)
    3dcalc -a ${WD}/T1w_brain_mixeltype.nii.gz \
      -expr 'equals(a,2)' -prefix ${WD}/T1w_wm.nii.gz


## Alignment / Registration / Spatial normalization
First check out the following to understand image registration and alignment \
http://jpeelle.net/mri/image_processing/registration.html \
https://www.youtube.com/watch?v=PaZinetFKGY&list=PL_CD549H9kgqJ1GDXAs1BWkgEimAHZeNX&index=2&t=9s \
https://afni.nimh.nih.gov/pub/dist/edu/latest/afni14_alignment/afni14_alignment.pdf\
https://www.fmrib.ox.ac.uk/primers/intro_primer/ExBox18/IntroBox18.html\


### Align BOLD with anatomical
Here we are using the averaged BOLD (motion correction target) as the input to align with T1.
This step will perform the boundary based registration (BBR), for details see:\
https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FLIRT_BBR \
To impelemt BBR, it is necessary to map out the gray/white matter boundary. We will therefore feed the program the the white matter mask we obtained from FAST with the "--wmseg" option. Rest of the input arguments should be pretty self explanatory. "--epi" stands for echo planar imaging, which is the sequecne for BOLD, is the input. "--t1" and "--t1brain" is the anatomcial image with and without brain extraction. This is the target for moving the BOLD to be alinged with.

    epi_reg --wmseg=${WD}/T1w_wm.nii.gz \
      -epi=${WD}/Tmean.nii.gz \
      --t1=${WD}/sub-20200130_T1w.nii.gz \
      --t1brain=${WD}/T1w_brain.nii.gz \
      --out=${WD}/func2struct


### Align anatomical with MNI atlas
First we do an affine registration between BOLD and T1. We do affine (12 parameters) instead of rigid body because BOLD image often have spatial distortions. Then we will refine the alignment using a nonlinear transformation procedure to
warp and deform the images so they match up between T1 and T2. The "warping" parameters will be saved to warp.nii.gz\
The target of the alignment is the MNI atlas. For more details, see: \
http://web.mit.edu/fsl_v5.0.10/fsl/doc/wiki/FNIRT(2f)UserGuide.html

    flirt -in ${WD}/T1w_brain.nii.gz \
      -ref $FSLDIR/data/standard/MNI152_T1_2mm_brain.nii.gz \
      -dof 12 \
      -out ${WD}/T1toMNIlin.nii.gz \
      -omat ${WD}/T1toMNIlin.mat

    fnirt --in=${WD}/T1w_brain.nii.gz \
      --aff=${WD}/T1toMNIlin.mat \
      --config=${WD}/T1_2_MNI152_2mm.cnf \
      --iout=${WD}/T1toMNInonlin.nii.gz \
      --cout=${WD}/T1toMNI_coef.nii.gz \
      --fout=${WD}/T1toMNI_warp.nii.gz


### Project BOLD into MNI space
Here, we will combine the BOLD_to_T1 transformation matrix with the T1_to_MNI warping into one transformation and apply that to the motion corrected functional data. We will use spline interpolation for sharper results.

    applywarp --ref=$FSLDIR/data/standard/MNI152_T1_2mm_brain.nii.gz \
      --in=${WD}/sub-20200212TEST_task-MB3_run-001_mc_bold.nii.gz \
      --warp=${WD}/T1toMNI_warp.nii.gz --premat=${WD}/func2struct.mat \
      --interp=spline \
      --out=sub-20200212TEST_task-MB3_run-001_mc_MNI_bold.nii.gz


### Intensity scaling.
Convert signal to percent of signal change that is relative the temporal mean. BOLD signal do not have absolute scale, so we need to normalize the scale to facilitate comparison between scans and between subjects. See https://sscc.nimh.nih.gov/sscc/gangc/TempNorm.html

    3dTstat -prefix ${WD}/meanBOLD_MNI.nii.gz ${WD}/sub-20200212TEST_task-MB3_run-001_mc_MNI_bold.nii.gz

    3dAutomask -prefix ${WD}/bold_mask.nii.gz ${WD}/sub-20200212TEST_task-MB3_run-001_mc_MNI_bold.nii.gz

    3dcalc -a ${WD}/sub-20200212TEST_task-MB3_run-001_mc_MNI_bold.nii.gz \
      -b ${WD}/meanBOLD_MNI.nii.gz \
      -c ${WD}/bold_mask.nii.gz \
      -expr "c*(a/b*100)" \
      -prefix ${WD}/sub-20200212TEST_task-MB3_run-001_mc_MNI_scaled_bold.nii.gz


### Optional step, spatial smoothing
We don't often do this anymore. Historically, it is often considered a good idea to do spatial smoothing and make signals from nearby voxels look more alike. see: \
http://jpeelle.net/mri/image_processing/smoothing.html

    3dmerge -1blur_fwhm 4 \
      -doall \
      -prefix ${WD}/sub-20200212TEST_task-MB3_run-001_mc_MNI_scaled_bold_sm4.nii.gz \
      ${WD}/sub-20200212TEST_task-MB3_run-001_mc_MNI_scaled_bold.nii.gz


### Perform nuisance regressions
BOLD data are noisy and are contaminated by physiological noise (breathing, cardio), machine noise, and motion related artifacts. These signals most likely do not have a "neuronal" origin, and therefore are not of interest to most researchers.
There are many "de-noisng" strategies for reducing the influence of noise sources. One of the most common strategy is to perform nuisance regression, where estimates of noise signals are entered into a regression model as predictor, and variances that can explained by noise sources are removed from the data before more analyses. The nuisance regressors that are commonly used include rigid body motion parameters, signals from CSF and white matter (again not of neuronal origin). For task fMRI, these nuisance regressors will be included along with task regressors, so nuisance regression is most often not a separate step by itself. Instead it is merged into the main regression analysis. For resting-state fMRI, we often perform nuisance regression on its own. Below is an example

To extract CSF and WM signals, we often perform a PCA analysis to create a set of signals that capture a large amount of signal variances in WM and CSF. WM and CSF unlikely contain "neural" signals, so signals there can be removed from the data. We will try to use 5 components to capture WM/CSF signals, this is also known as the compcor approach. See:\
Behzadi, Yashar, et al. "A component based noise correction method (CompCor) for BOLD and perfusion based fMRI." Neuroimage 37.1 (2007): 90-101.

We will prepare WM and CSF masks from the FAST outputs.

    3dcalc -a ${WD}/T1w_brain_pve_0.nii.gz -expr 'equals(a,1)' -prefix ${WD}/CSF.nii.gz

    3dcalc -a ${WD}/T1w_brain_pve_2.nii.gz -expr 'equals(a,1)' -prefix ${WD}/WM.nii.gz

We now have to resample the masks so they match the functional data dimension.

    3dresample -master ${WD}/sub-20200212TEST_task-MB3_run-001_mc_MNI_scaled_bold.nii.gz \
      -inset ${WD}/WM.nii.gz -prefix ${WD}/WM_rs.nii.gz

    3dresample -master ${WD}/sub-20200212TEST_task-MB3_run-001_mc_MNI_scaled_bold.nii.gz \
      -inset ${WD}/CSF.nii.gz -prefix ${WD}/CSF_rs.nii.gz

We will then use 3dpc to extract the first 5 principle component vectors from these masks.

    3dpc -mask ${WD}/WM_rs.nii.gz -pcsave 5 \
      -prefix ${WD}/WM_pc ${WD}/sub-20200212TEST_task-MB3_run-001_mc_MNI_scaled_bold.nii.gz
    3dpc -mask ${WD}/CSF_rs.nii.gz -pcsave 5 \
      -prefix ${WD}/CSF_pc ${WD}/sub-20200212TEST_task-MB3_run-001_mc_MNI_scaled_bold.nii.gz

Now we can perform the nuisance regression with these WM and CSF regressors created using 3dpc. We will include those as well as the motion esitmates into a regression model. Note that for task fMRI, this step will be included in the main regression analysis, but not as an additional step. Typically, for resting-state we will use 3dTproject for nuisance regression. For task fMRI, we will use 3dDeconvolve for task regression. For now we will treat this example as a resting-state scan.

For resing-state fMRI, we are also often only interested in slower frequency component in the signal, so we will include an additional bandpass filtering step in 3dTproject with the -passband option. The frequency range of interest common for resting-state fMRI is 0.001 to 0.01 hz. The -ort options include all the nuisance regressors we created.

Another option that we did not include in this example is to use the "-censor" option to remove datapoints with large outliers. You can consult the enorm.1D and outcount.1D files to determine if there are any timepoints you would like to exclude (or "censor") from the analysis.

    3dTproject \
      -input ${WD}/sub-20200212TEST_task-MB3_run-001_mc_MNI_scaled_bold.nii.gz \
      -ort ${WD}/WM_pc00.1D \
      -ort ${WD}/WM_pc01.1D \
      -ort ${WD}/WM_pc02.1D \
      -ort ${WD}/WM_pc03.1D \
      -ort ${WD}/WM_pc04.1D \
      -ort ${WD}/CSF_pc00.1D \
      -ort ${WD}/CSF_pc01.1D \
      -ort ${WD}/CSF_pc02.1D \
      -ort ${WD}/CSF_pc03.1D \
      -ort ${WD}/CSF_pc04.1D \
      -ort ${WD}/motion.1D \
      -passband 0.001, 0.01 \
      -mask ${WD}/bold_mask.nii.gz \
      -prefix ${WD}/preproc_output_for_resting-state.nii.gz
