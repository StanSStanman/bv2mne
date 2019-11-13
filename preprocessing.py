import mne
import numpy as np
import os
from autoreject import AutoReject
from directories import *
from arifact_rejection import GUI_plot
import matplotlib.pyplot as plt


def meg_preprocessing(subject, session, art_rej=[None, (0., 0.)], event_epochs=[None],
                      event_time=[(-1.5, 1.5)], baseline=[None, (0., 0.)]):
    # for sbj in subjects:
    #     for sn in sessions:
    print('\n----- Preprocessing subject {0}, session {1} -----'.format(subject, session))

    raw = mne.io.read_raw_fif(op.join(raw_dir.format(subject, session), '{0}_raw.fif'.format(subject)), preload=True)

    ##### First way to proceed, not sure about it....
    # if art_rej[0] != None:
    #     # Loading events for artifact rejection epoching
    #     ar_event = mne.read_events(op.join(prep_dir.format(subject, session), '{0}_{1}-eve.fif'.format(subject, art_rej[0])))
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
    #     artifact_rejection = GUI_plot(rms, prep_dir.format(subject, session))
    #     print('artifact rejection ', artifact_rejection)
    #
    # if type(artifact_rejection[0]) != type(None):
    #     bad_chans = list(meg.ch_names[c] for c in list(artifact_rejection[0]))
    #     raw.drop_channels(bad_chans)
    #####

    ##### Second way, slower but more reliable
    # MEG data
    meg = raw.copy().pick_types(meg=True)
    meg.resample(600)
    meg.plot(show=False)
    plt.show()
    bad_chans = meg.info['bads']
    # raw.drop_channels(bad_chans)
    print('\n----- Channels {0} marked as bad -----'.format(bad_chans))

    # d = {'bad_chans': bad_chans, 'bad_trials': []}
    np.savez(op.join(prep_dir.format(subject, session), 'channels_rejection'), ar=bad_chans)
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
            events = mne.read_events(op.join(prep_dir.format(subject, session), '{0}-eve.fif'.format(subject)))
        else:
            events = mne.read_events(op.join(prep_dir.format(subject, session), '{0}_{1}-eve.fif'.format(subject, ev)))

        tmin = t[0]
        tmax = t[1]

        epochs = mne.Epochs(raw=raw, events=events, tmin=tmin, tmax=tmax, preload=True, baseline=None)
        epochs.save(op.join(prep_dir.format(subject, session), '{0}_{1}-epo.fif'.format(subject, ev)))

    if type(baseline[0]) == str:
        events = mne.read_events(op.join(prep_dir.format(subject, session), '{0}_{1}-eve.fif'.format(subject, baseline[0])))
        tmin = baseline[1][0]
        tmax = baseline[1][1]

        epochs = mne.Epochs(raw=raw, events=events, tmin=tmin, tmax=tmax, baseline=None)
        epochs.save(op.join(prep_dir.format(subject, session), '{0}_baseline-epo.fif'.format(subject)))

    return

def trials_autoreject(subject, session, event, save=False):
    # for sbj in subjects:
    #     for session in session:
    #         for ev in events:
    epochs = mne.read_epochs(op.join(prep_dir.format(subject, session), '{0}_{1}-epo.fif'.format(subject, event)), preload=True)
    ar_epochs = AutoReject(n_jobs=-1).fit_transform(epochs)
    if save == True:
        ar_epochs.save(op.join(prep_dir.format(subject, session), '{0}_{1}-epo.fif'.format(subject, event)))

    # BUG TO SOLVE: for different events there could be differents artifact rejection, so it would be nice
    #               if they're saved in different .npz files (see case of sub_2 sess_4 outcome)
    bad_trials = list(i for i in range(len(ar_epochs.drop_log)) if ar_epochs.drop_log[i])
    # d = np.load(op.join(prep_dir.format(subject, session), 'artifact_rejection.npz'), allow_pickle=True)
    # ar = d['ar'].item()
    # ar['bad_trials'] = bad_trials
    np.savez(op.join(prep_dir.format(subject, session), 'trials_rejection-{0}'.format(event)), ar=bad_trials)
    print('----- Trials {0} marked as bad -----\n'.format(bad_trials))
    return
