# FC analysis with nilearn
This is an example of how to use nilearn and nibabel to load preprocessed nitfi files, and do functional connectivity analysis.

nilearn and nibabel are both very well documented. So spend some time going throuhgh its documentations would be very helpful:
https://nipy.org/nibabel/ \
https://nilearn.github.io/user_guide.html

If you don't have nibabel and nilearn installed, do:

    pip3 install --user nibabel nilearn
pip3 means it will install for python3 env, --user means it will be in your home. Note that on most systems we don't have the permission to do system wide installation.


Then get into ipython and try:

    import nilearn as ni
    import nibabel as nib


To understand how nilearn and nibabel load and manipulate data, See
https://nilearn.github.io/auto_examples/plot_3d_and_4d_niimg.html#sphx-glr-auto-examples-plot-3d-and-4d-niimg-py
http://nilearn.github.io/manipulating_images/input_output.html

Let us load an example HCP subject from Xitong's project:

    nii = nib.load('tfMRI_WM_LR.nii.gz')
    nii                                                                        
    Out[36]: <nibabel.nifti1.Nifti1Image at 0x7fc408e47d68>

    nii.shape
    (91, 109, 91, 405)

The first three numbers are x, y, z grids of the data. The last dimension is number of TRs.
You will notice this matches the output from 3dinfo. It is extremely important you understand the dimension and the resolution of the data.


Let us now visualize the first TR. We will use nilearn to load the data this time.

    from nilearn import image
    nii = image.load_img('tfMRI_WM_LR.nii.gz')
    nii
    Out[39]: <nibabel.nifti1.Nifti1Image at 0x7fc408d346a0>

    first_vol = image.index_img(nii, 0)
    print(first_vol.shape)
    (91, 109, 91)

    from nilearn import plotting
    import matplotlib.pyplot as plt
    plotting.plot_stat_map(first_vol)

To understand all the other plotting capabilities of nilearn, see:
https://nilearn.github.io/plotting/index.html
https://nilearn.github.io/auto_examples/plot_nilearn_101.html#sphx-glr-auto-examples-plot-nilearn-101-py
https://nilearn.github.io/auto_examples/plot_3d_and_4d_niimg.html#sphx-glr-auto-examples-plot-3d-and-4d-niimg-py


Now let us put a region of interest mask over our data. We will load a thalamus mask with different integer values:

    Morel_path = '/data/backed_up/shared/ROIs/Thalamus_Morel_consolidated_mask_v3.nii.gz'
    thalamus_mask = image.load_img(Morel_path)
    thalamus_mask.shape
    Out[57]: (91, 109, 91)
    plotting.plot_roi(thalamus_mask, title="Thalamus Morel atlas")
    plt.show()

It is extremely important to check and make sure the geometry of the mask and your functional data are consistent.
Read this carefully:
https://nipy.org/nibabel/coordinate_systems.html



Now let us extract data from this mask. Examples can be found Here
https://nilearn.github.io/auto_examples/03_connectivity/plot_seed_to_voxel_correlation.html


    from nilearn import input_data

    masker = input_data.NiftiLabelsMasker(
    thalamus_mask, verbose=0)

    time_series = masker.fit_transform(nii)
    time_series.shape
    Out[79]: (405, 15)

This extraction procedure will return a numpy array of 405 x 15 405 is the number of TRs, 15 is the number of ROIs in the mask. Essentially, each mask ROI will have one vector of functional data. How do you know which row corresponds to which ROI? you will have to do the record booking and checking yourself.

    data = thalamus_mask.get_data()
    np.unique(data)
    Out[78]: array([ 0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 17],
      dtype=int16)
    #see https://github.com/kaihwang/LesionNetwork for the coding of these integers


Now let us "flatten" the whole-brain functional data into a two dimensional array

    brain_masker = input_data.NiftiMasker()
    brain_time_series = brain_masker.fit_transform(nii)


Now let us do the correlation (functional connectivity analysis):

    import numpy as np

    seed_to_voxel_correlations = np.zeros((np.shape(brain_time_series)[1],1))

    #someone better at matrix algebra can probably speed this up
    for r in np.arange(np.shape(brain_time_series)[1]):
      seed_to_voxel_correlations[r,0] = np.corrcoef(brain_time_series[:,r],time_series[:,5])[0,1]


    from nilearn import plotting

    seed_to_voxel_correlations_img = brain_masker.inverse_transform(
        seed_to_voxel_correlations.T)
    display = plotting.plot_stat_map(seed_to_voxel_correlations_img,
                                     threshold=0.1, vmax=0.5,
                                     title="Seed-to-voxel correlation"
                                     )

You can the extract the data object from the resulting correlation image and do all kinds of masking operations

    seed_to_voxel_correlations_img.get_data().shape


Spend some time going through both nilearn and nibabel's online documentation. it has lots of masking, inputing and outputing functions that could come in handy.
https://nilearn.github.io/user_guide.html
