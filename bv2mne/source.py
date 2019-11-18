import numpy as np

import mne
from mne import SourceSpaces

from directories import *

from bv2mne.surface import get_surface, get_surface_labels
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
    # mne_dir = op.join(db_mne, project)

    # BV decimated white meshes (cortical sources)
    fname_surf_L = op.join(db_bv, project, subject, 't1mri', 'default_acquisition', 'default_analysis', 'segmentation',
                           'mesh', 'surface_analysis', '{0}_Lwhite_remeshed_hiphop.gii'.format(subject))

    fname_surf_R = op.join(db_bv, project, subject, 't1mri', 'default_acquisition', 'default_analysis', 'segmentation',
                           'mesh', 'surface_analysis', '{0}_Rwhite_remeshed_hiphop.gii'.format(subject))

    # BV texture (MarsAtlas labels) for decimated white meshes
    # (cortical sources)
    fname_tex_L = op.join(db_bv, 'hiphop138-multiscale', 'Decimated', '4K',
                          'hiphop138_Lwhite_dec_4K_parcels_marsAtlas.gii')

    fname_tex_R = op.join(db_bv, 'hiphop138-multiscale', 'Decimated', '4K',
                          'hiphop138_Rwhite_dec_4K_parcels_marsAtlas.gii')

    # MarsAtlas labels for each texture
    # fname_atlas = os.path.join(bv_dir,
    #    'hiphop138-multiscale/marsAtlasRegions.xlsx')
    # not yet handled (missing subcortical labels),
    # the old MarsAtlas_BV_2015.xls is used)

    # Labelling xls file
    fname_atlas = op.join(db_mne, project, 'marsatlas', 'MarsAtlas_BV_2015.xls')

    # Color palette (still used???)
    fname_color = op.join(db_mne, project, 'marsatlas', 'MarsAtlas.ima')

    # MarsAtlas volume parcellation
    fname_vol = op.join(db_bv, project, subject, 't1mri', 'default_acquisition', 'default_analysis', 'segmentation',
                        'mesh', 'surface_analysis', '{0}_parcellation.nii.gz'.format(subject))

    # -------------------------------------------------------------------------
    # Transformation files BV to FS
    # -------------------------------------------------------------------------

    # Referential file list
    # (4 transformation files to transform BV meshes to FS space)
    fname_trans_ref = op.join(db_mne, project, 'referential', 'referential.txt')

    # This file contains the transformations for subject_01
    fname_trans_out = op.join(db_mne, project, subject, 'ref', '{0}-trans.trm'.format(subject))

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
    surf_src, surf_labels = get_brain_surf_sources(subject, fname_surf_L, fname_surf_R, fname_tex_L, fname_tex_R, None,
                                                  fname_trans_out, fname_atlas, fname_color)

    if save == True:
        print('Saving surface source space and labels.....')
        mne.write_source_spaces(op.join(src_dir.format(subject), '{0}_surf-src.fif'.format(subject)), surf_src, overwrite=True)
        for sl in surf_labels:
            mne.write_label(op.join(src_dir.format(subject), '{0}_surf-lab'.format(subject)), sl)
        print('[done]')

    print('\n------------ Subcortical soures----------\n')
    # vol_src = get_volume(subject)
    vol_src, vol_labels = get_brain_vol_sources(subject, fname_vol, name_lobe_vol, fname_trans_out, fname_atlas, space=5)
    #
    if save == True:
        print('Saving volume source space and labels.....')
        mne.write_source_spaces(op.join(src_dir.format(subject), '{0}_vol-src.fif'.format(subject)), vol_src, overwrite=True)
        for vl in vol_labels:
            mne.write_label(op.join(src_dir.format(subject), '{0}_vol-lab'.format(subject)), vl)
        print('[done]')
    #
    print('\n------------ Sources Completed ----------\n')

    # vol_src, vol_labels = 0, 0
    # return src_surf, src_vol, surfaces, volumes
    return surf_src, surf_labels, vol_src, vol_labels


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

    print('Building surface areas.....')

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
                # bad =
                labels_hemi = list(np.delete(labels_hemi, bad_areas, axis=0))


            # MNE accepts hemispheric labels as a single object that keeps the sum of all single labels
            # That normlly should be really helpful... but maybe in this case is better to keep them separate.
            labels_sum = []
            for l in labels_hemi:
                if type(labels_sum) == list:
                    labels_sum = l
                else:
                    labels_sum += l


            surfaces.append(surface)
            # surf_labels.append(labels_hemi)
            surf_labels.append(labels_sum)


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
    # list_hemi = ['lh', 'rh']

    # get volume
    # volumes = []
    # vol_labels = []
    # for hemi in list_hemi:
        # cour_volume = get_volume(fname_vol, fname_atlas, name_lobe_vol,
        #                          subject, hemi, reduce_volume=True)
    vol_src = get_volume(subject, pos=5.0)
    vol_labels = get_volume_labels(vol_src)
    # volumes.append(cour_volume)
    # vol_labels.append(cour_labels)
    #
    labels_sum = []
    for l in vol_labels:
        if type(labels_sum) == list:
            labels_sum = l
        else:
            labels_sum += l
    vol_labels = [labels_sum.lh, labels_sum.rh]

    # compute also sources
    # volumes = create_param_dict(volumes)
    # src_vol = [get_vol_src(volumes[hemi], space=space) for hemi in list_hemi]
    # vol_src = mne.SourceSpaces(volumes)

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


def create_forward_models(subject, srcs, session, event):

    # mne_dir = os.path.join(db_mne, project)

    # File to align coordinate frames meg2mri computed using mne analyze
    # (computed with interactive gui)
    fname_trans = op.join(trans_dir.format(subject), '{0}-trans.fif'.format(subject))

    # MEG Epoched data to recover position of channels
    fname_event = op.join(prep_dir.format(subject, session), '{0}_{1}-epo.fif'.format(subject, event))

    epochs_event = mne.read_epochs(fname_event)

    # Forward models computed with the old version of BV2MNE
    # fwd_cortex = os.path.join(
    #   mne_dir, '{0}/fwd/{0}-singleshell-cortex-fwd.fif'.format(subject))

    # Computing the single-shell forward solution
    # using raw data for each session
    print('\n--------- Forward Model for cortical sources-------------\n')

    # Forward model for cortical sources
    # (fix the source orientation normal to cortical surface)
    fwd_cortex_gen = forward_model(subject, epochs_event, fname_trans, srcs,
                                   force_fixed=True, name='singleshell-cortex')

    # print('\n-------- Forward Model for subcortical soures------------\n')
    # # Forward model for subcortical sources (no fixed orientation)
    # fwd_subcort_gen = forward_model(
    #     subject, epochs_event, fname_trans, srcs[1], op.join(db_mne, project),
    #     force_fixed=False, name='singleshell-subcort')
    #
    # print('\n--------- Forward Models Completed ----------------------\n')
    #
    # return [fwd_cortex_gen, fwd_subcort_gen]
    return fwd_cortex_gen


def forward_model(subject, raw, fname_trans, src,
                  force_fixed=False, name='single-shell'):
    """construct forward model

    Parameters
    ----------
    subject : str
        The name of subject
    raw : instance of rawBTI
        functionnal data
    fname_trans : str
        The filename of transformation matrix
    src : instance of SourceSpaces | list
        Sources of each interest hemisphere
    subjects_dir : str
        The subjects directory
    force_fixed: Boolean
        Force fixed source orientation mode
    name : str
        Use to save output

    Returns
    -------
    fwd : instance of Forward
    -------
    Author : Alexandre Fabre
    """
    # files to save step
    fname_bem_model = op.join(bem_dir.format(subject), '{0}-{1}-bem.fif'.format(subject, name))
    fname_bem_sol = op.join(bem_dir.format(subject), '{0}-{1}-bem-sol.fif'.format(subject, name))
    fname_fwd = op.join(fwd_dir.format(subject), '{0}-{1}-fwd.fif'.format(subject, name))

    # Make bem model: single-shell model. Depends on anatomy only.
    model = mne.make_bem_model(subject, conductivity=[0.3], subjects_dir=op.join(db_mne, project))
    mne.write_bem_surfaces(fname_bem_model, model)

    # Make bem solution. Depends on anatomy only.
    bem_sol = mne.make_bem_solution(model)
    mne.write_bem_solution(fname_bem_sol, bem_sol)

    # bem_sol=mne.read_bem_solution(fname_bem_sol)

    #if len(src) == 2:
            ## gather sources each the two hemispheres
            #lh_src, rh_src = src
            #src = lh_src + rh_src

    # Compute forward, commonly referred to as the gain or leadfield matrix.
    fwd = mne.make_forward_solution(info=raw.info, trans=fname_trans, src=src, bem=bem_sol, mindist=0.0)

    # Set orientation of cortical sources to surface normals
    if force_fixed:
        # Surface normal
        fwd = mne.forward.convert_forward_solution(fwd, surf_ori=True, force_fixed=True)

    # Save fwd model
    mne.write_forward_solution(fname_fwd, fwd, overwrite=True)

    return fwd