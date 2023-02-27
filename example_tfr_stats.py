# An example script on how to run statistics on time-frequency estimates.

# We will be using cluster-based permutation test. Details can be found in this paper:
# https://www.sciencedirect.com/science/article/abs/pii/S0165027007001707

# We will be using MNE functions, some examples can be found on its website.
# the two primary functions are:
# https://mne.tools/stable/generated/mne.stats.spatio_temporal_cluster_test.html#mne.stats.spatio_temporal_cluster_test
# https://mne.tools/stable/generated/mne.stats.spatio_temporal_cluster_1samp_test.html#mne.stats.spatio_temporal_cluster_1samp_test
# both performed mass-univariate stats on high-D data, 4D in our case, subject by time-frequency-space. 
# also see: https://mne.tools/stable/auto_tutorials/stats-sensor-space/10_background_stats.html#sphx-glr-auto-tutorials-stats-sensor-space-10-background-stats-py
# https://mne.tools/stable/auto_tutorials/stats-sensor-space/75_cluster_ftest_spatiotemporal.html#sphx-glr-auto-tutorials-stats-sensor-space-75-cluster-ftest-spatiotemporal-py

# this sript depends on having the time-frequency estiamtes already calculated and saved. Example script for that can be found here:
# https://github.com/HwangLabNeuroCogDynamics/ThalHiEEG/blob/master/analyze_task_switch.py

import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd  
import mne
import os
import scipy

data_path = "/data/backed_up/shared/ThalHi_EEG/preproc_EEG/figures/" #be care to check where you stored your data
subjects = ['103', '107', '108', '110', '111', '125', '128', '140', '142', '76', '80', '82'] #only doing some subs for this example, include all subjects in your own script.

# check the TFR output, get a sense of the size and shape of the data. 
sub='103'
EDS_tfr = mne.time_frequency.read_tfrs(data_path+"%s-EDS-tfr.h5" %sub)[0]
print(EDS_tfr.data.shape) 
# Note, the data appears to be already z-scored. If its not, you need to run it.
# the shape of the data is 78, 64, 20, 1537. Which is trial by channel by frequency by time

# based on the shape of the data, now we need to create all zero arrays to stored each subject's averaged data.
subs_eds = np.zeros((len(subjects), EDS_tfr.data.shape[1], EDS_tfr.data.shape[2], EDS_tfr.data.shape[3]))
subs_ids = np.zeros((len(subjects), EDS_tfr.data.shape[1], EDS_tfr.data.shape[2], EDS_tfr.data.shape[3]))
subs_stay = np.zeros((len(subjects), EDS_tfr.data.shape[1], EDS_tfr.data.shape[2], EDS_tfr.data.shape[3]))

# Load each subject's trial by trial time-frequency estimates, averaged across trials, and then saved it into the array we created. Here we are only dealing with correct trials.
for i, sub in enumerate(subjects):
    EDS_tfr = mne.time_frequency.read_tfrs(data_path+"%s-EDS-tfr.h5" %sub)[0]
    IDS_tfr = mne.time_frequency.read_tfrs(data_path+"%s-IDS-tfr.h5" %sub)[0]
    stay_tfr = mne.time_frequency.read_tfrs(data_path+"%s-stay-tfr.h5" %sub)[0]
    
    try:
        subs_eds[i,:,:,:] = EDS_tfr[(EDS_tfr.metadata['trial_Corr']==1)].average().data #average all the correct trials, then put into the subject array
        # one issue that I encoutered is not all subjects have 64 channels of data, this appears because if a channel is rejected, its TFR output will not be saved. This is problematic, and I 
        # think the best way to handel this is to interpolate the bad channels. At this point I don't have code to do that. So we will have that leave that as a challenge to solve in the future.
        
        subs_ids[i,:,:,:] = IDS_tfr[(IDS_tfr.metadata['trial_Corr']==1)].average().data
        subs_stay[i,:,:,:] = stay_tfr[(stay_tfr.metadata['trial_Corr']==1)].average().data
    except:
        print(sub + " has bad channels?")

# now we create the "adj" matrix to determine chn-time-frequency adj points. This is necessary to determine what datat points are allowed to be connected as clusters.
ch_adj, ch_names = mne.channels.find_ch_adjacency(stay_tfr.info, ch_type='eeg')
#mne.viz.plot_ch_adjacency(cue.info, adj, ch_names)
adjacency = mne.stats.combine_adjacency(len(stay_tfr.freqs), len(stay_tfr.times),ch_adj)

#now we can create contrast of interest. Let us do EDS vs Stay.
EDS_v_Stay = subs_eds - subs_stay # this is the data array that stores this contrast for every subject

# calculate the statistical threshold, here we use paird sample t test.
degrees_of_freedom = len(subjects) - 1
t_thresh = scipy.stats.t.ppf(1 - 0.05, df=degrees_of_freedom)

# now do the cluster-based permutation test. 1000 permutations. read the function description carefully to understand what it is doing.
# Especially the different outputs. 
# https://mne.tools/stable/generated/mne.stats.spatio_temporal_cluster_1samp_test.html#mne.stats.spatio_temporal_cluster_1samp_test
EDS_v_Stay = EDS_v_Stay.transpose((0, 2, 3, 1)) # the permation function requires the last dimension to be "space", which is channel, and the first dimension to be subject, so we need to rearange it
# from subject by chn by time by freq into subject by time by frequency by chn

T_obs, clusters, cluster_p_values, H0 = mne.stats.permutation_cluster_1samp_test(EDS_v_Stay, n_permutations=1000,
                                   threshold=t_thresh, tail=0,
                                   adjacency=adjacency, t_power =1,
                                   out_type='mask', verbose=True, n_jobs = 24)
# this takes a while, 10 min or so.

# Now let us see if there are any significant clusters? there should be because I inserted one...
cluster_inds = np.where(cluster_p_values < .05)[0]
print(cluster_inds) # these are the significant cluster indices
print(clusters[cluster_inds[0]].shape) #this is the shape of the boolean cluster, 

# now we will create a mask to visualize the significant clusters
mask = np.zeros((T_obs.shape))
for clust_i in cluster_inds:
    mask = mask + clusters[cluster_inds[clust_i]]
mask = mask>0
T_obs_masked = T_obs * mask #zero out not sig datapoints

# turn the t stats output into a TFR object for visualization
EDS_v_Stay_tfr = mne.time_frequency.AverageTFR(info = stay_tfr.info, data = T_obs_masked.transpose((2,0,1)), times = stay_tfr.times, freqs = stay_tfr.freqs, nave = len(subjects)) 
#note we have to reshape the t-stats data back into chn by time by freq

EDS_v_Stay_tfr.plot_topo() #because I inserted a fake cluster, this will be very much out of scale

# A few practices
# 1. This is just paired sample t test, what about an ANOVA test of EDS, IDS, Stay? Hint, look at spatio_temporal_cluster_test
# 2. Are there other ways of visulize the data? Hint, you will have to play around with the mask
# 3. This is statistics on time-frequency data? What about evoked data? Hint, yes the function applies to evoked data as well, but you will have to think carefully about the data dimension.

