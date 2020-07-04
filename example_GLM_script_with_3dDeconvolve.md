## Example of running GLM analysis using AFNI's 3dDeconvolve

### Before you start
You should make sure you have a basic understanding of several basic stats concepts:
- Basic descriptive stats.
  - Mean and variance.
- Hypothesis test
  - t test
  - Simple and multiple regression
  - p value and null hypothesis

If you don't, a good crash course can be found here from ["Mumford Brain Stats"](https://www.youtube.com/c/mumfordbrainstats/videos):
- [Basic terminology](https://youtu.be/apt8uAgtgdY)
- [Regression](https://www.youtube.com/watch?v=yLgPpmXVVbs)
- [Multiple Regression](https://www.youtube.com/watch?v=qdOG7YMolmA)
- [Hypothesis test](https://www.youtube.com/watch?v=ULeg3DH3g9w)
- [Regression parameters](https://www.youtube.com/watch?v=uClfe4pLrCo)

Then, you should finish these two coursera videos on general linear model (GLM). These two videos will give you an overall conceptual understanding:
- [Part 1](https://www.youtube.com/watch?v=GDkLQuV4he4)
- [Part 2](https://www.youtube.com/watch?v=OyLKMb9FNhg&t=18s)
- [part 3](https://www.youtube.com/watch?v=7MibM1ATai4&feature=emb_title)
- [part 4](https://www.youtube.com/watch?v=YfeMIcDWwko)
- [part 5](https://www.youtube.com/watch?v=DEtwsFdFwYc)
- [part 6](https://www.youtube.com/watch?v=NRunOo7EKD8)


We will be using AFNI's [3dDeconvolve](https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dDeconvolve.html) to perform GLM analysis. It is a versatile, powerful tool, but with a bit of a learning curve. AFNI bootcamp has a series of excellent [youtube videos](https://www.youtube.com/watch?v=iZ7ci1Pw-_o&list=PL_CD549H9kgpLv7qW0cP03S-JBPHscg9i) that you should watch.

JB Poline and Matthew Brett wrote an [excellent review](https://www.sciencedirect.com/science/article/pii/S1053811912001607?casa_token=-gnykR5VTScAAAAA:5LmVepVWvvoG-Pphkx8A4Wz1uzZUrNwF_g2TDMIMjU2FMYycPTbIdpC_-uk36hyTyv49543lag) on GLM for fMRI that would be very useful to go over as well.

It is probably more productive to go back and forth between these materials and your own analyses as you work through your project. fMRI is hard, and I find it useful to periodically revisit these concepts.

## How 3dDeconvolve works
The main tool we use to do GLM is [3dDeconvolve](https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dDeconvolve.html).
Below is an example 3dDeconvolve script analyzing our practice dataset. <br>

In this dataset, the subjects performed a set-switching task with three conditions: switch between task sets (EDS switch), switch between task-rules within a task set (IDS switch), and repeat trials. This is an event related design, so the timing of each of these trials were randomized. One of the main goals (but not the only one) of doing GLM with 3dDeconvolve is to identify brain regions showing BOLD activity modulated by these conditions. <br>

Here we have an example script to analyze data subject 20190516. Note that this subject was succesfully preprocessed using fMRI prep. We will first have to find where the preprocessed files are. You should be able to find all the files in this data folder:

    data='/data/backed_up/shared/fMRI_Practice/fMRIprep/fmriprep/sub-20190516/func'
    cd $data
    ls

In it you will see all the preprocessed BOLD data, from run 1 to run 5. Typically, we use the version of preprocessed files in MNI space. Those are:

    $ ls -lh ${data}/sub-20190516_task-MB3_run-00*MNI152NLin2009cAsym_desc-preproc_bold.nii.gz
    sub-20190516_task-MB3_run-001_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz  sub-20190516_task-MB3_run-004_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz
    sub-20190516_task-MB3_run-002_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz  sub-20190516_task-MB3_run-005_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz
    sub-20190516_task-MB3_run-003_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz

For each run, there is a ""-confounds_regressors.tsv" that contains the nuisance regressors, such as head motion estimates that we would need to prepare before entering it into 3dDeconvolve.

    $ ls -lh ${data}/sub-20190516_task-MB3_run*desc-confounds*regressors.tsv
    -rw-r--r-- 2 cjhollis hwang-group 764K Jul  2 14:07 /data/backed_up/shared/fMRI_Practice/fMRIprep/fmriprep/sub-20190516/func/sub-20190516_task-MB3_run-001_desc-confounds_regressors.tsv
    -rw-r--r-- 2 cjhollis hwang-group 744K Jul  2 14:06 /data/backed_up/shared/fMRI_Practice/fMRIprep/fmriprep/sub-20190516/func/sub-20190516_task-MB3_run-002_desc-confounds_regressors.tsv
    -rw-r--r-- 2 cjhollis hwang-group 748K Jul  2 14:06 /data/backed_up/shared/fMRI_Practice/fMRIprep/fmriprep/sub-20190516/func/sub-20190516_task-MB3_run-003_desc-confounds_regressors.tsv
    -rw-r--r-- 2 cjhollis hwang-group 739K Jul  2 14:06 /data/backed_up/shared/fMRI_Practice/fMRIprep/fmriprep/sub-20190516/func/sub-20190516_task-MB3_run-004_desc-confounds_regressors.tsv
    -rw-r--r-- 2 cjhollis hwang-group 794K Jul  2 14:06 /data/backed_up/shared/fMRI_Practice/fMRIprep/fmriprep/sub-20190516/func/sub-20190516_task-MB3_run-005_desc-confounds_regressors.tsv

Here "tsv" stands for tab delineated file, like a csv. fMRIprep generates all kinds of nuisance data stored in these files, where each column in this file is a different regressor. But we typically only include  wm, csf, and motion estimates into our GLM model. So we need to "cut" the data and only keep the ones we want. The second annoying thing is we need to remove the first line of column header from the file, since 3dDeconvolve can only take numbers as inputs. So we will need to write a small script to deal with this.


    outputpath='/data/backed_up/shared/fMRI_Practice/Deconvolve_practice'
    data='/data/backed_up/shared/fMRI_Practice/fMRIprep/fmriprep/sub-20190516/func'

    #this will create an empty file
    echo -n $outputpath/all_nuisance.1D

    for run in 1 2 3 4 5; do
      # pipe everything after the first line into the empty file we just created
      cat ${data}/sub-20190516_task-MB3_run-00${run}_desc-confounds_regressors.tsv | tail -n+2 >> $outputpath/all_nuisance.1D
      # beware of the difference between ">" and ">>"

    done

    cat $outputpath/all_nuisance.1D | cut -f23-28,203,207,211,215,219,223  > $outputpath/nuisance.1D

In the above example we concatenated all the nuisance regressors from the 5 runs, while removing the first header line. Then we use the unix cut function to cut out the columns we need. each of the number after the -f option indicates the number of column you want to select. Here we select 5 components from the acompcor, and the 6 rigid body motion regressors. Be very careful that you are selecting the right column variables. The end product nuisance.1D is the file we will feed into 3dDeconvolve for nuisance regression.

The other input required is the task timing. 3dDedonvolve needs to know when did the EDS, IDS, Stay trials occured. Those will be documented in the following trials, each condition requires its own file:

    /data/backed_up/shared/fMRI_Practice/ScanLogs/110_MB3_EDS_stimtime.1D.txt
    /data/backed_up/shared/fMRI_Practice/ScanLogs/110_MB3_IDS_stimtime.1D.txt
    /data/backed_up/shared/fMRI_Practice/ScanLogs/110_MB3_Stay_stimtime.1D.txt

These timings files were created by extracting timestamp logs from our PsychoPy program. The format of these timing files for AFNI is as follows: One line per run; in each line/run, stimulus onset in seconds since the beginning of the run (known as local times). So if you see a file like:

    1.3 3.7 4.5
    2.4 5.6
    *

That means this particular condition occurred at 1.3, 3.7, and 4.5 seconds since the start of run 1. For run 2 it occurred at 2.4 and 5.6 seconds since the start. For run 3, * denotes no trials for this condition in run 3. For more information please see this [page](https://afni.nimh.nih.gov/pub/dist/doc/misc/Decon/DeconSummer2004.html). Note that we typically use local times, which can be specified by the -local_times flag.

Now that we have the inputs ready, below is the complete 3dDeconvolve script:


    outputpath='/data/backed_up/shared/fMRI_Practice/Deconvolve_practice'
    data='/data/backed_up/shared/fMRI_Practice/fMRIprep/fmriprep/sub-20190516/func'

    3dDeconvolve -input $(ls ${data}/sub-20190516_task-MB3_run-*space-MNI152NLin2009cAsym_desc-preproc_bold*.nii.gz | sort -V) \
    -mask ${data}/sub-20190516_task-MB3_run-004_space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz \
    -polort A \
    -ortvec ${outputpath}/nuisance.1D \
    -local_times \
    -num_stimts 3 \
    -stim_times 1 /data/backed_up/shared/fMRI_Practice/ScanLogs/110_MB3_EDS_stimtime.1D.txt 'TENT(0, 13.6, 9)' -stim_label 1 EDS \
    -stim_times 2 /data/backed_up/shared/fMRI_Practice/ScanLogs/110_MB3_IDS_stimtime.1D.txt 'TENT(0, 13.6, 9)' -stim_label 2 IDS \
    -stim_times 3 /data/backed_up/shared/fMRI_Practice/ScanLogs/110_MB3_Stay_stimtime.1D.txt 'TENT(0, 13.6, 9)' -stim_label 3 Stay \
    -iresp 1 ${outputpath}/sub-20190516_EDS_FIR_MNI.nii.gz \
    -iresp 2 ${outputpath}/sub-20190516_IDS_FIR_MNI.nii.gz \
    -iresp 3 ${outputpath}/sub-20190516_Stay_FIR_MNI.nii.gz \
    -num_glt 7 \
    -gltsym 'SYM: +1*EDS' -glt_label 1 EDS \
    -gltsym 'SYM: +1*EDS' -glt_label 2 IDS \
    -gltsym 'SYM: +1*EDS' -glt_label 3 Stay \
    -gltsym 'SYM: +1*EDS - 1*IDS' -glt_label 4 EDS-IDS \
    -gltsym 'SYM: +1*IDS - 1*Stay' -glt_label 5 IDS-Stay \
    -gltsym 'SYM: +1*EDS + 1*IDS + 1*Stay' -glt_label 6 All \
    -gltsym 'SYM: +1*EDS + 1*IDS - 2*Stay' -glt_label 7 Switch \
    -rout \
    -tout \
    -bucket ${outputpath}/sub-20190516_FIRmodel_MNI_stats \
    -errts ${outputpath}/sub-20190516_FIRmodel_errts.nii.gz \
    -noFDR \
    -nocout \
    -jobs 4 \
    -ok_1D_text

Let us explain each major components of this command call: <br>
The first few lines specified the input:

    3dDeconvolve -input $(ls ${data}/sub-20190516_task-MB3_run-*space-MNI152NLin2009cAsym_desc-preproc_bold*.nii.gz | sort -V) \
    -mask ${data}/sub-20190516_task-MB3_run-004_space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz \

Here the "-input" flag will search for all the runs using the wildcard. The -mask option specifies the spatial extent we will analyze. Here I got a bit lazy and just used the mask fmriprep generated for run 4. You should probably create an union masks for all the runs. As always, [AFNI has a tool just for this purpose](https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dmask_tool.html).

The second part is to setup the baseline model and nuisance regressors

    -polort A \
    -ortvec ${outputpath}/nuisance.1D \

The -polort option will model drifts, and the -ortvec is to model nuisance variables that we extracted above.

The next part specifies the conditions that we want to model:

    -stim_times 1 /data/backed_up/shared/fMRI_Practice/ScanLogs/110_MB3_EDS_stimtime.1D.txt 'TENT(0, 13.6, 9)' -stim_label 1 EDS \
    -stim_times 2 /data/backed_up/shared/fMRI_Practice/ScanLogs/110_MB3_IDS_stimtime.1D.txt 'TENT(0, 13.6, 9)' -stim_label 2 IDS \
    -stim_times 3 /data/backed_up/shared/fMRI_Practice/ScanLogs/110_MB3_Stay_stimtime.1D.txt 'TENT(0, 13.6, 9)' -stim_label 3 Stay \
    -iresp 1 ${outputpath}/sub-20190516_EDS_FIR_MNI.nii.gz \
    -iresp 2 ${outputpath}/sub-20190516_IDS_FIR_MNI.nii.gz \
    -iresp 3 ${outputpath}/sub-20190516_Stay_FIR_MNI.nii.gz \

The stimu_times flag will read in the stimulus timing, and then model using  "TENT" basis function. This is perhaps the most important part of 3dDeconvolve. To understand all the different ways you can model your conditions, see: https://afni.nimh.nih.gov/pub/dist/doc/misc/Decon/2007_0504_basis_funcs.html <br>
We typically use TENT for event related design, and GAM for block design or conditions that we want to assume a HRF shape. TENT is equivalent to the finite impulse function (FIR approach). TENT(0, 13.6, 9) means we are modeling for 0 to 13.6 seconds after the stimulus onset, using 9-1 = 8 tent basis functions. 13.6 / 8 = 1.7, which is the TR of this particular dataset.

The next part is to contrast different conditions and perform hypotheses tests:

    -num_glt 7 \
    -gltsym 'SYM: +1*EDS' -glt_label 1 EDS \
    -gltsym 'SYM: +1*EDS' -glt_label 2 IDS \
    -gltsym 'SYM: +1*EDS' -glt_label 3 Stay \
    -gltsym 'SYM: +1*EDS - 1*IDS' -glt_label 4 EDS-IDS \
    -gltsym 'SYM: +1*IDS - 1*Stay' -glt_label 5 IDS-Stay \
    -gltsym 'SYM: +1*EDS + 1*IDS + 1*Stay' -glt_label 6 All \
    -gltsym 'SYM: +1*EDS + 1*IDS - 2*Stay' -glt_label 7 Switch \

The rest is to specify the output. We are saving the statistics as well as the residual timeseries:

    -rout \
    -tout \
    -bucket ${outputpath}/sub-20190516_FIRmodel_MNI_stats \
    -errts ${outputpath}/sub-20190516_FIRmodel_errts.nii.gz \
    -noFDR \
    -nocout \

3dDeconvolve can be run with multiple threads, here we are using 4 (-jobs 4).

3dDeconvolve will generate many files:

    $ cd $outputpath
    $ ls -l
    total 1363204
    -rw-rw-r-- 1 kahwang hwang-group   3860820 Jul  4 13:47 all_nuisance.1D
    -rw-rw-r-- 1 kahwang hwang-group    175115 Jul  4 13:47 nuisance.1D
    -rw-rw-r-- 1 kahwang hwang-group   4821023 Jul  4 13:38 sub-20190516_EDS_FIR_MNI.nii.gz
    -rw-rw-r-- 1 kahwang hwang-group 623431578 Jul  4 13:39 sub-20190516_FIRmodel_errts.nii.gz
    -rw-rw-r-- 1 kahwang hwang-group      3709 Jul  4 13:48 sub-20190516_FIRmodel_MNI_stats.REML_cmd
    -rw-rw-r-- 1 kahwang hwang-group  57946752 Jul  4 13:38 sub-20190516_FIRmodel_MNI_stats+tlrc.BRIK
    -rw-rw-r-- 1 kahwang hwang-group      7326 Jul  4 13:38 sub-20190516_FIRmodel_MNI_stats+tlrc.HEAD
    -rw-rw-r-- 1 kahwang hwang-group    543552 Jul  4 13:48 sub-20190516_FIRmodel_MNI_stats.xmat.1D
    -rw-rw-r-- 1 kahwang hwang-group   4812657 Jul  4 13:38 sub-20190516_IDS_FIR_MNI.nii.gz
    -rw-rw-r-- 1 kahwang hwang-group   4782752 Jul  4 13:38 sub-20190516_Stay_FIR_MNI.nii.gz


You can look at the design matrix, which is saved in sub-20190516_FIRmodel_MNI_stats.xmat.1D, with the following commands:

    1dgrayplot ${outputpath}/sub-20190516_FIRmodel_MNI_stats.xmat.1D
    ExamineXmat -input ${outputpath}/sub-20190516_FIRmodel_MNI_stats.xmat.1D

The FIR_MNI.nii.gz files are the HRF timecourses for each condition. The statistics output are saved in sub-20190516_FIRmodel_MNI_stats+tlrc

## 3dREMLfit

It is now recommended that also run [3dREMLfit](https://afni.nimh.nih.gov/pub/dist/doc/program_help/3dREMLfit.html) to correct for temporally correlated noise in fMRI data. It won't affect parameter estimate, but does affect the t and f stats calculated. For details see these [slides](https://afni.nimh.nih.gov/pub/dist/doc/misc/3dREMLfit/3dREMLfit.pdf). To run it, you can just execute the command generated by 3dDeconvolve.

    #look at the saved REML command
    cat ${outputpath}/sub-20190516_FIRmodel_MNI_stats.REML_cmd

    #Execute it
    . ${outputpath}/sub-20190516_FIRmodel_MNI_stats.REML_cmd


## Other things to consider

In the above example, we did not "remove" any data points that were likely contaminated by excessive noise. fMRIprep does save the "frame-wise displacement" measure in the nuisance regressor output. AFNI provides a "-censor" option to remove data points.
