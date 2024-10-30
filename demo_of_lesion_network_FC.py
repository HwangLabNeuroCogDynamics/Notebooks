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






