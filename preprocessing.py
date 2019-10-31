import mne
import numpy as np
import os
from autoreject import AutoReject
from directories import *
from arifact_rejection import GUI_plot
import matplotlib.pyplot as plt

def get_raw_causal(subjects):

    # Loop on subjects
    for sbj in subjects:

        # Loop on raw foldrs
        for d in os.listdir(op.join(db_raw, sbj)):
            if op.isdir(op.join(db_raw, sbj, d)):
                db_raw_dir = op.join(db_raw, sbj, d)

                # Defining raw files
                pdf_name = op.join(db_raw_dir, fname_bti)
                config_name = op.join(db_raw_dir, fname_config)
                head_shape_name  = op.join(db_raw_dir, fname_hs)

                # Load raw data
                raw = mne.io.read_raw_bti(pdf_name, config_name, head_shape_name, rename_channels=False,
                                          sort_by_ch_name=True, preload=True)

                # Event data ("trigger" channels)
                events = mne.find_events(raw, stim_channel='TRIGGER', min_duration=0.005, shortest_event=2)

                # Responses
                resps = mne.find_events(raw, stim_channel='RESPONSE')

                # Define codes for Stim, Action and Reward
                O_id = [522, 532, 542]  # Stim 10, 20, 30 + 512 of photodyode code
                A_id = [256, 512]  # Play / don't play choice

                # We want to slice the data according to the different conditions
                cnd_start = [102, 104, 106, 108, 110, 112, 114, 116, 118, 120, 122, 124, 126, 128, 130]
                cnd_end = [202, 204, 206, 208, 210, 212, 214, 216, 218, 220, 222, 224, 226, 228, 230]

                idx_start = []
                idx_end = []
                idx_cond = []
                for n, i in enumerate(events[:, 2]):
                    if i in cnd_start:
                        idx_start.append(n)
                        idx_cond.append(cnd_start.index(i) + 1)
                    if i in cnd_end:
                        idx_end.append(n)

                # In case of 'emergency' break this glass
                if len(idx_start) > len(idx_end):
                    idx_end.append(len(events))
                    # idx_start[2] = idx_start[2]-1

                conditions = np.zeros((len(idx_start), events[idx_start[0]:idx_end[0]].shape[0], events.shape[1]),
                                      dtype=int)

                start_time = 0.
                for idx in range(len(idx_start)):
                    conditions[idx] = events[idx_start[idx]:idx_end[idx]]
                    print('\n========== Processing the SCENARIO n. ', idx_cond[idx], ' ==========')

                    # Saving cropped raw file for mne
                    raw_copy = raw.copy()
                    end_time = raw_copy.times[conditions[idx][-1, 0]]
                    raw_copy.crop(tmin=start_time, tmax=end_time + 5.)
                    if not op.exists(raw_dir.format(sbj, idx_cond[idx])):
                        os.makedirs(raw_dir.format(sbj, idx_cond[idx]))
                    raw_copy.save(op.join(raw_dir.format(sbj, idx_cond[idx]), '{0}_raw.fif'.format(sbj)), overwrite=True)

                    # Save event file for mne_analyze
                    if not op.exists(prep_dir.format(sbj, idx_cond[idx])):
                        os.makedirs(prep_dir.format(sbj, idx_cond[idx]))
                    mne.write_events(op.join(prep_dir.format(sbj, idx_cond[idx]), '{0}-eve.fif'.format(sbj)), conditions[idx])

                    # Get action events
                    outc = conditions[idx][np.logical_or.reduce([conditions[idx][:, -1] == _id for _id in O_id])]

                    # Get outcome events
                    acts = resps[np.logical_or.reduce([resps[:, -1] == _id for _id in A_id])]

                    # Delete all previous actions except the last one before the first outcome
                    _ac = acts[:, 0] > outc[0, 0]
                    _ac = (np.where(_ac == 0))[0]
                    acts = np.delete(acts, (_ac[0:-1]), 0)

                    # Delete all actions after the last outcome of interest
                    acts = np.delete(acts, (np.where(acts[:, 0] > outc[-1, 0])[0]), 0)

                    # ___________________________________________________________________________________________________________________
                    # @author: Nathan Coppe
                    # Take out the supplementary responses
                    bads = {}
                    for n, a in enumerate(outc[:, 0]):
                        for m, i in enumerate(acts[:, 0]):
                            if m < (acts.shape[0] - 1):
                                if a < i < outc[:, 0][n + 1] and a < acts[:, 0][m + 1] < outc[:, 0][n + 1]:
                                    bads[m] = i

                    acts = np.delete(acts, list(bads.keys()), axis=0)

                    A_size = acts.shape[0]
                    O_size = outc.shape[0]
                    assert (A_size == O_size), 'Actions and Outcomes arrays have not the same size'
                    # ___________________________________________________________________________________________________________________

                    # Take only correct and incorrect trials (remove late trials)
                    c = acts[:, 2] != 542
                    if np.any(c) != True:
                        acts = acts[c]
                        outc = outc[c]

                    # Save all the important events and times for each scenario in a pickle file
                    mne.write_events(op.join(prep_dir.format(sbj, idx_cond[idx]), '{0}_action-eve.fif'.format(sbj)), acts)
                    mne.write_events(op.join(prep_dir.format(sbj, idx_cond[idx]), '{0}_outcome-eve.fif'.format(sbj)), outc)

    return

def meg_preprocessing(subjects, sessions, art_rej=[None, (0., 0.)], event_epochs=[None],
                      event_time=[(-1.5, 1.5)], baseline=[None, (0., 0.)]):
    for sbj in subjects:
        for sn in sessions:
            print('\n----- Preprocessing subject {0}, session {1} -----'.format(sbj, sn))

            raw = mne.io.read_raw_fif(op.join(raw_dir.format(sbj, sn), '{0}_raw.fif'.format(sbj)), preload=True)

            ##### First way to proceed, not sure about it....
            # if art_rej[0] != None:
            #     # Loading events for artifact rejection epoching
            #     ar_event = mne.read_events(op.join(prep_dir.format(sbj, sn), '{0}_{1}-eve.fif'.format(sbj, art_rej[0])))
            #     tmin = art_rej[1][0]
            #     tmax = art_rej[1][1]
            #
            #     # MEG data
            #     meg = raw.copy().pick_types(meg=True)
            #     meg_epochs = mne.Epochs(raw=meg, events=ar_event, tmin=tmin, tmax=tmax, baseline=None)
            #
            #
            #     # # Filter in the high-gamma range
            #     # hga = meg.copy()
            #     # hga = hga.filter(60, 120)
            #     # hga_epochs = mne.Epochs(raw=hga, events=ar_event, tmin=tmin, tmax=tmax)
            #     # epoch_datas = hga_epochs.get_data()
            #
            #     # RMS
            #     # rms = np.sqrt(np.mean(np.square(epoch_datas), axis=2))
            #     rms = np.sqrt(np.mean(np.square(meg_epochs.get_data()), axis=2))
            #
            #     # Grafical artifact rejection
            #     artifact_rejection = GUI_plot(rms, prep_dir.format(sbj, sn))
            #     print('artifact rejection ', artifact_rejection)
            #
            # if type(artifact_rejection[0]) != type(None):
            #     bad_chans = list(meg.ch_names[c] for c in list(artifact_rejection[0]))
            #     raw.drop_channels(bad_chans)
            #####

            ##### Second way, slower but more reliable
            # MEG data
            meg = raw.copy().pick_types(meg=True)
            meg.resample(500)
            meg.plot(show=False)
            plt.show()
            bad_chans = meg.info['bads']
            # raw.drop_channels(bad_chans)
            print('\n----- Channels {0} marked as bad -----'.format(bad_chans))

            d = {'bad_chans': bad_chans, 'bad_trials': []}
            np.savez(op.join(prep_dir.format(sbj, sn), 'artifact_rejection'), ar=d)
            #####

            # Band pass filter
            raw.filter(1, 250)

            # Nothc filter
            raw.notch_filter(np.arange(50, 151, 50))

            # Independent component analysis
            ica = mne.preprocessing.ICA(n_components=0.95, method='fastica').fit(raw)
            ica.plot_components(picks=range(20))
            ica.apply(raw)

            for ev, t in zip(event_epochs, event_time):
                if ev == None:
                    events = mne.read_events(op.join(prep_dir.format(sbj, sn), '{0}-eve.fif'.format(sbj)))
                else:
                    events = mne.read_events(op.join(prep_dir.format(sbj, sn), '{0}_{1}-eve.fif'.format(sbj, ev)))

                tmin = t[0]
                tmax = t[1]

                epochs = mne.Epochs(raw=raw, events=events, tmin=tmin, tmax=tmax, preload=True, baseline=None)
                epochs.save(op.join(prep_dir.format(sbj, sn), '{0}_{1}-epo.fif'.format(sbj, ev)))

            if type(baseline[0]) == str:
                events = mne.read_events(op.join(prep_dir.format(sbj, sn), '{0}_{1}-eve.fif'.format(sbj, baseline[0])))
                tmin = baseline[1][0]
                tmax = baseline[1][1]

                epochs = mne.Epochs(raw=raw, events=events, tmin=tmin, tmax=tmax, baseline=None)
                epochs.save(op.join(prep_dir.format(sbj, sn), '{0}_baseline-epo.fif'.format(sbj)))

    return

def trials_autoreject(subjects, sessions, events, save=False):
    for sbj in subjects:
        for sn in sessions:
            for ev in events:
                epochs = mne.read_epochs(op.join(prep_dir.format(sbj, sn), '{0}_{1}-epo.fif'.format(sbj, ev)), preload=True)
                ar_epochs = AutoReject(n_jobs=-1).fit_transform(epochs)
                if save == True:
                    ar_epochs.save(op.join(prep_dir.format(sbj, sn), '{0}_{1}-epo.fif'.format(sbj, ev)))

                bad_trials = list(i for i in range(len(ar_epochs.drop_log)) if ar_epochs.drop_log[i])
                d = np.load(op.join(prep_dir.format(sbj, sn), 'artifact_rejection.npz'), allow_pickle=True)
                ar = d['ar'].item()
                ar['bad_trials'] = bad_trials
                np.savez(op.join(prep_dir.format(sbj, sn), 'artifact_rejection'), ar=ar)
                print('----- Trials {0} marked as bad -----\n'.format(bad_trials))
    return
