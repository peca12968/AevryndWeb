from pathlib import Path
import bpy,numpy as np,json,hashlib,datetime
from mathutils import Vector
E=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158/evidence/character-female-next/r0167-artist-rooted-region')
SRC=Path('C:/Users/USER/AppData/Local/Temp/Aevrynd-hair-editor-reference/hair.blend')
assert hashlib.sha256(SRC.read_bytes()).hexdigest()=='93aedaef061dc14618a0fcfad33c3df816fa755e8093381cbdfd0fd4c34527f5'
bpy.ops.wm.open_mainfile(filepath=str(SRC));ob=bpy.data.objects['straight_hair_to_shoulder'];d=ob.data
P=np.empty(len(d.position_data)*3,'f4');d.position_data.foreach_get('vector',P);P=P.reshape(-1,3);W=np.array([ob.matrix_world@Vector(v) for v in P]);offset=np.array([x.first_point_index for x in d.curves]+[len(P)]);assert set(np.diff(offset))=={16};Q=W.reshape(-1,16,3)
surface=d.surface;mesh=surface.data;mesh.calc_loop_triangles();V=np.array([surface.matrix_world@v.co for v in mesh.vertices]);T=np.array([t.vertices for t in mesh.loop_triangles]);uv=np.empty(len(mesh.uv_layers.active.data)*2,'f4');mesh.uv_layers.active.data.foreach_get('uv',uv);loop=np.array([t.loops for t in mesh.loop_triangles]);sourceUV=np.empty(len(d.curves)*2,'f4');d.attributes['surface_uv_coordinate'].data.foreach_get('vector',sourceUV)
np.savez_compressed(E/'actual-cc0-complete-guide-reference.npz',guideWorld=Q,sourceSurfaceWorld=V,sourceSurfaceTriangles=T,triangleUV=uv.reshape(-1,2)[loop],sourceRootUV=sourceUV.reshape(-1,2))
out={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':str(SRC),'sourceSHA256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'object':ob.name,'surface':surface.name,'surfaceUV':d.surface_uv_map,'curves':len(Q),'stations':16,'rootBounds':[Q[:,0].min(0).tolist(),Q[:,0].max(0).tolist()],'wholeGuideBounds':[Q.min((0,1)).tolist(),Q.max((0,1)).tolist()],'attributes':[(a.name,a.domain,a.data_type) for a in d.attributes],'rootTipMidExamples':[{'id':i,'root':q[0].tolist(),'mid':q[7].tolist(),'tip':q[-1].tolist()} for i,q in enumerate(Q)],'sourceModifiersNotImported':True,'sourceCC0Author':'Tomáš Klecer','actualGuidePointReadCapabilityConfirmed':True}
(E/'actual-cc0-guide-inspection.json').write_bytes((json.dumps(out,indent=2)+'\n').encode());print('R167_ACTUAL_252_COMPLETE_GUIDE_DATA_READ',len(Q),out['rootBounds'],flush=True)
