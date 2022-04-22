#!/usr/bin/env bash

# Set the working directory so we can use full path instead of relative path to minimize error
WD='/data/backed_up/shared/fMRI_Practice/Example_Preprocessing_Pipeline'

### Data quality check
3dToutcount -automask -fraction -polort 3 -legendre                     \
    ${WD}/sub-20200212TEST_task-MB3pe0_run-001_bold.nii.gz > ${WD}/outcount.1D

1dplot ${WD}/outcount.1D

3dDespike -NEW -nomask -prefix ${WD}/sub-20200212TEST_task-MB3pe0_run-001_ds_bold.nii.gz \
    ${WD}/sub-20200212TEST_task-MB3pe0_run-001_bold.nii.gz


### Motion correction
3dTstat -prefix ${WD}/Tmean.nii.gz ${WD}/sub-20200212TEST_task-MB3pe0_run-001_ds_bold.nii.gz
3dvolreg -verbose -zpad 1 -base ${WD}/Tmean.nii.gz \
    -1Dfile motion.1D -prefix ${WD}/sub-20200212TEST_task-MB3pe0_run-001_mc_bold.nii.gz \
    -cubic \
    -maxdisp1D maxdisp.1D \
    ${WD}/sub-20200212TEST_task-MB3pe0_run-001_ds_bold.nii.gz


1dplot ${WD}/motion.1D

1d_tool.py -infile ${WD}/motion.1D \
    -derivative  -collapse_cols euclidean_norm  \
    -write enorm.1D

1dplot ${WD}/enorm.1D


### Optional step, slice timing correction
cat sub-20200212TEST_task-MB3pe0_run-001_bold.json | grep SliceTiming | grep -Eo "[0-9]*\.*[0-9]*" > slice_timing.txt
3dTshift -prefix shifted.nii.gz -tpattern @slice_timing.txt sub-20200212TEST_task-MB3pe0_run-001_bold.nii.gz


### Brain extraction
bet ${WD}/sub-20200130_T1w.nii.gz ${WD}/T1w_brain.nii.gz -f 0.4


### Tissue segmentation
cd ${WD}/
fast -B ${WD}/T1w_brain.nii.gz
# create the WM mask
3dcalc -a ${WD}/T1w_brain_mixeltype.nii.gz -expr 'equals(a,2)' -prefix ${WD}/T1w_wm.nii.gz


#### Alignment / Registration / Spatial normalization

### Align BOLD with anatomical
epi_reg --wmseg=${WD}/T1w_wm.nii.gz --epi=${WD}/Tmean.nii.gz \
    --t1=${WD}/sub-20200130_T1w.nii.gz --t1brain=${WD}/T1w_brain.nii.gz --out=${WD}/func2struct


### Align anatomical with MNI atlas
flirt -in ${WD}/T1w_brain.nii.gz -ref $FSLDIR/data/standard/MNI152_T1_2mm_brain.nii.gz \
    -dof 12 -out ${WD}/T1toMNIlin.nii.gz -omat ${WD}/T1toMNIlin.mat
fnirt --in=${WD}/T1w_brain.nii.gz --aff=${WD}/T1toMNIlin.mat \
    --config=${WD}/T1_2_MNI152_2mm.cnf --iout=${WD}/T1toMNInonlin.nii.gz \
    --cout=${WD}/T1toMNI_coef.nii.gz --fout=${WD}/T1toMNI_warp.nii.gz


### Project BOLD into MNI space
applywarp --ref=$FSLDIR/data/standard/MNI152_T1_2mm_brain.nii.gz \
    --in=${WD}/sub-20200212TEST_task-MB3_run-001_mc_bold.nii.gz \
    --warp=${WD}/T1toMNI_warp.nii.gz --premat=${WD}/func2struct.mat \
    --interp=spline \
    --out=sub-20200212TEST_task-MB3_run-001_mc_MNI_bold.nii.gz


### Intensity scaling. Convert signal to percent of signal change that is relative the temporal mean.
3dTstat -prefix ${WD}/meanBOLD_MNI.nii.gz ${WD}/sub-20200212TEST_task-MB3_run-001_mc_MNI_bold.nii.gz
3dAutomask -prefix ${WD}/bold_mask.nii.gz ${WD}/sub-20200212TEST_task-MB3_run-001_mc_MNI_bold.nii.gz
3dcalc -a ${WD}/sub-20200212TEST_task-MB3_run-001_mc_MNI_bold.nii.gz -b ${WD}/meanBOLD_MNI.nii.gz \
    -c ${WD}/bold_mask.nii.gz \
    -expr '(a/b*100)*step(a)*step(b)*c'       \
    -prefix ${WD}/sub-20200212TEST_task-MB3_run-001_mc_MNI_scaled_bold.nii.gz


### Optional step, spatial smoothing
3dmerge -1blur_fwhm 4 -doall -prefix ${WD}/sub-20200212TEST_task-MB3_run-001_mc_MNI_scaled_bold_sm4.nii.gz \
    ${WD}/sub-20200212TEST_task-MB3_run-001_mc_MNI_scaled_bold.nii.gz


### Perform nuisance regressions
3dcalc -a ${WD}/T1w_brain_pve_0.nii.gz -expr 'equals(a,1)' -prefix ${WD}/CSF.nii.gz
3dcalc -a ${WD}/T1w_brain_pve_2.nii.gz -expr 'equals(a,1)' -prefix ${WD}/WM.nii.gz

3dresample -master ${WD}/sub-20200212TEST_task-MB3_run-001_mc_MNI_scaled_bold.nii.gz \
    -inset ${WD}/WM.nii.gz -prefix ${WD}/WM_rs.nii.gz
3dresample -master ${WD}/sub-20200212TEST_task-MB3_run-001_mc_MNI_scaled_bold.nii.gz \
    -inset ${WD}/CSF.nii.gz -prefix ${WD}/CSF_rs.nii.gz

3dpc -mask ${WD}/WM_rs.nii.gz -pcsave 5 \
    -prefix ${WD}/WM_pc ${WD}/sub-20200212TEST_task-MB3_run-001_mc_MNI_scaled_bold.nii.gz
3dpc -mask ${WD}/CSF_rs.nii.gz -pcsave 5 \
    -prefix ${WD}/CSF_pc ${WD}/sub-20200212TEST_task-MB3_run-001_mc_MNI_scaled_bold.nii.gz

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
-mask
-prefix ${WD}/preproc_output_for_resting-state.nii.gz
