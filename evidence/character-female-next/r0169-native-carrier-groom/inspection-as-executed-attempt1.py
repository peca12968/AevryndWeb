"""One original-native identity/carrier check before any retired-map retry."""
from pathlib import Path
import bpy,numpy as np,json,time,datetime,hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
E=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158/evidence/character-female-next/r0169-native-carrier-groom');SRC=Path('C:/Users/USER/AppData/Local/Temp/Aevrynd-hair-editor-reference/hair.blend')
def arr(d,p,n,k=1):
 x=np.empty((n,k) if k>1 else n,'f4');d.foreach_get(p,x.ravel());return x
def roots(ob):
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());d=ev.data;P=arr(d.position_data,'vector',len(d.position_data),3);offset=np.array([x.first_point_index for x in d.curves]);W=P@np.array(ob.matrix_world)[:3,:3].T+np.array(ob.matrix_world.translation);return W,offset,ev
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
tick=time.time();assert sha(SRC)=='93aedaef061dc14618a0fcfad33c3df816fa755e8093381cbdfd0fd4c34527f5';bpy.ops.wm.open_mainfile(filepath=str(SRC));ob=bpy.data.objects['straight_hair_to_shoulder'];human=ob.data.surface;raw=arr(ob.data.position_data,'vector',len(ob.data.position_data),3);original=[]
for mod in ob.modifiers:
 fields={}
 for key in mod.keys():
  value=mod[key]
  if isinstance(value,bpy.types.ID):fields[key]={'name':value.name,'type':value.bl_rna.identifier}
  elif isinstance(value,(float,int,str,bool)):fields[key]=value
  else:fields[key]=str(value)
 original.append({'name':mod.name,'viewport':mod.show_viewport,'render':mod.show_render,'nodeGroup':mod.node_group.name if mod.type=='NODES' else None,'inputs':fields})
P,offset,ev=roots(ob);he=human.evaluated_get(bpy.context.evaluated_depsgraph_get());hm=he.to_mesh();hm.calc_loop_triangles();HV=np.array([human.matrix_world@v.co for v in hm.vertices]);HT=np.array([t.vertices for t in hm.loop_triangles]);tree=BVHTree.FromPolygons(HV.tolist(),HT.tolist(),all_triangles=True);gaps=np.array([tree.find_nearest(Vector(p))[3] for p in P[offset]]);surfaceAttributes=[(a.name,a.domain,a.data_type) for a in human.data.attributes];rest=human.data.attributes.get('rest_position');restReport=None
if rest:
 RP=arr(rest.data,'vector',len(rest.data),3);V=arr(human.data.vertices,'co',len(human.data.vertices),3);restReport={'restPoints':len(RP),'rawPoints':len(V),'rawVsRestMaximumM':float(np.linalg.norm(RP-V,axis=1).max()) if len(RP)==len(V) else None}
identity={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':str(SRC),'sourceSHA':sha(SRC),'actualSurface':human.name,'sourceCurves':len(ob.data.curves),'actualEvaluatedCurves':len(offset),'actualEvaluatedPoints':len(P),'actualOriginalFinalRootToEvaluatedHumanM':{'max':float(gaps.max()),'median':float(np.median(gaps)),'over1mm':int((gaps>.001).sum())},'actualOriginalRootBounds':[P[offset].min(0).tolist(),P[offset].max(0).tolist()],'sourceModifiers':original,'surfaceAttributes':surfaceAttributes,'sourceRestPositionAttribute':restReport,'surfaceModifiers':[{'name':m.name,'type':m.type,'viewport':m.show_viewport,'render':m.show_render} for m in human.modifiers],'sourceOriginalNativeGroupNodes':[]}
mod=next(m for m in ob.modifiers if m.name=='Surface Deform')
for node in mod.node_group.nodes:
 identity['sourceOriginalNativeGroupNodes'].append({'name':node.name,'type':node.bl_idname,'inputs':[{'name':x.name,'default':x.default_value.name if hasattr(x,'default_value') and isinstance(x.default_value,bpy.types.ID) else str(x.default_value) if hasattr(x,'default_value') else None,'linked':x.is_linked} for x in node.inputs]})
np.savez_compressed(E/'original-native-carrier-reference.npz',originalEvaluatedFibreWorld=P,originalCurveOffsets=offset,originalEvaluatedCarrierWorld=HV,originalEvaluatedCarrierTriangles=HT,originalRawGuideLocal=raw)
human.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear();(E/'original-native-carrier-identity.json').write_bytes((json.dumps(identity,indent=2)+'\n').encode());print('R169_ORIGINAL_NATIVE_IDENTITY_READ',identity['actualOriginalFinalRootToEvaluatedHumanM'],len(P),time.time()-tick,flush=True)
