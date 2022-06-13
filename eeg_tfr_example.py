## template script for running TFR on one tree thalhi

import numpy as np
from numpy import average, std
import pickle
from numpy.random import random, randint, normal, shuffle,uniform
import scipy
from scipy import sparse
from scipy.stats import ttest_ind
from scipy.spatial.distance import pdist
from scipy.cluster.hierarchy import dendrogram,linkage
from scipy.stats.mstats import zscore
import seaborn as sns
import fnmatch
import os  # handy system and path functions
import sys  # to get file system encoding
import csv
from pandas import DataFrame, read_csv
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib
import mne
#import FOOOF
from mne.time_frequency import tfr_morlet
plt.ion() #turning interactive plotter off
#print(matplotlib.is_interactive())
#matplotlib.use('Agg')

def mirror_evoke(ep):

	e = ep.copy()
	nd = np.concatenate((np.flip(e._data[:,:,e.time_as_index(0)[0]:e.time_as_index(1.5)[0]], axis=2), e._data, np.flip(e._data[:,:,e.time_as_index(e.tmax-1.5)[0]:e.time_as_index(e.tmax)[0]],axis=2)),axis=2)
	tnmin = e.tmin - 1.5
	tnmax = e.tmax + 1.5
	e._set_times(np.arange(tnmin,tnmax+e.times[2]-e.times[1],e.times[2]-e.times[1]))
	e._data = nd

	return e

def mirror_iti(ep):

	e = ep.copy()
	nd = np.concatenate((np.flip(e._data[:,:,e.time_as_index(0)[0]:e.time_as_index(3)[0]], axis=2), e._data, np.flip(e._data[:,:,e.time_as_index(e.tmax-3)[0]:e.time_as_index(e.tmax)[0]],axis=2)),axis=2)
	tnmin = e.tmin - 3
	tnmax = e.tmax + 3
	e._set_times(np.arange(tnmin,tnmax+e.times[2]-e.times[1],e.times[2]-e.times[1]))
	e._data = nd

	return e


#Read epoch
epochs = mne.read_epochs('sub-4015_ses-01_task-ThalHi_probe_eeg-epo.fif')
ITI_epoch = mne.read_epochs('sub-4015_ses-01_task-ThalHi_ITI_eeg-epo.fif')
Stay_epoch = epochs[epochs.metadata.Trial_type=='Stay']
IDS_epoch = epochs[epochs.metadata.Trial_type=='IDS']

#resample the data, don't need it to be at 500Hz, to save memory ds to 128 hz.
ITI_epoch = ITI_epoch.resample(128,'auto')
Stay_epoch = Stay_epoch.resample(128,'auto')
IDS_epoch = ITI_epoch.resample(128,'auto')

# now run the wavelet filter to turn data from time to time-frequency domain
''' Some background here
https://mne.tools/stable/auto_tutorials/time-freq/20_sensors_time_frequency.html
https://mne.tools/stable/auto_examples/time_frequency/time_frequency_simulated.html#sphx-glr-auto-examples-time-frequency-time-frequency-simulated-py
'''

freqs = np.logspace(*np.log10([1, 40]), num=20)
n_cycles = 6

#"To prevent edge effect I "mirrored" the data
ITI_tfr = tfr_morlet(mirror_iti(mirror_iti(ITI_epoch)), freqs=freqs, average=False,n_cycles=n_cycles, use_fft=True, return_itc=False, decim=1, n_jobs=16)
ITI_tfr = ITI_tfr.crop(tmin = ITI_epoch.tmin, tmax = ITI_epoch.tmax)

Stay_TFR = tfr_morlet(mirror_evoke(mirror_evoke(mirror_evoke(Stay_epoch.crop(tmin=-1, tmax=Stay_epoch.tmax)))), freqs=freqs, average=False, n_cycles=n_cycles, use_fft=True, return_itc=False, decim=1, n_jobs=16)
Stay_TFR = Stay_TFR.crop(tmin = -1, tmax = Stay_epoch.tmax)
IDS_TFR = tfr_morlet(mirror_evoke(mirror_evoke(mirror_evoke(IDS_epoch.crop(tmin=-1, tmax=IDS_epoch.tmax)))), freqs=freqs, average=False, n_cycles=n_cycles, use_fft=True, return_itc=False, decim=1, n_jobs=16)
IDS_TFR = IDS_TFR.crop(tmin = -1, tmax = IDS_epoch.tmax)

# save data to disk
# because these TFR objects are big and takes time to run might as well save to disk so in the future we can just read the finished product
ITI_tfr.save("sub-4015_ITI-tfr.h5")
Stay_TFR.save("sub-4015_Stay-tfr.h5")
IDS_TFR.save("sub-4015_IDS-tfr.h5")

## basic plotting. We will need more subjects before we can do statistic analysis
# the TFR object has all the trial info which will be useful later, but for now we will average across trials for visualization purposes
ave_Stay = Stay_TFR.average()
ave_Stay.plot_topomap(tmin=-0.5, tmax=0, fmin=4, fmax=8, baseline=(-1, -0.5), mode='zscore', title=' Stay Theta')

ave_IDS = IDS_TFR.average()
ave_IDS.plot_topomap(tmin=-0.5, tmax=0, fmin=4, fmax=8, baseline=(-1, -0.5), mode='zscore', title=' Stay Theta')

ave_IDS.plot_joint(baseline=(-1, -0.5), mode='mean', tmin=-.5, tmax=2, timefreqs=[(0, 4), (0.3, 8)])

#eventually we have to extract the time-freqeuncy data to do statistics:
print(ave_IDS.data.shape) # here the data grid is channel by frequency by time