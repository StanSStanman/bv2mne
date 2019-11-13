from directories import *
import numpy as np
import mne
from nibabel import gifti
import visbrain
from visbrain.objects import *
from vispy.visuals.transforms import MatrixTransform

src = mne.read_source_spaces('D:\\Databases\\toy_db\\db_mne\\meg_causal\\subject_02\\src\\subject_02_cortical')
rr = src[0]['rr']

fname_mesh = op.join(db_bv, 'hiphop138-multiscale', 'Decimated', '4K', 'hiphop138_Lwhite_dec_4K_parcels_marsAtlas.gii')
giftiImage = gifti.giftiio.read(fname_mesh)
values = giftiImage.darrays[0].data
parcels, counts = np.unique(values, return_counts=True)

trans = mne.read_trans('D:\\Databases\\toy_db\\db_mne\\meg_causal\\subject_02\\trans\\subject_02-trans.fif')
trans = trans['trans']

mt = MatrixTransform(trans)
rr = mt.map(rr*1000)[:, 0:-1]

cmap = np.zeros(rr.shape)
col = np.vstack((np.linspace(1,0,len(parcels)), np.linspace(0,1,len(parcels)), np.roll(np.linspace(1,0,len(parcels)), 21))).T
for p in parcels:
    cmap[values == p] = col[parcels == p]

se = SceneObj(bgcolor='black')
brain = BrainObj('D:\\Databases\\toy_db\\db_mne\\meg_causal\\subject_02\\surf\\subject_02_Lwhite.gii')
src = SourceObj('coords', rr, color=cmap)
se.add_to_subplot(brain)
se.add_to_subplot(src)
se.preview()