import nibabel as nib
from nilearn import image, input_data, masking, plotting
import nilearn.image
import numpy as np
from glob import glob
from scipy import stats, linalg
import multiprocessing
from scipy.stats import zscore
import pandas as pd
import pickle

low_wm=['0bk','0bk_body', '0bk_faces', '0bk_places', '0bk_tools']
high_wm=['2bk','2bk_body', '2bk_faces', '2bk_places', '2bk_tools']

conditions={'0bk':53, '2bk':56, '0bk_body':2, '0bk_faces':5,'0bk_places':8,'0bk_tools':11,
'2bk_body':14, '2bk_faces':17,'2bk_places':20,'2bk_tools':23,
'body_others':26,'faces_others':29,'places_others':32,'tools_others':35}


thalamus_mask=nib.load('/Shared/lss_kahwang_hpc/ROIs/Thalamus_Morel_consolidated_mask_v3.nii.gz')
thalamus_mask_data = thalamus_mask.get_fdata()
thalamus_mask_data = thalamus_mask_data>0
thalamus_masker = image.new_img_like(thalamus_mask, thalamus_mask_data)

cortex_mask=nib.load('/Shared/lss_kahwang_hpc/ROIs/Schaefer2018_400Parcels_17Networks_order_FSLMNI152_2mm.nii.gz')
cortex_masker=input_data.NiftiLabelsMasker(labels_img=cortex_mask, standardize=False)

other_rois=nib.load('/Shared/lss_kahwang_hpc/HCP_data/activity_flow/other_rois/Schaefer100+BG_2mm.nii.gz')
other_rois_data=other_rois.get_fdata()

def save_object(obj, filename):
	''' Simple function to write out objects into a pickle file
	usage: save_object(obj, filename)
	'''
	with open(filename, 'wb') as output:
		pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)
def read_object(filename):
	''' short hand for reading object because I can never remember pickle syntax'''
	o = pickle.load(open(filename, "rb"))
	return o

def run_fc_evoke_corr(inputs):

    ### these inptus will have to be edited, and new variables will have to be created from share memory

    functional_data_shm = shared_memory.SharedMemory(name=inputs[0]) # this is to access the shared memory space that is storing X
    #create the functional data from shared memory
    functional_data =  np.ndarray(inputs[1], buffer=functional_data_shm.buf) #input 1 is the shape of fmat

    cortical_ts_shm = shared_memory.SharedMemory(name=inputs[2])
    cortical_ts =  np.ndarray(inputs[3], buffer=cortical_ts_shm.buf) #input 3 is the shape of cortical ts

    
    # three elements expected in input
    #s = inputs[0] # subject name
    #subcortical_mask = inputs[1]  # subocortical mask
    #cortex_masker = inputs[2] # cortex masker
    ###



    #thalamus_mask = nib.load(rois+'Morel_2.5_mask.nii.gz')
    #cortex_mask = nib.load(rois+'Schaefer400_2.5.nii.gz')
    #cortex_masker = NiftiLabelsMasker(labels_img=cortex_mask, standardize=False)

    subcortical_mask_size = np.sum(subcortical_mask.get_fdata()>0)
    roi_size = len(np.unique(cortex_masker.labels_img.get_fdata()))-1

    fcmat = np.zeros((subcortical_mask_size,roi_size))

    subcortical_evoke = {}
    ctx_evoke = {}
    for condition in conditions:
        subcortical_evoke[condition] = np.zeros((subcortical_mask_size)) #subject by time by voxel
        ctx_evoke[condition] = np.zeros((roi_size)) #subject by time by cortical ROI

    # FC
    fn = '/Shared/lss_kahwang_hpc/HCP_data/sub-{}/sub-{}_rfMRI_FIRmodel_MNI_errts_tproject.nii'.format(s,s)
    functional_data = nib.load(fn)
    cortex_ts = cortex_masker.fit_transform(functional_data)
    subcortical_ts = masking.apply_mask(functional_data, subcortical_mask)

    # remove censored timepoints
    mts = np.mean(cortex_ts, axis = 1)
    if any(mts==0):
        del_i = np.where(mts==0)
        cortex_ts = np.delete(cortex_ts, del_i, axis = 0)
        subcortical_ts = np.delete(subcortical_ts, del_i, axis = 0)
    
    #standardize the matrix
    s_cortex_ts=(cortex_ts-cortex_ts.mean(0))/cortex_ts.std(0,ddof=1)
    s_subcortical_voxel_ts=(subcortical_ts-subcortical_ts.mean(0))/subcortical_ts.std(0,ddof=1)

    #caculate the correlation matrix
    fcmat[:, :]=np.arctanh(np.dot(s_subcortical_voxel_ts.T,s_cortex_ts)/(s_subcortical_voxel_ts.shape[0]-1))

    # correlation and partial correlation
    #fcmat[:, :] = generate_correlation_mat(thalamus_ts.T, cortex_ts.T) #th by ctx
    #fcmat[:, :] = pcorr_subcortico_cortical_connectivity(thalamus_ts, cortex_ts)[400:, 0:400]
    #get the evoked response
    fn = nib.load('/Shared/lss_kahwang_hpc/HCP_data/sub-{}/{}_FIRmodel_MNI_stats_REML+tlrc.nii.gz'.format(s,s)).get_fdata().squeeze()
    fir_hrf = image.new_img_like(thalamus_mask,fn)
    subcortical_betas=masking.apply_mask(fir_hrf, subcortical_mask)
    ctx_betas=cortex_masker.fit_transform(fir_hrf)
    #Extract tha and cortical evoke
    for condition in conditions.keys():
        
        subcortical_evoke[condition][:] = subcortical_betas[conditions[condition],:]  #time by voxel
        ctx_evoke[condition][:] = ctx_betas[conditions[condition],:]  #time by cortical ROI

    return s, fcmat, subcortical_evoke, ctx_evoke


for data in ['197','198']:
    df_subs=pd.read_csv('/Shared/lss_kahwang_hpc/HCP_data/activity_flow/indiv_rsfc_corr_actu_prect_{}subs.csv'.format(data))
    subjects=df_subs.subjects.tolist()
    #subjects=subjects[:10]
    
    s = subjects[0] # now instead of spliting subjects into multiple threads, we will do it differntly by spliting ROIs into threads
                    # which requires creating a shared memory object of each subject's functional data that we can access within each thread. 

    # load functional data outside of the pool threads, because otherwise it is way too slow
    fn = '/Shared/lss_kahwang_hpc/HCP_data/sub-{}/sub-{}_rfMRI_FIRmodel_MNI_errts_tproject.nii'.format(s,s)
    functional_data = nib.load(fn)

    ## need to now put functional data into a numpy array, because the multiprocessing shared_memory object only works with arrays or lists.
    f_mat = functional_data.get_fdata() 
    print(f_mat.shape) #it is x, y, z, time, so we can still index it to extract time series from mask


    from multiprocessing import shared_memory
    functional_data_shm = shared_memory.SharedMemory(create=True, size=f_mat.nbytes)
    # put a version of f_mat in share memory
    f_mat_in_shm = np.ndarray(f_mat.shape, buffer=functional_data_shm.buf)
    f_mat_in_shm[:] = f_mat[:]
    del f_mat # save memory
    f_mat_shm_name = functional_data_shm.name # 
    print(f_mat_shm_name) #this is the variable that we can access from the share memory within the loop

    # we will now do the same thing to load the cortical ROI ts and put that in share memory
    cortex_ts = cortex_masker.fit_transform(functional_data) ## this steps also takes a lot of time to run, so do it ouside the pool threads
    cortex_ts_shm = shared_memory.SharedMemory(create=True, size=cortex_ts.nbytes)
    cortex_ts_in_shm = np.ndarray(cortex_ts.shape, buffer=cortex_ts_shm.buf)
    cortex_ts_in_shm[:] = cortex_ts[:]
    cortex_ts_shm_name = cortex_ts_shm.name # 
    print(cortex_ts_shm_name)

    # we will send to other ROIs into each thread
    other_rois=nib.load('/Shared/lss_kahwang_hpc/HCP_data/activity_flow/other_rois/Schaefer100+BG_2mm.nii.gz')
    other_rois_data=other_rois.get_fdata()
    number_of_rois = len(np.unique(other_rois_data))-1

    #this is crearte an iterable object putting all inputs into list of tuples, that will be upacked in the function. The length of this list is the numer of ROIs
    input_lists = zip([cortex_ts_shm_name]*number_of_rois, [f_mat.shape]*number_of_rois [cortex_ts_shm_name]*number_of_rois, [other_rois]*number_of_rois, [cortex_ts.shape]*number_of_rois)
 
    ## below the loop has to be rewritten but I will let you figure it out. Instead of looping through ROI and sending each subject to a pool thread, 
    ## you should be looping through subject, load subject functional data and cortical ts into share memory, then send each ROI to a pool thread that access the share memory.
    for r in range(103):
        roi_data = np.where(other_rois_data==r+1,1,0)
        roi_mask = image.new_img_like(other_rois,roi_data)
        print('start running roi {}'.format(r+1))
        pool = multiprocessing.Pool(80)
        results = pool.map(run_fc_evoke_corr, zip(subjects, [roi_mask]*len(subjects), [cortex_masker]*len(subjects)))
        pool.close()
        pool.join()

        save_object(results,'activity_flow_mapping_rsfc_results_{}subs_roi{}.p'.format(data,r+1))

        ##### unpack results
        print("correlation between observed and predicted cortical evoked pattern by ROI {}".format(r+1))
        print(" ")

        predicted_ctx = np.zeros((len(results), results[0][1].shape[1]))
        observed_ctx = np.zeros((len(results), results[0][1].shape[1]))
        observed_tha = np.zeros((len(results), results[0][1].shape[0]))
        #corr = np.zeros((len(results), len(subjects)))

        #save the rsfc output, shape (197,2227,400)
        group_rsfc=np.zeros((len(results),results[0][1].shape[0],results[0][1].shape[1]))

        pd_dict={'subjects':subjects,
        '0bk':[], '2bk':[], '0bk_body':[], '0bk_faces':[],'0bk_places':[],'0bk_tools':[],
        '2bk_body':[], '2bk_faces':[],'2bk_places':[],'2bk_tools':[],
        'body_others':[],'faces_others':[],'places_others':[],'tools_others':[]}

        pd_diff_dict={'2bk-0bk':[],'2bk-0bk_body':[],'2bk-0bk_faces':[],'2bk-0bk_places':[],'2bk-0bk_tools':[]}

        for ic, cond in enumerate(conditions.keys()):
            for ix , res in enumerate(results):
                fc = np.nan_to_num(np.arctanh(res[1])) #need to fisher's transform
                tha_b = zscore(results[ix][2][cond]) #zscore the actual thalamus evoked response
                ctx_b = zscore(results[ix][3][cond]) #zscore the actual cortical evoked response
                ctx_p = zscore(np.dot(tha_b, fc)) #zscore the predicted evoked response
                # correlate predicted cortical evoke vs observed
                #corr[ic, ix] = np.corrcoef(predicted_ctx[ic, :], observed_ctx[ic, :])[0,1]
                corr=np.dot(ctx_p,ctx_b)/ctx_b.shape[0] #prediction accuracy
                
                pd_dict[cond].append(np.arctanh(corr)) #Fisher's z-transform the correlation before average

                group_rsfc[ix,:,:]=fc
                predicted_ctx[ix, :] = ctx_p
                observed_ctx[ix, :] = ctx_b
                observed_tha[ix, :] = tha_b
            
            ##save the rsfc output, shape (24,2473,400)
            #np.save('group_pca_regression_rsfc_nonfisher_{}subs_roi{}.npy'.format(len(subjects),r+1),group_rsfc)
            ##save the observed thalamus evrs, shape (24,2473)
            #np.save('{}_group_observed_tha_ztransformed_{}subs_roi{}.npy'.format(cond,len(subjects),r+1),observed_tha)
            ##save the observed cortical evrs, shape (24,400)
            #np.save('{}_group_observed_ctx_ztransformed_{}subs_roi{}.npy'.format(cond,len(subjects),r+1),observed_ctx)
            ##save the predicted cortical evrs, shape (24,400)
            #np.save('{}_group_pca_regression_rsfc_predicted_ctx_ztransformed_{}subs_roi{}.npy'.format(cond,len(subjects),r+1),predicted_ctx)
        

        for hm,lm,co in zip(high_wm,low_wm,pd_diff_dict.keys()):
            for ix , res in enumerate(results):
                fc = np.nan_to_num(np.arctanh(res[1])) #need to fisher's transform
                tha_b=zscore(results[ix][2][hm]-results[ix][2][lm]) #zscore the actual thalamus evoked response
                ctx_b=zscore(results[ix][3][hm]-results[ix][3][lm]) #zscore the actual cortical evoked response
                ctx_p=zscore(np.dot(tha_b, fc)) #zscore the predicted evoked response
                corr=np.dot(ctx_p,ctx_b)/ctx_b.shape[0] #prediction accuracy
                pd_diff_dict[co].append(np.arctanh(corr)) 


        pd_dict.update(pd_diff_dict)

        df=pd.DataFrame(data=pd_dict)
        df.to_csv('{}subs_indiv_pca_regression_rsfc_fisherztransform_corr_roi{}.csv'.format(len(subjects),r+1))
        for con in pd_dict.keys():
            print(con)
            #print(corr[ic, :])
            print(np.tanh(df[con].mean())) #return back to Pearson correlation result after average

    ## at the end of the script you need to close the shared memory
    cortex_ts_shm.close()
    cortex_ts_shm.unlink()
    functional_data_shm.close()
    functional_data_shm.unlink()