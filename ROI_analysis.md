We often want to extract or summarize values in a functional region. To do that, we will need to have a "mask" that marks the location of voxels within the functional region you are interested in, then we "apply the mask" to the functional data that you want to study. The functional data can be a statistical output from 3dDeconvovle, or estimates of functional connectivity.

Here is an example of using AFNI's 3dROIstats.

First you need to have a "mask" nifti file ready. This mask file contains the regions of interests (ROI), by indexing voxel values within the ROI(s) with different integer numbers, and voxels outside the ROI as zero. For example here is a file that we can use.

    3dinfo /data/backed_up/shared/ROIs/Morel_2.5.nii.gz

    Number of values stored at each pixel = 1
    -- At sub-brick #0 '?' datum type is short:            0 to            17

Also try to use afni to visulize this data.

You will see that this file contains voxel values of 0 to 17. Each of these voxel values indicate a different thalamic nucleus: #1:AN #2:VM #3:VL #4:MGN #5:MD #6:PuA #7:LP #8:IL #9:VA #10:Po #11:LGN #12:PuM #13:PuI #14:PuL #17:VP
So if a voxel has an integer values of "5", that means that voxel belongs to the mediodorsal (MD) nucleus. If a voxel has a value of 12, then it is a part of the medial puvlinar (PuM).

We can use several AFNI programs to summarize these ROIs. For example for the thalhi task, we have several contrasts of interest: EDS v IDS, IDS v Stay. What if we want to know the activation of these task contrasts within each thalamus nucleus?

First we need to know where to find the beta estimates for these task contrasts. We will use subject 10006 as an example:

    3dinfo /data/backed_up/shared/ThalHi_MRI_2020/3dDeconvolve/sub-10006/sub-10006_FIRmodel_MNI_stats+tlrc

    Number of values stored at each pixel = 23
    -- At sub-brick #0 'Full_R^2' datum type is float:            0 to      0.329583
       statcode = fibt;  statpar = 13.5 104.5
    -- At sub-brick #1 'Full_Fstat' datum type is float:            0 to       3.80541
       statcode = fift;  statpar = 27 209
    -- At sub-brick #2 'EDS_GLT#0_Coef' datum type is float:      -3872.1 to       2934.78
    -- At sub-brick #3 'EDS_GLT#0_Tstat' datum type is float:     -6.18941 to       5.60169
       statcode = fitt;  statpar = 209
    -- At sub-brick #4 'EDS_GLT_R^2' datum type is float:            0 to      0.154903
       statcode = fibt;  statpar = 0.5 104.5
    -- At sub-brick #5 'IDS_GLT#0_Coef' datum type is float:     -3687.16 to        3343.2
    -- At sub-brick #6 'IDS_GLT#0_Tstat' datum type is float:     -6.05399 to       6.02688
       statcode = fitt;  statpar = 209
    -- At sub-brick #7 'IDS_GLT_R^2' datum type is float:            0 to      0.149199
       statcode = fibt;  statpar = 0.5 104.5
    -- At sub-brick #8 'Stay_GLT#0_Coef' datum type is float:     -2872.68 to       2565.09
    -- At sub-brick #9 'Stay_GLT#0_Tstat' datum type is float:      -7.6188 to       6.37883
       statcode = fitt;  statpar = 209
    -- At sub-brick #10 'Stay_GLT_R^2' datum type is float:            0 to      0.217364
       statcode = fibt;  statpar = 0.5 104.5
    -- At sub-brick #11 'EDS-IDS_GLT#0_Coef' datum type is float:     -5231.44 to       5010.65
    -- At sub-brick #12 'EDS-IDS_GLT#0_Tstat' datum type is float:     -6.58897 to       6.73645
       statcode = fitt;  statpar = 209
    -- At sub-brick #13 'EDS-IDS_GLT_R^2' datum type is float:            0 to      0.178394
       statcode = fibt;  statpar = 0.5 104.5
    -- At sub-brick #14 'IDS-Stay_GLT#0_Coef' datum type is float:     -2552.54 to       2476.37
    -- At sub-brick #15 'IDS-Stay_GLT#0_Tstat' datum type is float:     -5.54061 to       6.48777
       statcode = fitt;  statpar = 209
    -- At sub-brick #16 'IDS-Stay_GLT_R^2' datum type is float:            0 to      0.167633
       statcode = fibt;  statpar = 0.5 104.5
    -- At sub-brick #17 'All_GLT#0_Coef' datum type is float:     -8158.31 to       6249.33
    -- At sub-brick #18 'All_GLT#0_Tstat' datum type is float:     -7.27205 to       5.44494
       statcode = fitt;  statpar = 209
    -- At sub-brick #19 'All_GLT_R^2' datum type is float:            0 to      0.201933
       statcode = fibt;  statpar = 0.5 104.5
    -- At sub-brick #20 'Switch_GLT#0_Coef' datum type is float:     -3569.25 to       3513.12
    -- At sub-brick #21 'Switch_GLT#0_Tstat' datum type is float:      -5.4698 to       5.41474
       statcode = fitt;  statpar = 209
    -- At sub-brick #22 'Switch_GLT_R^2' datum type is float:            0 to      0.125225
       statcode = fibt;  statpar = 0.5 104.5

Here we can see sub-brick #11 and #14 are the beta estimates for the task contrasts we are interested. Then we can use 3dROIstats to get the mean beta estimates within each thalamus nucleus. Also see: https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dROIstats.html

    3dROIstats -mask /data/backed_up/shared/ROIs/Morel_2.5.nii.gz /data/backed_up/shared/ThalHi_MRI_2020/3dDeconvolve/sub-10006/sub-10006_FIRmodel_MNI_stats+tlrc > stats_10006.txt

And if we open up the resulting output stats_10006.txt

    cat stats_10006.txt


It is a text file where each column is a different ROI, and each row is a different sub-brik in sub-10006_FIRmodel_MNI_stats+tlrc. We will be looking for the values for sub-brik #11 and #14.

Alternatively, you can restrict the input to 3dROIstats by using "[]" to select sub-briks:

    3dROIstats -mask /data/backed_up/shared/ROIs/Morel_2.5.nii.gz /data/backed_up/shared/ThalHi_MRI_2020/3dDeconvolve/sub-10006/sub-10006_FIRmodel_MNI_stats+tlrc[11]

    File	Sub-brick	Mean_1  	Mean_2  	Mean_3  	Mean_4  	Mean_5  	Mean_6  	Mean_7  	Mean_8  	Mean_9  	Mean_10  	Mean_11  	Mean_12  	Mean_13  	Mean_14  	Mean_17  
    /data/backed_up/shared/ThalHi_MRI_2020/3dDeconvolve/sub-10006/sub-10006_FIRmodel_MNI_stats+tlrc[11]	0[EDS-IDS_G]	28.326362	46.336259	13.789012	-20.490505	55.040666	-5.007179	14.755374	27.626903	44.884624	-20.879833	3.707921	21.475616	-34.610061	51.587974	18.109154

From this output, we know the average beta estimate for contrast EDS-IDS, within the first ROI (Mean_1), the AN nucleus, is 28.32. For the second ROI (Mean_2), the VM nucleus, it is 46.33 You can repeat this process for every other subject, to summarize the activation for different thalamic nuclei for different task contrasts.

Another program that you can use is 3dmaskave. If you are familiar with bash scripting and piping outputs, you can try to write a script to go through each subjects and compile the ROI values for further analysis.

End of notebook.
