import os.path as op
from bv2mne.config.config import setup_db_coords
from bv2mne.source import create_source_models

# def create_main(database, project, subjects, ses, event, json):
#
#     if not json:
#         json = setup_db_coords(database, project, overwrite=True)
#
#     from bv2mne.source import create_source_models
#     from bv2mne.forward import create_forward_models
#
#     for sbj in subjects:
#
#         create_sbj_db_mne (json, sbj)
#         # Pipeline for the estimation of surfaces/volumes sources and labels
#         # ------------------------------------------------------------------------------------------------------------------
#         surf_src, surf_labels, vol_src, vol_labels = create_source_models(sbj, save=True)
#         # ------------------------------------------------------------------------------------------------------------------
#
#         # Pipeline to estimate surfaces/volumes forward models
#         # ------------------------------------------------------------------------------------------------------------------
#         fwds = create_forward_models(sbj, ses, event, json)
#         # ------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    project = 'meg_causal'
    db_fs = op.join('D:\\', 'Databases', 'toy_db', 'db_freesurfer', project)
    db_bv =op.join('D:\\', 'Databases', 'toy_db', 'db_brainvisa', project)
    db_mne = op.join('D:\\', 'Databases', 'toy_db', 'db_mne', project)

    setup_db_coords(db_fs, db_bv, db_mne, json_path='default', overwrite=True)

    subjects = ['subject_01']

    for sbj in subjects:
        create_source_models(sbj, bem_dir=None, trans_dir=None, src_dir=None,
                             json_fname='default', decim='4K', save=True)