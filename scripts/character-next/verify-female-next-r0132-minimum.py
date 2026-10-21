"""Independent whole source reopen, actual displayed edits and exact restoration."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0132-anatomical-volume-groom'
sp=importlib.util.spec_from_file_location('r132verify',Path(__file__).with_name('build-female-next-r0116-native-eye-character.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b;q=a.q
def main():
 tick=time.time();s=json.loads((E/'a-build-summary.json').read_text('utf-8'));src=Path(s['output']);assert a.sha(src)==s['sha256'];bpy.ops.wm.open_mainfile(filepath=str(src));skin=bpy.data.objects['AFN126_COMPLETE_WOMAN_BODY_AND_ARTIST_HEAD'];hair=bpy.data.objects[s['hairObject']];carrier=bpy.data.objects[s['carrierObject']];lat=bpy.data.objects[s['latticeObject']];bpy.context.view_layer.update();protected=a.protected();line=np.load(E/'anatomical-volume-lineage.npz');before=q.hair(hair).copy();_,W,T=b.u.b.geom(skin);W=W.copy();T=T.copy();assert [a.hasharray(W),a.hasharray(T)]==s['currentSkinHashes'];counts=np.array([c.points_length for c in hair.data.curves]);assert np.array_equal(counts,line['sourceCounts']);assert np.linalg.norm(before-line['mappedWorld'],axis=1).max()<3e-6;r=q.arr(hair.data.attributes['radius'].data,'value',len(before));ops={}
 def raw(o):return q.arr(o.data.vertices,'co',len(o.data.vertices),3)
 def put(o,V):o.data.vertices.foreach_set('co',V.ravel());o.data.update();bpy.context.view_layer.update()
 V=raw(carrier);edit=V.copy();j=int(counts[0]-1);edit[j,1]+=.001;put(carrier,edit);d=np.linalg.norm(q.hair(hair)-before,axis=1);ops['actualFreeSourcePathPointEdit']={'point':j,'requestedM':.001,'visibleHairMaxM':float(d.max()),'pointsAbove1um':int((d>1e-6).sum())};assert d.max()>.0001;put(carrier,V);assert np.array_equal(q.hair(hair),before)
 C=np.array([tuple(p.co_deform) for p in lat.data.points]);k=int(line['activeControls'][len(line['activeControls'])//2]);co=C[k].copy();co[0]+=.001/lat.scale.x;lat.data.points[k].co_deform=co;lat.data.update_tag();bpy.context.view_layer.update();d=np.linalg.norm(q.hair(hair)-before,axis=1);ops['actualNativeVolumeControlEdit']={'point':k,'requestedControlWorldM':.001,'visibleHairMaxM':float(d.max()),'pointsAbove1um':int((d>1e-6).sum())};assert d.max()>1e-6;lat.data.points[k].co_deform=C[k];lat.data.update_tag();bpy.context.view_layer.update();assert np.array_equal(q.hair(hair),before)
 V=raw(skin);edit=V.copy();j=int(s['anatomicalLandmarks'][0]['targetActualSkinVertex']);edit[j,2]+=.0002;put(skin,edit);d=np.linalg.norm(q.hair(hair)-before,axis=1);ops['actualCurrentVisibleSkinEdit']={'point':j,'requestedM':.0002,'visibleHairMaxM':float(d.max()),'noLiveCurrentScalpTrackingAuthored':True};put(skin,V);assert np.array_equal(q.hair(hair),before);_,WW,TT=b.u.b.geom(skin);assert np.array_equal(WW,W) and np.array_equal(TT,T) and protected==a.protected();assert np.array_equal(r,q.arr(hair.data.attributes['radius'].data,'value',len(before)))
 rays=[]
 for ob in bpy.context.scene.objects:
  if ob.type!='MESH' or ob.hide_render:continue
  _,VV,FF=b.u.b.geom(ob)
  if not len(FF):continue
  tree=BVHTree.FromPolygons(VV.tolist(),FF.tolist(),all_triangles=True)
  for z in [1.50,1.52,1.54]:
   co,no,fi,dist=tree.ray_cast(Vector((0,.40,z)),Vector((0,-1,0)),.6)
   if co is not None:rays.append({'object':ob.name,'rayZ':z,'hit':list(co),'distance':dist,'materialNames':[m.name if m else None for m in ob.data.materials]})
 textures=[]
 for im in bpy.data.images:
  if im.source=='FILE' and not im.packed_file and im.filepath:
   p=Path(bpy.path.abspath(im.filepath));assert p.is_file();textures.append({'relative':im.filepath,'absolute':str(p),'bytes':p.stat().st_size,'sha256':a.sha(p)})
 assert a.sha(src)==s['sha256'];result={'source':str(src),'sha256':s['sha256'],'bytes':src.stat().st_size,'independentlyReopened':True,'actualVisibleHairCountsAndPointsRecovered':True,'curves':len(counts),'points':len(before),'operations':ops,'actualSkinCarrierLatticeHairAndRadiiRestoredExactly':True,'oldHiddenRollbackExact':True,'allReferencedExternalTextures':textures,'diagnosticBackMeshRaysOnlyNotHairOccupancyOrContactProof':rays,'completeUsableHairstyleOperationAccepted':False,'naturalMotionFiniteSelfContinuousContactAndRuntimeAccepted':False,'seconds':time.time()-tick};(E/'minimum-saved-volume-readback.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('R132_INDEPENDENT_VOLUME_REOPEN_VISIBLE_EDITS_AND_EXACT_RESTORE_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
