from preprocessing import *
from bv2mne.source import create_source_models #create_forward_models
# from bv2mne.source_power import compute_singletrial_sourcepower

subjects = ['subject_02']
sessions = [1] #range(1, 16)

events = ['action', 'outcome']
times = [(-1.1, 2.), (-1.6, 1.6)]

baseline = ['action', (-1.3, -0.8)]

# Preprocessing pipeline
# ----------------------------------------------------------------------------------------------------------------------
# get_raw_causal(subjects)
#
# meg_preprocessing(subjects, sessions, art_rej=['action', (-1., 1.)], event_epochs=events,
#                   event_time=times, baseline=baseline)
#
# trials_autoreject(subjects, sessions, events, save=False)
# ----------------------------------------------------------------------------------------------------------------------

# Source estimate pipeline
# ----------------------------------------------------------------------------------------------------------------------
srcs, surfaces, volumes = create_source_models(subjects[0], save=True)
# ----------------------------------------------------------------------------------------------------------------------

# HGA estimation pipeline
# ----------------------------------------------------------------------------------------------------------------------
# fwds = create_forward_models(subjects[0], srcs, '1', 'action')
# stsp = compute_singletrial_sourcepower('subject_01', 1, 'action')
print('ciao')
# ----------------------------------------------------------------------------------------------------------------------
