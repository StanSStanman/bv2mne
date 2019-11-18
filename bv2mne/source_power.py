from directories import *

import mne
import numpy as np
from bv2mne.utils import apply_artifact_rejection#, load_srcs
from bv2mne.forward import create_forward_models
# from bv2mne.csd import csd_epochs

def compute_singletrial_sourcepower(sbj, sn, ev):
    epochs_ev = mne.read_epochs(op.join(prep_dir.format(sbj, sn), '{0}_{1}-epo.fif'.format(sbj, ev)), preload=True)
    epochs_ev = apply_artifact_rejection(epochs_ev, sbj, sn)

    # epochs_bl = mne.read_epochs(op.join(prep_dir.format(sbj, sn), '{0}_baseline-epo.fif'.format(sbj)), preload=True)
    # epochs_bl = apply_artifact_rejection(epochs_bl, sbj, sn)

    t_event = [epochs_ev.tmin, epochs_ev.tmax]

    # srcs = load_srcs(sbj)
    srcs = mne.read_source_spaces(op.join(src_dir.format(sbj), '{0}_surf-src.fif'.format(sbj)))

    # Frequency parameters
    fmin = 88
    fmax = 92
    mt_bandwidth = 60
    # Time parameters
    win_lengths = 0.2
    tstep = 0.005
    # Sampling rate of power estimates
    sfreq = 1 / tstep

    fwds = create_forward_models(sbj, srcs, sn, ev)

    power_event, time_event = get_epochs_dics(epochs_ev, fwds, fmin=fmin, fmax=fmax, tmin=t_event[0],
                                              tmax=t_event[1], tstep=tstep, win_lenghts=win_lengths,
                                              mode='multitaper', mt_bandwidth=mt_bandwidth)

    return power_event, time_event

def get_epochs_dics(epochs_event, fwd, fmin=0, fmax=np.inf, tmin=None, tmax=None, tstep=0.005, win_lenghts=0.2,
                    mode='multitaper', mt_bandwidth=None):

    if tmin is None:
        tmin = epochs_event.times[0]
    else: tmin = tmin
    if tmax is None:
        tmax = epochs_event.times[-1] - win_lenghts
    else: tmax = tmax - win_lenghts

    n_tsteps = int(((tmax - tmin) * 1e3) // (tstep * 1e3))

    power = []
    time = np.zeros(n_tsteps)

    for it in range(n_tsteps):

        win_tmin = tmin + (it * tstep)
        win_tmax = win_tmin + win_lenghts
        time[it] = win_tmin + (win_lenghts / 2.)

        avg_csds = None

        print('.....From {0}s to {1}s'.format(win_tmin, win_tmax))
        # csds_cust = csd_epochs(epochs_event, mode='multitaper', fmin=88, fmax=92, tmin=0.0, tmax=0.2, fsum=False,
        #                        n_fft=None, mt_bandwidth=60, mt_adaptive=False, mt_low_bias=False, avg_tapers=False,
        #                        on_epochs=False)

        csds = mne.time_frequency.csd_multitaper(epochs_event, fmin=fmin, fmax=fmax, tmin=win_tmin, tmax=win_tmax,
                                                 bandwidth=mt_bandwidth, n_jobs=-1)

        if len(csds[0]._data.shape) > 2:
            avg_csds = mne.time_frequency.csd_multitaper(epochs_event, fmin=fmin, fmax=fmax, tmin=win_tmin, tmax=win_tmax,
                                                         bandwidth=mt_bandwidth, n_jobs=-1)

        beamformer = mne.beamformer.make_dics(epochs_event.info, fwd, csds, reg=0.05)
        power_time = mne.beamformer.apply_dics_csd(csds, beamformer)

        power.append(power_time)


    return power, time
