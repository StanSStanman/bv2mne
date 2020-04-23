import os.path as op
from bv2mne.config.config import setup_db_coords
from bv2mne.source import create_source_models

dbss = 'G:\\data'
project = 'meg_causal'
db_fs = op.join(dbss, 'db_freesurfer', project)
db_bv = op.join(dbss, 'db_brainvisa', project)
db_mne = op.join(dbss, 'db_mne', project)
setup_db_coords(db_fs, db_bv, db_mne=db_mne, json_path='default', overwrite=True)

if __name__ == '__main__':

    subjects = ['subject_01', 'subject_02', 'subject_04', 'subject_05', 'subject_06', 'subject_07',
                'subject_08', 'subject_09', 'subject_10', 'subject_11', 'subject_13', 'subject_14',
                'subject_15', 'subject_16', 'subject_17', 'subject_18']
    subjects = ['subject_18']

    for sbj in subjects:
        create_source_models(sbj, bem_dir=None, trans_dir=None, src_dir=None,
                             json_fname='default', decim='4K', save=True)