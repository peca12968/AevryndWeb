"""Canonical CC0 topology/UV + exact supplied female morph; no addon code.

The original library is stored in Edit Mode. Commit its mesh/UV state before
using it; the separately supplied Default array is the declared canonical
basis. A missing UV buffer is not reconstructed from guessed coordinates.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib
R=Path(r'D:\Download\Aevrynd');D=R/'Reference/character/charmorph-vitruvian-cc0';E=R/'Evidence/character-female-next/r0057-coherent-foundation';OUT=D/'canonical-female-data.blend'
bpy.ops.wm.open_mainfile(filepath=str(D/'char.blend'));o=bpy.data.objects['cm_vitruvian'];bpy.context.view_layer.objects.active=o
if o.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
P=np.load(D/'Default.npy',allow_pickle=False);a=np.load(D/'Gender_Female.npz',allow_pickle=False);assert P.shape==(len(o.data.vertices),3)
o.data.vertices.foreach_set('co',P.astype('f4').ravel());o.shape_key_add(name='Basis');key=o.shape_key_add(name='AFN57_Supplied_Female_Morph');Q=P.copy();Q[a['idx']]+=a['delta'];key.data.foreach_set('co',Q.astype('f4').ravel());key.value=1
uv=o.data.uv_layers['VitruvianUV.UDIM'];assert len(uv.data)==len(o.data.loops);o.data.uv_layers.active=uv
systems=[]
for ps in o.particle_systems:
    s=ps.settings;systems.append({'name':ps.name,'type':s.type,'count':s.count,'children':s.child_type,'renderedChildren':s.rendered_child_count,'hairLength':s.hair_length,'hairStep':s.hair_step,'material':s.material,'rootRadius':s.root_radius,'tipRadius':s.tip_radius,'radiusScale':s.radius_scale,'particlesInFile':len(ps.particles)})
for other in list(bpy.data.objects):
    if other!=o:bpy.data.objects.remove(other,do_unlink=True)
for text in list(bpy.data.texts):bpy.data.texts.remove(text)
o.animation_data_clear();o['scope']='CC0 canonical body data and supplied female shape only. No imported addon, embedded rig script, animation or runtime qualification.'
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
row={'output':str(OUT),'sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),'vertices':len(P),'femaleHeadMaximumDisplacementM':float(np.linalg.norm(a['delta'][P[a['idx'],2]>1.48],axis=1).max()),'particleSystems':systems,
     'basisSHA256':hashlib.sha256((D/'Default.npy').read_bytes()).hexdigest(),'femaleMorphSHA256':hashlib.sha256((D/'Gender_Female.npz').read_bytes()).hexdigest(),'activeUV':uv.name,'removedEmbeddedTexts':True,'newFemaleControl':'AFN57_Supplied_Female_Morph'}
(E/'canonical-library.json').write_text(json.dumps(row,indent=2)+'\n',encoding='utf8');print('R57_CANONICAL_LIBRARY',json.dumps(row),flush=True)
