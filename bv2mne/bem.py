import mne

from directories import *

def create_bem(subject, name='single-shell'):

    fname_bem_model = op.join(bem_dir.format(subject), '{0}-{1}-bem.fif'.format(subject, name))
    fname_bem_sol = op.join(bem_dir.format(subject), '{0}-{1}-bem-sol.fif'.format(subject, name))

    # Make bem model: single-shell model. Depends on anatomy only.
    model = mne.make_bem_model(subject, ico=None, conductivity=[0.3], subjects_dir=op.join(db_mne, project))
    mne.write_bem_surfaces(fname_bem_model, model)

    # Make bem solution. Depends on anatomy only.
    bem_sol = mne.make_bem_solution(model)
    mne.write_bem_solution(fname_bem_sol, bem_sol)

    return