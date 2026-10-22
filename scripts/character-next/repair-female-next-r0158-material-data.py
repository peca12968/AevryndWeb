"""Restore original Main material IDs and source authoring/shader attributes.
One geometry candidate, second complete saved state; first remains immutable.
"""
from pathlib import Path
import bpy,numpy as np,json,datetime,time,importlib.util
R=Path('D:/Download/Aevrynd');C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');M=C/'assets-source/aevrynd-character/female-next';E=C/'evidence/character-female-next/r0158-shared-native-skin';OUT=M/'r0158-source/aevrynd-female-next-r0158-b-preserved-material-data.blend'
sp=importlib.util.spec_from_file_location('r158repair',C/'scripts/character-next/build-female-next-r0158-shared-native-skin.py');h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);a=h.a
def save(n,x):h.save(n,x)
def main():
 tick=time.time();assert not OUT.exists();b=json.loads((E/'a-build-summary.json').read_text());assert a.a.sha(Path(b['output']))==b['sha256'];bpy.ops.wm.open_mainfile(filepath=b['output']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[b['actualSkin']];source=bpy.data.objects[b['actualPoseSource']];beforeGeom=[a.a.hasharray(x) for x in a.geometry(skin)];beforeUV=a.rawsig(skin)['uv'];z=np.load(E/'explicit-shared-skin-lineage.npz');keep=z['retainedSourceVertices'];mapping=z['sourceToNative'];ev=source.evaluated_get(bpy.context.evaluated_depsgraph_get());old=ev.to_mesh();new=skin.data;assert len(old.polygons)==len(new.polygons);order=np.empty(len(new.loops),'i4')
 for oldf,newf in zip(old.polygons,new.polygons):
  lookup={int(mapping[int(vi)]):oldf.loop_start+k for k,vi in enumerate(oldf.vertices)}
  for k,vi in enumerate(newf.vertices):order[newf.loop_start+k]=lookup[int(vi)]
 beforeSlots=[x.name if x else None for x in new.materials];materials=[]
 for mat in old.materials:
  actual=mat.original if mat is not None else None
  assert actual is None or not actual.is_evaluated,'Do not store temporary evaluated material IDs'
  materials.append(actual)
 new.materials.clear()
 for i,mat in enumerate(materials):
  new.materials.append(mat if mat is not None else next(x for x in materials if x is not None))
  if mat is None:new.materials[i]=None
 for slot in skin.material_slots:slot.link='DATA'
 # The old face material indices are the actual evaluated output assignment.
 for f,orig in zip(new.polygons,old.polygons):f.material_index=orig.material_index
 uvNames={u.name for u in old.uv_layers};skip={'position','.edge_verts','.corner_vert','.corner_edge','material_index','sharp_face','custom_normal','.custom_normal',*uvNames};copied=[];edgeFirst=None;edgeSourceMap=None
 for att in old.attributes:
  if att.name in skip or att.name.startswith('AFN157_'):continue
  if att.data_type not in ['FLOAT','INT','BOOLEAN','FLOAT_VECTOR','FLOAT_COLOR','BYTE_COLOR','FLOAT2']:continue
  prop,k=('vector',3) if att.data_type=='FLOAT_VECTOR' else ('color_srgb',4) if att.data_type=='BYTE_COLOR' else ('color',4) if att.data_type=='FLOAT_COLOR' else ('vector',2) if att.data_type=='FLOAT2' else ('value',1);typ='i4' if att.data_type=='INT' else 'bool' if att.data_type=='BOOLEAN' else 'f4';values=h.arr(att.data,prop,len(att.data),k,typ)
  if att.domain=='POINT':out=values[keep]
  elif att.domain=='CORNER':out=values[order]
  elif att.domain=='FACE':out=values
  elif att.domain=='EDGE':
   if edgeFirst is None:
    target={tuple(sorted(e.vertices)):e.index for e in new.edges};edgeFirst=np.full(len(new.edges),-1,'i4');edgeSourceMap=np.empty(len(old.edges),'i4')
    for e in old.edges:
     idx=target[tuple(sorted(mapping[list(e.vertices)]))];edgeSourceMap[e.index]=idx
     if edgeFirst[idx]<0:edgeFirst[idx]=e.index
    assert (edgeFirst>=0).all()
   if att.data_type=='BOOLEAN':
    out=np.zeros(len(new.edges),bool);np.logical_or.at(out,edgeSourceMap,values)
   else:out=values[edgeFirst]
  else:continue
  dst=new.attributes.get(att.name)
  if dst is None:dst=new.attributes.new(att.name,att.data_type,att.domain)
  assert dst.domain==att.domain and dst.data_type==att.data_type;dst.data.foreach_set(prop,out.ravel());got=h.arr(dst.data,prop,len(dst.data),k,typ);assert np.array_equal(got,out),att.name;copied.append({'name':att.name,'domain':att.domain,'type':att.data_type,'elements':len(out),'mappedValuesExact':True})
 # Preserve source UV layer roles as well; the first hypothesis was falsified:
 # A and source already had identical roles, so this is not called the cause.
 for u in old.uv_layers:
  dst=new.uv_layers[u.name];dst.active_render=u.active_render;dst.active_clone=u.active_clone
 new.uv_layers.active_index=old.uv_layers.active_index;actualSlots=[m.name if m else None for m in new.materials];ev.to_mesh_clear();new.update();skin.update_tag(refresh={'DATA'});bpy.context.view_layer.update();assert beforeGeom==[a.a.hasharray(x) for x in a.geometry(skin)] and beforeUV==a.rawsig(skin)['uv'];save('material-and-data-preservation-repair.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalStartedUTC':'2026-10-22T09:51:48+00:00','sourceStateAUnchanged':b,'sameOneGeometryCandidateSecondSavedState':True,'uvActiveRoleHypothesisFalsified':True,'reopenedADataMaterialSlots':beforeSlots,'restoredOriginalMainMaterialSlots':actualSlots,'evaluatedTemporaryMaterialsNotStored':True,'sourceShaderAndAuthoringAttributesRestored':copied,'transientAFN157InputFieldsRemainOnPreservedSourceOnly':True,'nativeGeometryAndAllUVArraysUnchanged':True,'originalPaletteLightingExposureNotAdjusted':True,'noSourceContactsOrAcceptanceWaived':True});bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=True);save('b-build-summary.json',dict(b,source=b['output'],output=str(OUT),engineAlias=str(R/'engine/assets/characters/female-next/source/r0158-source'/OUT.name),sha256=a.a.sha(OUT),bytes=OUT.stat().st_size,sameOneGeometryCandidateSecondSavedState=True));a.b.u.v.E=E;views=[]
 for f,view,tag in [(11,'face','b-shared-closed'),(11,'body-face','b-shared-closed'),(1,'face','b-shared-neutral'),(9,'face','b-shared-half')]:
  s.frame_set(f);bpy.context.view_layer.update();_=a.geometry(skin)
  for name in h.h.h.h.ATTACH:_=a.geometry(bpy.data.objects[name])
  control=a.b.u.v.image(tag,view);control.update(frame=f,blink=[float(rig[x]) for x in ['blink_L','blink_R']] if (rig:=bpy.data.objects[b['actualRig']]) else []);views.append(control);save('b-actual-view-controls.json',views)
 s.frame_set(1);bpy.context.view_layer.update();print('R158_B_ORIGINAL_MATERIAL_DATA_RESTORED_FULL_HEAD_BODY_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
