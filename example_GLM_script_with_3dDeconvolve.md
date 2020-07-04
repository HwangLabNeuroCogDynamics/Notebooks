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
The main tool we use to do GLM is 3dDeconvolve.
Below is an example 3dDeconvolve script analyzing our practice dataset.
Here we will analyze subject 20190516, we will first have to find where the preprocessed files are. You should be able to find all the files in this data folder:

    data='/data/backed_up/shared/fMRI_Practice/fMRIprep/fmriprep/sub-20190516/func'
    cd $data
    ls

In it you will see all the preprocessed BOLD data, from run 1 to run 5. For each run, there is a ""-confounds_regressors.tsv" that contains the nuisance regressors, such as head motion estimates that we would need to prepare before entering it into 3dDeconvolve.

fMRIprep generates all kinds of nuisance data, where each column in this tsv is a different regressor. But we typically only include  wm, csf, and motion estimates. So we need to "cut" the data and only keep the ones we want. The second annoying thing is we need to remove the first line of column header from the file, since 3dDeconvolve can only take numbers as inputs. So we will need to write a small script to deal with this.


    outputpath='/data/backed_up/shared/fMRI_Practice/Deconvolve_practice'
    data='/data/backed_up/shared/fMRI_Practice/fMRIprep/fmriprep/sub-20190516/func'
    echo -n $outputpath/all_nuisance.1D

    for run in 1 2 3 4 5; do
      cat ${data}/sub-20190516_task-MB3_run-00${run}_desc-confounds_regressors.tsv | tail -n+2 >> $outputpath/all_nuisance.1D
    done

    cat $outputpath/all_nuisance.1D | cut -f23-28,203,207,211,215,219,223  > $outputpath/nuisance.1D

    3dDeconvolve -input $(ls ${data}/sub-20190516_task-MB3_run-*_space-MNI152NLin2009cAsym_desc-preproc_bold*.nii.gz | sort -V) \
    -mask ${data}/sub-20190516_task-MB3_run-004_space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz \
    -polort A \
    -num_stimts 3 \
    -stim_times 1 /data/backed_up/shared/fMRI_Practice/ScanLogs/110_MB3_EDS_stimtime.1D.txt 'CSPLIN(0, 13.6, 9)' -stim_label 1 EDS \
    -stim_times 2 /data/backed_up/shared/fMRI_Practice/ScanLogs/110_MB3_IDS_stimtime.1D.txt 'CSPLIN(0, 13.6, 9)' -stim_label 2 IDS \
    -stim_times 3 /data/backed_up/shared/fMRI_Practice/ScanLogs/110_MB3_Stay_stimtime.1D.txt 'CSPLIN(0, 13.6, 9)' -stim_label 3 Stay \
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
