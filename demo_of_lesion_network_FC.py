## here is a short example of how to do lesion network analysis. Using a lesion mask as "seed", and map its connectiity pattern across the whole brain.
# some examples:
# Boes, A. D., Prasad, S., Liu, H., Liu, Q., Pascual-Leone, A., Caviness Jr, V. S., & Fox, M. D. (2015). Network localization of neurological symptoms from focal brain lesions. Brain, 138(10), 3061-3075.
# Hwang, K., Bruss, J., Tranel, D., & Boes, A. D. (2020). Network localization of executive function deficits in patients with focal thalamic lesions. Journal of cognitive neuroscience, 32(12), 2303-2319.

import numpy as np
import pandas as pd
import glob
import nilearn
import nibabel as nib
from nilearn.maskers import NiftiLabelsMasker, NiftiMasker
from nilearn.masking import compute_epi_mask
from joblib import Parallel, delayed
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
from nilearn.plotting import plot_stat_map


## Data for calculating FC.
# Here we use the MGH restings state files. They are already preprocessed using proecdures describe in the Hwang paper.

rest_files = glob.glob("/data/backed_up/shared/MGH/MGH/*/MNINonLinear/*rfMRI_REST_ncsreg.nii.gz")
num_of_subjects = len(rest_files)
print(num_of_subjects)

# load the lesion mask as seed. For now just doing one, you would have to modify this script to do other lesions.
lesion_mask = nib.load("/data/backed_up/shared/OneTree/Lesions/2662.nii.gz")
# create a "masker" to extract timeseries. Study the nilearn website if you want to learn more about this function (https://nilearn.github.io/dev/modules/generated/nilearn.maskers.NiftiMasker.html)
# note there are many different types of maskers. Here we are just using one type for a single lesion mask
lesion_masker = NiftiLabelsMasker(lesion_mask)
lesion_id = '2662'

# now read in each subject's rest data, and apply the masker to extract the time series
for i, f in enumerate(rest_files):
    rest_file = nib.load(f)
    seed_time_series = lesion_masker.fit_transform(rest_file)
    print(seed_time_series.shape)

    # now extract signal from the whhole brain.
    nii_data = rest_file.get_fdata()
    # Extract the first TR (index 0 along the time dimension)
    first_tr_data = nii_data[..., 0]
    first_tr_data = first_tr_data!=0 #all none zero data points

    # Create a new 3D mask image for the first TR
    brain_mask = nib.Nifti1Image(first_tr_data, affine=rest_file.affine, header=rest_file.header)
    brain_masker = NiftiMasker(brain_mask)
    
    brain_time_series = brain_masker.fit_transform(rest_file)
    print(brain_time_series.shape) ## there are 30k voxels!
    
    #now compute fc map
    def fc_calc(r):
        fc = np.corrcoef(seed_time_series[:, 0], brain_time_series[:, r])[0, 1]
        return fc

    fc_map = Parallel(n_jobs=24)(delayed(fc_calc)(r) for r in range(brain_time_series.shape[1]))
    fc_map = np.array(fc_map)
    print(fc_map.shape) #it should have the same number of whole brain voxels
    
    fc_map_img = brain_masker.inverse_transform(fc_map.T) ### this is to put it back into nii space
    fc_map_img.to_filename("/data/backed_up/shared/OneTree/lesion_network_mapping/%s_id_%s.nii.gz" %(lesion_id, i)) #save to disk for later use

    ## we can briefly visualize it
    #plot_stat_map(fc_map_img, display_mode="z", threshold=0.3, title="Seed-based Connectivity")



#### after you are done with caluclating FC maps from individual subjects, we can a do group level t stats
lesion_id = '2662' #do one lesion mask at a time
maps = glob.glob("/data/backed_up/shared/ThalHi_EEG/stats/lesion_network_mapping/%s_*.nii.gz" %lesion_id) #list all the fc maps

# this is the MNI mask where we will use to extract all the FC values from each map
mni_mask = nib.load("/data/backed_up/shared/ROIs/mni_brain_mask_2mm.nii.gz")
brain_masker = NiftiMasker(mni_mask)

fc_values = []
for m in maps:
    fc = brain_masker.fit_transform(m)
    print(fc.shape) # this is the number of voxels inside the MNI mask
    fc_values.append(fc[0,:]) 
fc_values = np.array(fc_values) #this will concatenate all the voxel-wise fc values into one numpy array
print(fc_values.shape)    #the end result is subject by # of voxels

## now we do a t test for each voxel
def fc_test(fc):
    from scipy import stats
    t, p = stats.ttest_1samp(fc, 0) #ttest against zero
    return t

# Apply fc_test function in parallel across the second dimension (i.e., voxels) of fc_values
t_stats = Parallel(n_jobs=12)(delayed(fc_test)(fc_values[:, i]) for i in range(fc_values.shape[1]))
t_stats = np.array(t_stats)
print(t_stats.shape) #make sure the size matches the number of voxels

# now put the t stat back to MNI space to save and for visualization
t_stat_img = brain_masker.inverse_transform(t_stats)
t_stat_img.to_filename("/data/backed_up/shared/ThalHi_EEG/stats/t_stats_%s.nii.gz" %lesion_id) #save it to file

#you can use this to plot it if you like
#plot_stat_map(t_stat_img, display_mode="z", threshold=10, title="Group level Seed-based Connectivity for lesion %s" %lesion_id)

