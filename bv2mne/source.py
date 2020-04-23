# Authors: David Meunier <david.meunier@univ-amu.fr>
#          Ruggero Basanisi <ruggero.basanisi@gmail.com>

import os
import os.path as op
import numpy as np

import mne
from mne import SourceSpaces

# from bv2mne.directories import read_databases, read_directories

from bv2mne.config.config import read_db_coords
from bv2mne.directories import mne_directories
from bv2mne.hipop138 import get_decimated
from bv2mne.surface import get_surface, get_surface_labels
from bv2mne.volume import get_volume, get_volume_labels
from bv2mne.utils import create_trans
from bv2mne.bem import check_bem, create_bem


def create_source_models(subject, bem_dir=None, trans_dir=None, src_dir=None,
                         json_fname='default', decim='orig', save=False):
    """ Create cortical and subcortical source models

    Pipeline for:
        i) importing BrainVISA white meshes for positions
        and MarsAtlas textures for areas
        ii) create transformation file from BV to head coordinates
        iii) create source spaces with cortical
        and subcortical dipoles,

    Parameters
    ----------
    subject : str
        Subject name
    database :
        To delete, database reference for trans file, useless from next version
    save : bool | True
        Allows to save source spaces and respective labels in the default directory

    Returns
    -------
    surf_src : instance of SourceSpace
        Cortical surface source spaces, lh and rh
    surf_labels : instance of Labels
        Cortical surfaces labels
    vol_src : instance of VolSourceSpace
        Subcortical volumes source space, lh and rh
    vol_labels : instance of Labels
        Subcortical volumes Labels
    """

    # if json_fname == 'default':
    #     read_dir = op.join(op.abspath(__package__), 'config')
    #     json_fname = op.join(read_dir, 'db_coords.json')
    #
    # database, project, db_mne, db_bv, db_fs = read_databases(json_fname)
    # raw_dir, prep_dir, trans_dir, mri_dir, src_dir, bem_dir, fwd_dir, hga_dir = read_directories(json_fname)

    ###########################################################################
    # -------------------------------------------------------------------------
    # BrainVISA anatomical data
    # -------------------------------------------------------------------------
    db_fs, db_bv, db_mne = read_db_coords(json_fname)
    if db_mne != None:
        _, _, trans_dir, _, src_dir, bem_dir, _, _ = mne_directories(db_mne)
        trans_dir = trans_dir.format(subject)
        src_dir = src_dir.format(subject)
        bem_dir = bem_dir.format(subject)

    assert decim in ['orig', '1K', '2K', '3K', '4K'], 'decim should be one of this string: orig, 1K, 2K, 3K, 4K'
    assert op.exists(bem_dir), 'bem_dir is not an existing folder'
    assert op.exists(trans_dir), 'trans_dir is not an existing folder'
    assert op.exists(src_dir), 'src_dir is not an existing folder'

    # BV decimated white meshes (cortical sources)
    # fname_surf_L = op.join(db_bv, project, subject, 't1mri', 'default_acquisition', 'default_analysis', 'segmentation',
    #                        'mesh', 'surface_analysis', '{0}_Lwhite_remeshed_hiphop.gii'.format(subject))
    #
    # fname_surf_R = op.join(db_bv, project, subject, 't1mri', 'default_acquisition', 'default_analysis', 'segmentation',
    #                        'mesh', 'surface_analysis', '{0}_Rwhite_remeshed_hiphop.gii'.format(subject))

    # BV texture (MarsAtlas labels) for decimated white meshes
    # (cortical sources)
    if decim == 'orig':
        # BV decimated white meshes (cortical sources)
        fname_surf_L = op.join(db_bv, subject, 't1mri', 'default_acquisition', 'default_analysis',
                               'segmentation', 'mesh', '{0}_Lwhite.gii'.format(subject))

        fname_surf_R = op.join(db_bv, subject, 't1mri', 'default_acquisition', 'default_analysis',
                               'segmentation', 'mesh', '{0}_Rwhite.gii'.format(subject))

        # BV texture (MarsAtlas labels) for decimated white meshes
        fname_tex_L = op.join(db_bv, subject, 't1mr', 'default_acquisition', 'default_analysis',
                              'segmentation', 'mesh', 'surface_analysis',
                              '{0}_Lwhite_parcels_marsAtlas.gii'.format(subject))

        fname_tex_R = op.join(db_bv, subject, 't1mr', 'default_acquisition', 'default_analysis',
                              'segmentation', 'mesh', 'surface_analysis',
                              '{0}_Rwhite_parcels_marsAtlas.gii'.format(subject))

    else:
        if not op.exists(op.join(db_bv, 'hiphop138-multiscale')):
            get_decimated(db_bv)

        # BV decimated white meshes (cortical sources)
        fname_surf_L = op.join(db_bv, subject, 't1mri', 'default_acquisition', 'default_analysis',
                               'segmentation', 'mesh', 'surface_analysis',
                               '{0}_Lwhite_remeshed_hiphop.gii'.format(subject))

        fname_surf_R = op.join(db_bv, subject, 't1mri', 'default_acquisition', 'default_analysis',
                               'segmentation', 'mesh', 'surface_analysis',
                               '{0}_Rwhite_remeshed_hiphop.gii'.format(subject))

        # BV texture (MarsAtlas labels) for decimated white meshes
        fname_tex_L = op.join(db_bv, 'hiphop138-multiscale', 'Decimated', decim,
                              'hiphop138_Lwhite_dec_{0}_parcels_marsAtlas.gii'.format(decim))

        fname_tex_R = op.join(db_bv, 'hiphop138-multiscale', 'Decimated', decim,
                              'hiphop138_Rwhite_dec_{0}_parcels_marsAtlas.gii'.format(decim))

    # Labelling xls file
    # fname_atlas = op.join(db_mne, project, 'marsatlas', 'MarsAtlas_BV_2015.xls')

    # Color palette (still used???)
    # fname_color = op.join(db_mne, project, 'marsatlas', 'MarsAtlas.ima')

    # MarsAtlas volume parcellation
    # fname_vol = op.join(db_bv, subject, 't1mri', 'default_acquisition', 'default_analysis', 'segmentation',
    #                     'mesh', 'surface_analysis', '{0}_parcellation.nii.gz'.format(subject))

    # -------------------------------------------------------------------------
    # Transformation files BV to FS
    # -------------------------------------------------------------------------

    # Referential file list
    # (3 transformation files to transform BV meshes to FS space)
    # fname_trans_ref = op.join(db_mne, project, 'referential', 'referential.txt')

    # This file contains the transformations
    trans_out = op.join(trans_dir, '{0}-trans.trm'.format(subject))
    # if trans_out is None:
    #     trans_out = op.join(db_bv, project, subject, 't1mri', 'default_acquisition', 'default_analysis',
    #                         'segmentation', 'mesh', '{0}-trans.trm'.format(subject))
    # elif type(trans_out) == str:
    #     trans_out = op.join(trans_out, '{0}-trans.trm'.format(subject))

    # name_lobe_vol = ['Subcortical']
    # ---------------------------------------------------------------------
    # Setting up the source space from BrainVISA results
    # ---------------------------------------------------------------------
    # http://martinos.org/mne/stable/manual/cookbook.html#source-localization
    # Create .trm file transformation from BrainVisa to FreeSurfer needed
    # for brain.py function for surface only
    create_trans(subject, db_fs, db_bv, trans_out)

    # Calculate cortical sources and MarsAtlas labels
    print('\n---------- Cortical sources ----------\n')
    surf_src, surf_labels = get_brain_surf_sources(subject, fname_surf_L, fname_surf_R, fname_tex_L, fname_tex_R,
                                                   trans_out)

    if save == True:
        # src_dir = op.join(db_mne, project, subject, 'src')
        # if not op.exists(src_dir):
        #     os.mkdir(src_dir)
        # print('\nSaving surface source space and labels in {0}'.format(src_dir))
        # mne.write_source_spaces(op.join(src_dir.format(subject), '{0}_surf-src.fif'.format(subject)), surf_src, overwrite=True)
        # for sl in surf_labels:
        #     mne.write_label(op.join(src_dir.format(subject), '{0}_surf-lab'.format(subject)), sl)
        # print('[done]')
        print('\nSaving surface source space and labels in {0}'.format(src_dir))
        mne.write_source_spaces(op.join(src_dir, '{0}_surf-src.fif'.format(subject)), surf_src, overwrite=True)
        for sl in surf_labels:
            mne.write_label(op.join(src_dir, '{0}_surf-lab'.format(subject)), sl)
        print('[done]')

    # Create BEM model if needed
    print('\nBEM model is needed for volume source space\n')
    if not check_bem(subject, bem_dir):
        print('BEM model not found... creating bem model')
        create_bem(subject, bem_dir, json_fname)

    print('\n---------- Subcortical sources ----------\n')

    vol_src, vol_labels = get_brain_vol_sources(subject, bem_dir, space=5., json_fname=json_fname)

    if save == True:
        print('Saving volume source space and labels in {0}'.format(src_dir))
        mne.write_source_spaces(op.join(src_dir, '{0}_vol-src.fif'.format(subject)), vol_src, overwrite=True)
        for vl in vol_labels:
            mne.write_label(op.join(src_dir, '{0}_vol-lab'.format(subject)), vl)
        print('[done]')
    #
    print('\n---------- Sources Completed ----------\n')

    return surf_src, surf_labels, vol_src, vol_labels


def get_brain_surf_sources(subject, fname_surf_L=None, fname_surf_R=None,
                           fname_tex_L=None, fname_tex_R=None, trans=False):
    """compute surface sources
    Parameters
    ----------
    subject : str
        The name of the subject
    fname_surf_L : None | str
        The filename of the surface of the left hemisphere
    fname_surf_R : None | str
        The filename of the surface of the right hemisphere
    fname_tex_L : None | str
        The filename of the texture surface of the right hemisphere
        The texture is used to select areas in the surface
    fname_tex_R : None | str
        The filename of the texture surface of the left hemisphere
    bad_areas : list of int
        Areas that will be excluded from selection
    trans : str | None
        The filename that contains transformation matrix for surface
    fname_atlas : str | None
        The filename of the area atlas
    fname_color : Brain surfer instance
        The filename of color atlas
    Returns
    -------
    surf_src : instance of mne.SourceSpace
        Surface source space
    surf_labels : instace of mne.Labels
        Surface MarsAtlas labels
    -------
    """

    list_hemi = ['lh', 'rh']

    fname_surf = [fname_surf_L, fname_surf_R]
    fname_tex = [fname_tex_L, fname_tex_R]

    print('\nBuilding surface areas.....')

    # Get surfaces
    surfaces = []
    surf_labels = []
    for hemi_surf, hemi_tex, hemi in zip(fname_surf, fname_tex, list_hemi):

        if hemi_surf is not None and hemi_tex is not None:

            # Create surface areas
            surface = get_surface(hemi_surf, subject=subject, hemi=hemi, trans=trans)
            labels_hemi = get_surface_labels(surface, texture=hemi_tex, subject=subject, hemi=hemi)

            # Delete WM (values of texture 0 and 42)
            bad_areas = [0, 42]
            if bad_areas is not None:
                # bad =
                labels_hemi = list(np.delete(labels_hemi, bad_areas, axis=0))


            # MNE accepts hemispheric labels as a single object that keeps the sum of all single labels
            labels_sum = []
            for l in labels_hemi:
                if type(labels_sum) == list:
                    labels_sum = l
                else:
                    labels_sum += l

            surfaces.append(surface)
            surf_labels.append(labels_sum)

    print('\nSet sources on MarsAtlas cortical areas')
    surf_src = SourceSpaces(surfaces)

    print('[done]')
    return surf_src, surf_labels


def get_brain_vol_sources(subject, bem_dir, space=5.0, json_fname='default'):
    """ Compute volume sources

    Parameters
    ----------
    subject : str
        The name of the subject
    fname_vol : None | str
        The filename of mri labelized
    name_lobe_vol : None | list of str | str
        Interest lobe names
    trans : str | None
        The filename that contains transformation matrix for surface
    fname_atlas : str | None
        The filename of the area atlas
    Returns
    -------
    vol_src : instance of mne.VolSourceSpace
        Volumetric source space of subcortical
    vol_labels: instance of mne.Labels
        Subcortical MarsAtlas labels
    -------
    """

    # if json_fname == 'default':
    #     read_dir = op.join(op.abspath(__package__), 'config')
    #     json_fname = op.join(read_dir, 'db_coords.json')

    print('build volume areas')

    # assert fname_vol is not None, "error, missing volume file"

    vol_src = get_volume(subject, bem_dir=bem_dir, pos=space, json_fname=json_fname)
    vol_labels = get_volume_labels(vol_src)

    labels_sum = []
    for l in vol_labels:
        if type(labels_sum) == list:
            labels_sum = l
        else:
            labels_sum += l
    vol_labels = [labels_sum.lh, labels_sum.rh]

    print('[done]')

    return vol_src, vol_labels


if __name__ == '__main__':
    subject = 'subject_01'
    create_source_models(subject, bem_dir=None, trans_dir=None, src_dir=None,
                         json_fname='default', decim='4K', save=True)