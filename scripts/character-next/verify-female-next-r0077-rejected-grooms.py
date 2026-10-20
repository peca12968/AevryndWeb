"""Minimal saved-source/dependency checks for visually rejected complete grooms.
No expansion into physics, runtime or expensive failed-candidate validation.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0077-guided-tip-groom';E76=E.parent/'r0076-proximal-crowns'
def module(n,f):
 s=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
v=module('verify77native','verify-female-next-r0076-crowns.py');q=v.q;m=module('verify77render','build-female-next-r0074-oral-controls.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def hair(o):
 d=o.data;p=q.arr(d.position_data,'vector',len(d.position_data),3).copy();rr=q.arr(d.attributes['radius'].data,'value',len(p)).copy();counts=np.array([c.points_length for c in d.curves]);return p,rr,counts

def main():
 tick=time.time();a=q.read(E/'a-build-summary.json');assert sha(Path(a['source']))==a['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=a['source']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();names=list(q.read(E.parent/'r0060-ocular-assembly/b-build-summary.json')['visibleComponents'].values());native={n:v.signature(bpy.data.objects[n]) for n in names};materials={o.name:m.m.k.f.v.v32.material_signature(o) for o in bpy.data.materials if o.use_nodes};lights=m.q.lights();oldhair={n:hair(bpy.data.objects[n]) for n in ('AFN68_MAIN_RENDER_CURVES','AFN68_FLYAWAY_RENDER_CURVES')};root=q.hair(bpy.data.objects['AFN68_MAIN_RENDER_CURVES']).copy();dental={n:q.arr(bpy.data.objects[n].data.vertices,'co',len(bpy.data.objects[n].data.vertices),3).copy() for n in ('AFN74_UPPER_TEETH_RIGID','AFN74_LOWER_TEETH_RIGID')};results=[]
 for tag in ('a','b'):
  ref=q.read(E/(tag+'-build-summary.json'));assert sha(Path(ref['output']))==ref['outputSha256'];bpy.ops.wm.open_mainfile(filepath=ref['output']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();assert {n:v.signature(bpy.data.objects[n]) for n in names}==native;assert {n:m.m.k.f.v.v32.material_signature(bpy.data.materials[n]) for n in materials}==materials;assert m.q.lights()==lights
  for n,p in dental.items():assert np.array_equal(q.arr(bpy.data.objects[n].data.vertices,'co',len(p),3),p)
  o=bpy.data.objects['AFN68_MAIN_RENDER_CURVES'];p,rr,counts=hair(o);old,oldrr,oldcounts=oldhair[o.name];assert np.array_equal(counts,oldcounts) and np.array_equal(rr,oldrr);z=np.load(E/(tag+'-groom-lineage.npz'));assert np.array_equal(p,z['outputLocal']) and np.array_equal(old,z['sourceLocal']);pins=np.unique(z['pinnedPointIDs']);assert np.array_equal(p[pins],old[pins]);starts=np.r_[0,np.cumsum(counts)[:-1]];A=np.array(o.matrix_world);pw=p.astype('f8')@A[:3,:3].T+A[:3,3];ow=old.astype('f8')@A[:3,:3].T+A[:3,3];mask=np.ones(len(p)-1,bool);mask[np.cumsum(counts)[:-1]-1]=False;edgeerror=float(np.abs(np.linalg.norm(np.diff(pw,axis=0)[mask],axis=1)-np.linalg.norm(np.diff(ow,axis=0)[mask],axis=1)).max());assert edgeerror<1e-6;actual=q.hair(o);rooterr=float(np.linalg.norm(actual[starts]-root[starts],axis=1).max());assert rooterr<1e-6
  for name in ('AFN68_FLYAWAY_RENDER_CURVES',):
   current=hair(bpy.data.objects[name]);assert all(np.array_equal(x,y) for x,y in zip(current,oldhair[name]))
  assert not bpy.data.libraries;images=[]
  for im in bpy.data.images:
   if im.source=='FILE' and not im.packed_file:
    path=Path(bpy.path.abspath(im.filepath));assert im.filepath.startswith('//') and path.is_file();images.append({'relative':im.filepath,'sha256':sha(path)})
  assert len(images)==15;row={'tag':tag,'source':ref['output'],'sha256':ref['outputSha256'],'status':'PASS_SAVED_SOURCE_SCOPE_VISUALLY_REJECTED','allFiveNativeCagesAllKeysWeightsUVAndDriversExact':True,'dentalRestVerticesExact':True,'materialsAndLightsExact':True,'radiiAndFlyawayGeometryExact':True,'exactPinnedPoints':len(pins),'actualNeutralRootMaximumDifferenceM':rooterr,'maximumNativeControlPolygonEdgeLengthErrorM':edgeerror,'controlPolygonLengthIsNotTrueSplineArcLength':True,'externalTextures':images,'newContactMotionOrRuntimeAcceptance':False};results.append(row);print('R77_REJECTED_SAVED_READBACK',tag,rooterr,edgeerror,flush=True)
 (E/'rejected-source-readback.json').write_text(json.dumps({'status':'PASS_REJECTED_SOURCE_PRESERVATION_ONLY','candidates':results,'noBroadContactMotionEngineExpansionForRejectedGrooms':True,'seconds':time.time()-tick},indent=2)+'\n',encoding='utf-8')
 # Only the pending r76 rest crown sculpt diagnostic: unchanged operation
 # reuses its independent six-pose readback instead of rerendering a movie.
 render=module('dental76close','render-female-next-r0075-evidence.py');render.E=E76;ref=q.read(E76/'a-build-summary.json');assert sha(Path(ref['output']))==ref['outputSha256'];render.dental_only(ref,'r76');print('R76_DENTAL_DIAGNOSTIC_AND_R77_MINIMAL_READBACK_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
