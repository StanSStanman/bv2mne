import os

import numpy as np

import mne
from mne import SourceSpaces
from mne import (make_bem_model, write_bem_surfaces, make_bem_solution,
                 write_bem_solution, make_forward_solution,
                 write_forward_solution, convert_forward_solution)

from directories import *

from bv2mne.surface import get_surface, get_surface_labels
#
from bv2mne.volume import get_volume, get_volume_labels
from bv2mne.utils import create_trans, create_param_dict#, create_trans, save_srcs

# from bv2mne.surface import get_surface_sources
# from bv2mne.volume import get_volume_sources


def create_source_models(subject, database=database, save=False):
    '''
    Pipeline for
    i) importing BrainVISA white meshes for positions
    and MarsAtlas textures for areas
    ii) create transformation file from BV to head coordinates
    iii) create source spaces src with cortical
    and subcortical dipoles,
    '''

    ###########################################################################
    # -------------------------------------------------------------------------
    # BrainVISA anatomical data
    # -------------------------------------------------------------------------

    # bv_dir = os.path.join(database, "db_brainvisa")
    mne_dir = os.path.join(db_mne, project)

    # BV decimated white meshes (cortical sources)
    fname_surf_L = os.path.join(db_bv, project,'{0}/t1mri/default_acquisition/default_analysis/segmentation/\
mesh/surface_analysis/{0}_Lwhite_remeshed_hiphop.gii'.format(subject))

    fname_surf_R = os.path.join(db_bv, project, '{0}/t1mri/default_acquisition/default_analysis/segmentation/\
mesh/surface_analysis/{0}_Rwhite_remeshed_hiphop.gii'.format(subject))

    # BV texture (MarsAtlas labels) for decimated white meshes
    # (cortical sources)
    fname_tex_L = os.path.join(db_bv, 'hiphop138-multiscale/Decimated/4K',
                               'hiphop138_Lwhite_dec_4K_parcels_marsAtlas.gii')

    fname_tex_R = os.path.join(db_bv, 'hiphop138-multiscale/Decimated/4K/',
                               'hiphop138_Rwhite_dec_4K_parcels_marsAtlas.gii')

    # MarsAtlas labels for each texture
    # fname_atlas = os.path.join(bv_dir,
    #    'hiphop138-multiscale/marsAtlasRegions.xlsx')
    # not yet handled (missing subcortical labels),
    # the old MarsAtlas_BV_2015.xls is used)

    # Labelling xls file
    fname_atlas = os.path.join(mne_dir, 'marsatlas/MarsAtlas_BV_2015.xls')

    # Color palette (still used???)
    fname_color = os.path.join(mne_dir, 'marsatlas/MarsAtlas.ima')

    # MarsAtlas volume parcellation
    fname_vol = os.path.join(db_bv, project, '{0}/t1mri/default_acquisition/default_analysis/segmentation/\
mesh/surface_analysis/{0}_parcellation.nii.gz'.format(subject))

    # -------------------------------------------------------------------------
    # Transformation files BV to FS
    # -------------------------------------------------------------------------

    # Referential file list
    # (4 transformation files to transform BV meshes to FS space)
    fname_trans_ref = os.path.join(mne_dir, 'referential/referential.txt')

    # This file contains the transformations for subject_01
    fname_trans_out = os.path.join(mne_dir, '{0}/ref/{0}-trans.trm'.format(subject))

    name_lobe_vol = ['Subcortical']
    # ---------------------------------------------------------------------
    # Setting up the source space from BrainVISA results
    # ---------------------------------------------------------------------
    # http://martinos.org/mne/stable/manual/cookbook.html#source-localization
    # Create .trm file transformation from BrainVisa to FreeSurfer needed
    # for brain.py function for surface only
    create_trans(subject, database, fname_trans_ref, fname_trans_out)

    # Calculate cortical sources and MarsAtlas labels
    print('\n------------ Cortical soures-------------\n')
    surf_src, surf_label = get_brain_surf_sources(subject, fname_surf_L, fname_surf_R, fname_tex_L, fname_tex_R, None,
                                                  fname_trans_out, fname_atlas, fname_color)

    # print('\n------------ Subcortical soures----------\n')
    vol_src, vol_labels = get_brain_vol_sources(subject, fname_vol, name_lobe_vol, fname_trans_out, fname_atlas, space=5)
    #
    # if save == True:
    #     save_srcs(subject, [src_surf, src_vol])
    #
    print('\n------------ Sources Completed ----------\n')

    # return src_surf, src_vol, surfaces, volumes
    return surf_src, surf_label, vol_src, vol_labels


def get_brain_surf_sources(subject, fname_surf_L=None, fname_surf_R=None,
                           fname_tex_L=None, fname_tex_R=None, bad_areas=None,
                           trans=False, fname_atlas=None, fname_color=None):
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
    figure : Figure object
    -------
    Author : Alexandre Fabre / modif David Meunier
    """

    list_hemi = ['lh', 'rh']

    fname_surf = [fname_surf_L, fname_surf_R]
    fname_tex = [fname_tex_L, fname_tex_R]

    print('build surface areas')

    # Get surfaces
    surfaces = []
    surf_labels = []
    for hemi_surf, hemi_tex, hemi in zip(fname_surf, fname_tex, list_hemi):

        if hemi_surf is not None and hemi_tex is not None:

            # Create surface areas
            surface = get_surface(hemi_surf, subject=subject, hemi=hemi, trans=trans)
            labels_hemi = get_surface_labels(surface, texture=hemi_tex, hemi=hemi, subject=subject,
                                           fname_atlas=fname_atlas, fname_color=fname_color)

            # Delete WM (values of texture 0 and 42)
            bad_areas = [0, 42]
            if bad_areas is not None:
                labels_hemi = list(np.delete(labels_hemi, bad_areas, axis=0))


            surfaces.append(surface)
            surf_labels.append(labels_hemi)

    print('Set sources on MarsAtlas cortical areas')
    surf_src = SourceSpaces(surfaces)

    print('[done]')
    return surf_src, surf_labels


def get_brain_vol_sources(subject, fname_vol=None, name_lobe_vol='Subcortical',
                          trans=False, fname_atlas=None, space=5):
    """compute volume sources
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
    figure : Figure object
    -------
    Author : Alexandre Fabre / modif David Meunier
    """

    print('build volume areas')

    assert fname_vol is not None, "error , missing volume file"
    list_hemi = ['lh', 'rh']

    # get volume
    volumes = []
    vol_labels = []
    for hemi in list_hemi:
        cour_volume = get_volume(fname_vol, fname_atlas, name_lobe_vol,
                                 subject, hemi, reduce_volume=True)
        cour_labels = get_volume_labels(cour_volume)
        volumes.append(cour_volume)
        vol_labels.append(cour_labels)

    # compute also sources
    # volumes = create_param_dict(volumes)
    # src_vol = [get_vol_src(volumes[hemi], space=space) for hemi in list_hemi]
    vol_src = mne.SourceSpaces(volumes)

    print('[done]')

    return vol_src, vol_labels


# def get_vol_src(volumes, space=5):
#     """get brain sources for each volum structure
#     Parameters
#     ----------
#     volumes : list of Volume object
#     space : float
#         Distance between sources
#
#     Returns
#     -------
#     src : SourceSpaces  object
#     -------
#     Author : Alexandre Fabre / Modif David Meunier
#     """
#
#     print('Set sources in MarsAtlas subcortical areas')
#
#     src = []
#     for volume in volumes:
#         print('    ' + volume['name'] + '-' + volume['hemi'])
#         cour_src = get_volume_sources(volume, space)
#         src.append(cour_src)
#
#     src = SourceSpaces(src)
#
#     print('[done]')
#     return src
