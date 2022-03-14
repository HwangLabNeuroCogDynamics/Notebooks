# example script trying out beta series using lss outputs

import os
import glob2
import natsort
import thalpy
import thalhi
import numpy as np
import nilearn as ni
import matplotlib.pyplot as plt
import nibabel as nib
from nilearn import image, plotting, input_data
from thalhi import decoding
from thalhi.decoding import SubjectLssTentData 
from thalpy import masks
#note the thalhi and thalpy are code Evan wrote.


def generate_correlation_mat(x, y):
	"""Correlate each N with each M.

	Parameters
	----------
	x : np.array
	  Shape N X T. N number of regions by T timepoints

	y : np.array
	  Shape M X T. M number of regions by T timepoints

	Returns
	-------
	np.array
	  N X M array in which each element is a correlation coefficient.

	"""
	mu_x = x.mean(1)
	mu_y = y.mean(1)
	n = x.shape[1]
	if n != y.shape[1]:
		raise ValueError('x and y must ' +
						 'have the same number of timepoints.')
	s_x = x.std(1, ddof=n - 1)
	s_y = y.std(1, ddof=n - 1)
	cov = np.dot(x,
				 y.T) - n * np.dot(mu_x[:, np.newaxis],
								  mu_y[np.newaxis, :])
	return cov / np.dot(s_x[:, np.newaxis], s_y[np.newaxis, :])

def create_mask(new_nii):
    '''make non zero voxels a mask'''
    mask = new_nii.get_fdata()!=0
    mask_nii = ni.image.new_img_like(new_nii, mask)
    return mask_nii

subs = ['10002']
for sub in subs:
    data_dir = f'/mnt/nfs/lss/lss_kahwang_hpc/data/ThalHi/3dDeconvolve/sub-{sub}'

    #load the lss output
    data = decoding.SubjectLssTentData.load(f'{data_dir}/LSS_TENT.p') #this is the object that Evan wrote for storing LSS outputs

    #average across tents. By default each tent from 3dDeconvolve will be a separate datapoint, here we consolidate them.
    mean_data = data.avg_tent_matrix()
    print(mean_data.shape) # always check the shape

    ## Here we are going to load a template nifti object so we can turn the tent outputs into nifti objects too.
    template = nib.load(f'/data/backed_up/shared/ThalHi_MRI_2020/3dDeconvolve/sub-{sub}/sub-{sub}_dcb_FIR_MNI.nii.gz')
    new_nii = ni.image.new_img_like(template, mean_data) #here the header is from the nifti templaet, make sure they have the same geometry.
    
    #ROI mask. Here we are loading the "seed" ROI to do thalamocortical FC. Functional connectivity between thalamus and cortex
    morel_path = '/data/backed_up/shared/ROIs/Morel_2.5.nii.gz'
    mask = image.load_img(morel_path)
   #plotting.plot_roi(mask, title = "Thalamus Morel Atlas")
   #plt.show()

    #Extract timeseries data from thalamus mask
    masker = input_data.NiftiLabelsMasker(mask, verbose = 0)
    thalamus_time_series = masker.fit_transform(new_nii)
    print(thalamus_time_series.shape) #double check the shape, it should be timepoints by number of rois in thalamus. 

    #Extract timeseries from the whole brain nii object
    brain_masker = input_data.NiftiMasker()
    brain_time_series = brain_masker.fit_transform(new_nii) #this operation will output all non zero voxels, so masking the whole brain image itself
    print(brain_time_series.shape) #double check the shape, it should be timepoints by number of voxels in the whole brain image. 

    #functional connectivity Analysis. Now we use the generate_correlation_mat function to generate thalamus by whole brain FC matrix:
    FC = generate_correlation_mat(thalamus_time_series.T, brain_time_series.T)  #notice here we transposed the matrix because the function expect time to be the 2nd dimension.
    print(FC.shape) #here the output FC matrix is thalamus ROI by whole brain voxels.
    
    #here we look at the whole-brain FC with the "first" thalamus R0I
    FC_voxels = FC[0,:] # select the first thalamus ROI , idx 0
    nii_mask = create_mask(ni.image.index_img(new_nii, 1)) # here we are using two functions to create a mask to "unmask" the FC values. An index function to cut the original 4D image to 3D, and a create_mask function to create a mask using non zero voxels
    FC_nii = ni.masking.unmask(FC_voxels, nii_mask) # this is perhaps the most useful nilearn function of all time. https://nilearn.github.io/modules/generated/nilearn.masking.unmask.html

    #we can use nilearn plotting to plot the FC.
    plotting.plot_stat_map(FC_nii)
    # but it is easier to save to file and use AFNI to look through it
    filename = f'/mnt/nfs/lss/lss_kahwang_hpc/data/ThalHi/3dDeconvolve/sub-{sub}_FC_firsThalamustROI.nii.gz'
    FC_nii.to_filename('test.nii.gz')




