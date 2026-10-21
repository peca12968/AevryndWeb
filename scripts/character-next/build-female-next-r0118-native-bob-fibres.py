"""One complete woman: reconstruct fibres from original native quad strips."""
from pathlib import Path
import bpy,numpy as np,json,time,datetime,importlib.util,os,hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0118-native-bob-construction';SRC=S/'r0117-source/aevrynd-female-next-r0117-a-native-fibre-brows.blend';OUT=S/'r0118-source/aevrynd-female-next-r0118-a-native-quad-strip-bob.blend'
sp=importlib.util.spec_from_file_location('r118base',Path(__file__).with_name('build-female-next-r0116-native-eye-character.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b;q=a.q;b.u.v.E=E
def save(n,j):(E/n).write_text(json.dumps(j,indent=2,default=lambda a:a.tolist() if isinstance(a,np.ndarray) else a.item())+'\n',encoding='utf-8',newline='\n')
def protected():
 d=a.protected();d['allOriginalFibres'].pop('AFN97_TUCKED_ARTIST_BOB_CHILDREN');return d
def sample(P,N):
 t=np.r_[0,np.linalg.norm(np.diff(P,axis=0),axis=1).cumsum()];valid=np.r_[True,np.diff(t)>1e-12];t=t[valid];P=P[valid];assert len(t)>1
 return np.stack([np.interp(np.linspace(0,t[-1],N),t,P[:,j]) for j in range(3)],axis=1)
def main():
 tick=time.time();assert not OUT.exists();save('complete-fibre-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':'Directly reconstruct all24800 original-width hair curves from source-native opposite-edge quad strips; no old Bob outward/tuck offsets or shared XYZ free-guide families.'});digest=a.sha(SRC);bpy.ops.wm.open_mainfile(filepath=str(SRC));b.deliver(0);before=protected();skin=bpy.data.objects['AFN113_COMPLETE_WOMAN_COHERENT_HEAD'];ob=bpy.data.objects['AFN97_TUCKED_ARTIST_BOB_CHILDREN'];oldWorld=q.hair(ob).copy();counts=np.array([c.points_length for c in ob.data.curves],dtype='i4');assert len(counts)==24800 and np.all(counts==17);radii=q.arr(ob.data.attributes['radius'].data,'value',len(oldWorld)).copy();data=ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.copy();ob.data=data
 for md in list(ob.modifiers):ob.modifiers.remove(md)
 z=np.load(E/'native-bob-authored-strip-paths.npz');W=z['actualSourceWorld'];pairs=z['edgeVertexPairs'];edgecounts=z['pathEdgeCounts'];offsets=np.r_[0,np.cumsum(edgecounts)];paths=[W[pairs[offsets[i]:offsets[i+1]]] for i in range(len(edgecounts))];width=np.array([np.linalg.norm(p[:,1]-p[:,0],axis=1).mean() for p in paths]);allocate=np.ones(len(paths),dtype='i4');quota=(24800-len(paths))*width/width.sum();allocate+=np.floor(quota).astype('i4');remaining=24800-int(allocate.sum());allocate[np.argsort(quota-np.floor(quota))[-remaining:]]+=1 if remaining else 0;assert allocate.sum()==24800
 HA=np.array(ob.matrix_world);HI=np.linalg.inv(HA[:3,:3]);d,BW,BT=b.u.b.geom(skin);BW=BW.copy();BT=BT.copy();VL=(BW-HA[:3,3])@HI.T;tree=BVHTree.FromPolygons(BW.tolist(),BT.tolist(),all_triangles=True);ids=[];barys=[];roots=[];frames=[];new=np.empty_like(oldWorld);lineage=[];distances=[];ci=0
 for pi,(path,n) in enumerate(zip(paths,allocate)):
  for j in range(int(n)):
   u=(j+.5)/n;P=path[:,0]*(1-u)+path[:,1]*u;hit,no,fi,dist=tree.find_nearest(Vector(P[0]));assert hit is not None;tri=BT[fi];w=b.u.a.bary(np.array(hit),BW[tri]);v=VL[tri];normal=np.cross(v[1]-v[0],v[2]-v[0]);normal/=np.linalg.norm(normal);t=v[1]-v[0];t/=np.linalg.norm(t);root=w@v+normal*radii[ci*17];rootWorld=root@HA[:3,:3].T+HA[:3,3]
   # The actual source-surface path remains intact after its new attached root.
   # No whole-strand root translation or displacement blending is applied.
   curve=sample(np.vstack([rootWorld,P]),17);new[ci*17:(ci+1)*17]=(curve-HA[:3,3])@HI.T;ids.append(tri);barys.append(w);roots.append(root);frames.append([t,np.cross(normal,t),normal]);distances.append(dist);lineage.append([pi,u]);ci+=1
 ids=np.array(ids,'i4');frames=np.array(frames);data.attributes['position'].data.foreach_set('vector',new.astype('f4').ravel())
 for j in range(3):data.attributes['AFN97_ScalpVertex'+str(j)].data.foreach_set('value',ids[:,j])
 for name,value in [('RootBarycentric',barys),('RestRoot',roots),('RestT',frames[:,0]),('RestB',frames[:,1]),('RestN',frames[:,2])]:data.attributes['AFN97_'+name].data.foreach_set('vector',np.array(value,'f4').ravel())
 data.attributes['AFN97_RootRadiusNative'].data.foreach_set('value',radii[::17]);b.u.root_modifier(ob,skin);data.update_tag();ob.update_tag();b.deliver(0);actual=q.hair(ob);expected=new@HA[:3,:3].T+HA[:3,3];error=float(np.linalg.norm(actual-expected,axis=1).max());assert error<3e-6;assert np.array_equal(q.arr(data.attributes['radius'].data,'value',len(radii)),radii);assert protected()==before
 ob['r118Scope']='Original-width24800 fibres reconstructed from source-native original quad strips, actual skin-mounted roots. Geometric source endpoints/nearest skin are NOT verified anatomical follicles. New complete art trial only, no natural dynamics or finite contact acceptance.'
 with bpy.data.libraries.load(str(E/'native-bob-source-authoring.blend'),link=False) as (aa,bb):bb.objects=['AFN118_NATIVE_BOB_SHAPE_REFERENCE']
 ref=bb.objects[0];bpy.context.scene.collection.objects.link(ref);ref.hide_render=True;ref.hide_set(True)
 np.savez_compressed(E/'native-bob-fibre-lineage.npz',originalWorld=oldWorld,newAuthoredLocal=new,actualWorld=actual,originalRadii=radii,counts=counts,actualRootSkinTriangles=ids,actualRootBarycentric=np.array(barys),sourcePathAndCrossParameter=np.array(lineage),sourceRootMountDistancesM=np.array(distances))
 save('a-build-summary.json',{'source':str(SRC),'output':str(OUT),'allCurves':len(counts),'allPoints':len(actual),'allOriginalWidthsAndCurveCountRetained':True,'nativeSourceQuadStripPaths':len(paths),'allocationPerOriginalStrip':allocate,'rootMountSourceEndpointDistanceQuantilesM':np.quantile(distances,[0,.5,.95,1]),'rootMountIsGeometricNotProvenAnatomicalFollicles':True,'actualAgainstAuthoredWorldMaxM':error,'beforeProtectedBodyKeysBrowsLashes':before,'afterProtectedBodyKeysBrowsLashes':protected(),'allProtectedGeometryAndKeysByteExact':True,'oldHairMaterialUnchanged':True,'allOriginalImagePathsAndInputsRetained':True,'sourceSurfaceHiddenReferenceOnly':True,'noOldSharedTuckOrOutwardBrush':True,'finiteRenderedSelfContinuousNaturalMotionAndRuntimeUnaccepted':True,'secondsBeforePreview':time.time()-tick})
 b.deliver(0);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=False);assert a.sha(SRC)==digest;views=[]
 for view in ['face','body-face','oblique','profile','back']:
  views.append(b.u.v.image('a-native-quad-strip-bob',view));save('a-view-controls.json',views)
 print('R118_COMPLETE_NATIVE_QUAD_STRIP_BOB_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
