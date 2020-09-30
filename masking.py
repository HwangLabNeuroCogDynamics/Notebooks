import numpy as np
import nibabel as nib
from scipy.stats import rankdata
import nilearn
from nilearn import plotting, input_data
import matplotlib.pyplot as plt

group_ffa_mask = nib.load('/data/backed_up/shared/xitchen_WM/stats/FFA_cluster1.nii.gz')
group_ffa_mask_data = group_ffa_mask.get_data()
indiv_ffa_ttest = nib.load('/data/backed_up/shared/xitchen_WM/results/100307/100307_FIRmodel_MNI_stats_GS_REML.nii')

#In [30]: indiv_ffa_ttest.shape
#Out[30]: (91, 109, 91, 1, 59)
#-- At sub-brick #30 'faces-others#0_Tstat' datum type is float:     -5.72194 to       6.35074
# need to select brik#30.
# Note, indiv_ffa_ttest is a 5d image according to nilearn, so we can't use its image module which only works on 4d image.
# This wont work: nilearn.image.index_img(indiv_ffa_ttest, 30)
# So had to do this:
indiv_ffa_ttest_data = np.squeeze(indiv_ffa_ttest.get_data()[:,:,:,:,30])

# use the group ffa mask to mask the invidual face v other t test results:
#nilearn.masking.apply_mask(imgs, mask_img,
indiv_ffa_ttest_masked = indiv_ffa_ttest_data * (group_ffa_mask_data!=0)
indiv_ffa_group_masked_img = nib.nifti2.Nifti1Image(dataobj = indiv_ffa_ttest_masked,
    header=group_ffa_mask.header, affine=group_ffa_mask.affine)

#check and see it is at the right place.
plotting.plot_glass_brain(indiv_ffa_group_masked_img)
plt.show()

#this indiv_ffa_img is this individual's facs_v_other tstats within the group FFA mask
# now search for the top 100 voxels within the image, show them.
# I picked the number 100  arbitrarily
masker = nilearn.input_data.NiftiMasker()
indiv_ffa_voxels = masker.fit_transform(indiv_ffa_group_masked_img)
# rank the t values, keep those in the top 100
indiv_top100 = (np.shape(indiv_ffa_voxels)[1] - rankdata(indiv_ffa_voxels))<100
indiv_ffa = masker.inverse_transform(indiv_top100)
plotting.plot_glass_brain(indiv_ffa)
plt.show()

# you can save the results
nib.save(indiv_ffa, '100307_ffa_top100vox.nii')
