from pathlib import Path
import bpy,numpy as np,json
R=Path(__file__).resolve().parent
s=R.parent/'r0485-native-root-to-tip/female-next-r0485-native-groom-portable-UNACCEPTED.blend'
bpy.ops.wm.open_mainfile(filepath=str(s),load_ui=False,use_scripts=False)
o=bpy.data.objects['R485 complete hair | B'];p=np.empty((24831,80,3),dtype='f4');o.data.position_data.foreach_get('vector',p.ravel());r=p[:,0]
print('ROOT_QUANTILES',np.quantile(r,[0,.05,.25,.5,.75,.95,1],axis=0).tolist(),flush=True)
print('TRANSFORM',list(map(list,o.matrix_world)),flush=True)
print('ATTRS',[(a.name,a.data_type,a.domain) for a in o.data.attributes],flush=True)
for z in (1.45,1.48,1.51,1.54,1.56):
 m=r[np.abs(r[:,2]-z)<.002];print('SLICE',z,len(m),np.quantile(m,[0,.5,1],axis=0).tolist() if len(m) else [],flush=True)
print('MATERIALS',[m.name for m in o.data.materials],flush=True)
