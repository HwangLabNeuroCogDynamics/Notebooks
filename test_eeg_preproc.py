#testing a EEG preprocessing pipeline.


import mne
from mne import io
import os
import pandas as pd
import numpy as np
import glob
import matplotlib.pyplot as plt
plt.ion()

output_path = '/data/backed_up/shared/ThalHi_EEG/preproc_EEG/'
raw_bids = '/data/backed_up/shared/ThalHi_EEG/BIDS/'
raw_behav = '/mnt/cifs/rdss/rdss_kahwang/ThalHi_data/EEG_data/Hospital_EEG_Behavioral_data/'
subjects = ['4032']

for sub in subjects:
    raw_file = raw_bids + f"sub-{sub}/ses-02/eeg/sub-{sub}_ses-02_task-ThalHi_eeg.vhdr"
    raw = mne.io.read_raw_brainvision(raw_file, preload = True)
    
    ##### Kai Note: based on brainvision's email, might have to create our own, will have to test more
    raw.set_montage(montage = "standard_1020") 


    #inspect channel, reject bad channels, and interpolate
    raw.plot(n_channels = 64)
    i = input("Press Enter to Continue: ")
    if raw.info['bads']: 
        eeg_data = raw.copy().pick_types(eeg = True, exclude=[])
        eeg_data_interp = eeg_data.copy().interpolate_bads()
        for title, data in zip(['orig.', 'interp.'], [eeg_data, eeg_data_interp]):
            with mne.viz.use_browser_backend('matplotlib'):
                fig = data.plot(butterfly = True, color = '#00000022', bad_color = 'r')
            fig.subplots_adjust(top = 0.9)
            fig.suptitle(title, size = 'xx-large', weight = 'bold')
        ##### Kai Note: I picked a random bad channel just to test it, the figure is interesting but not sure what it means. Look into futher.

    else:
        i = input("Press Enter to Continue: ")
 
	
    #Filter data
    raw.filter(l_freq=0.1, h_freq=50.0)
    raw.plot(n_channels = 64)
    i = input("Press Enter to Continue: ")

    # Output from MNE: 
    # FIR filter parameters
    # ---------------------
    # Designing a one-pass, zero-phase, non-causal bandpass filter:
    # - Windowed time-domain design (firwin) method
    # - Hamming window with 0.0194 passband ripple and 53 dB stopband attenuation
    # - Lower passband edge: 0.10
    # - Lower transition bandwidth: 0.10 Hz (-6 dB cutoff frequency: 0.05 Hz)
    # - Upper passband edge: 50.00 Hz
    # - Upper transition bandwidth: 12.50 Hz (-6 dB cutoff frequency: 56.25 Hz)
    # - Filter length: 33001 samples (33.001 sec)


    #Rereference the data. We will use electrode Fcz with the brainvision system
    raw.add_reference_channels(ref_channels = ['Fcz'])
    raw.plot(n_channels = 64)
    i = input("Press Enter to Continue: ")

    raw_reref = raw.set_eeg_reference(ref_channels='average')
    raw_reref.plot(n_channels = 64)
    i = input("Press Enter to Continue: ")

    #Create a data frame in which you've appended all of the subject's behavioral data files
    behav_files = glob.glob(raw_behav+f'{sub}_00*.csv')
    behav_df = pd.DataFrame()
    for f in behav_files:
        behav_df = behav_df.append(pd.read_csv(f))
    behav_df
    #try this raw_reref.metadata =  behav_df    
    raw_reref.metadata = behav_df 

    #Set Events
    events = mne.events_from_annotations(raw_reref)

    probe_indices = (events[0][:,2] == 151) + (events[0][:,2] == 153)
    probe_events = events[0][probe_indices]

    probe_event_id = {'Face': 151, 'Scene': 153}
    #Epoch the data
    probe_epochs = mne.Epochs(raw = raw_reref, events = probe_events, event_id = probe_event_id, tmin = -2.5, tmax = 2.0,
                             baseline = (None, -0.3), on_missing = 'warn', metadata = behav_df, event_repeated = 'drop',
                             preload = True)
    mne.Epochs.plot(probe_epochs)
    i = input("Press Enter to Continue: ")

    ICA_model = mne.preprocessing.ICA(method = 'infomax', fit_params=dict(extended=True))
    ICA_model.fit(probe_epochs)
    ICA_model.plot_properties(probe_epochs, picks = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20])
    i = input("Press Enter to Continue: ")

    ICA_model.plot_components()
    i = input("Press Enter to Continue: ")
    
    # there might be an additional step of actually rejecting the ICs.
    ICA_model.apply(probe_epochs)
    # then plot again to make suread = T components actually rejected
    ICA_model.plot_components()
    i = input("Press Enter to Continue: ")

    #Save output
    probe_epochs.save(f"/data/backed_up/shared/ThalHi_EEG/BIDS/sub-{sub}/ses-02/eeg/sub-{sub}_ses-02_task-ThalHi_eeg-epo.fif")