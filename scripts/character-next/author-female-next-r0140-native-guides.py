"""Actual original-clump open medial guide construction, not UV isocontours.
One intermediate native guide library on the same working woman, not a candidate.
"""
from pathlib import Path
import bpy,numpy as np,json,heapq,time,datetime,importlib.util
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0140-native-clump-roots';S=R/'engine/assets/characters/female-next/source';SRC=S/'r0139-source/aevrynd-female-next-r0139-a-native-lid-follow.blend';LIB=S/'r0140-source/aevrynd-female-next-r0140-native-clump-guides.blend'
sp=importlib.util.spec_from_file_location('r140base',Path(__file__).with_name('build-female-next-r0138-native-current-gaze.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
def save(n,x):
 (E/n).write_text(json.dumps(x,indent=2,default=lambda q:q.tolist() if isinstance(q,np.ndarray) else q.item() if isinstance(q,np.generic) else str(q))+'\n',encoding='utf-8')
def distances(g,seeds):
 d={int(i):0. for i in seeds};heap=[(0.,int(i)) for i in seeds];heapq.heapify(heap)
 while heap:
  v,i=heapq.heappop(heap)
  if v!=d[i]:continue
  for j,w in g[i]:
   t=v+w
   if t<d.get(j,np.inf):d[j]=t;heapq.heappush(heap,(t,j))
 return d
def main():
 tick=time.time();assert not LIB.exists();bpy.ops.wm.open_mainfile(filepath=str(SRC));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();save('direct-native-guide-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalStartedUTC':'2026-10-21T23:07:40+00:00','action':'Author actual source-clump geodesic open guides, real current-skin scalp root triangles/barycentrics, native CURVES intermediate in same complete woman. No original UV contour field, foreign fit or closed synthetic loft.'});W,T=a.geometry(bpy.data.objects[a.FIXED[0]]);V,F=a.geometry(bpy.data.objects[a.FIXED[1]]);cached=np.load(E.parent/'r0130-artist-native-groom/current-hair-native-triangle-charts.npz');labels=cached['componentLabels'];assert np.array_equal(F,cached['triangles']) and np.linalg.norm(V-cached['world'],axis=1).max()<2e-6;chart=np.load(E.parent/'r0133-anatomical-scalp-chart/target-scalp-chart.npz');K=KDTree(len(W))
 for i,p in enumerate(W):K.insert(Vector(p),i)
 K.balance();matches=[K.find(Vector(p)) for p in chart['world']];ids=np.array([r[1] for r in matches],dtype='i4');assert max(r[2] for r in matches)<1e-6;mapped=ids[chart['triangles']];lookup={tuple(sorted(f)):i for i,f in enumerate(T)};faces=np.array([lookup[tuple(sorted(f))] for f in mapped],dtype='i4');bvh=BVHTree.FromPolygons([Vector(p) for p in W],T[faces].tolist(),all_triangles=True);edges=np.unique(np.sort(np.concatenate([F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]]),axis=1),axis=0);g=[[] for _ in V]
 for i,j in edges:
  w=float(np.linalg.norm(V[i]-V[j]));g[int(i)].append((int(j),w));g[int(j)].append((int(i),w))
 P=[];width=[];roots=[];reports=[];stations=25
 for label in np.unique(labels):
  comp=np.flatnonzero(labels==label);D=distances(g,[int(comp[0])]);endA=max(D,key=D.get);DA=distances(g,[endA]);endB=max(DA,key=DA.get);DB=distances(g,[endB]);length=DA[endB];assert length>0
  capA=np.array([i for i in comp if DB[int(i)]>=length*.95]);capB=np.array([i for i in comp if DA[int(i)]>=length*.95]);A=V[capA].mean(0);B=V[capB].mean(0);na=bvh.find_nearest(Vector(A));nb=bvh.find_nearest(Vector(B));rootSeeds=capA if na[3]<=nb[3] else capB;D=distances(g,rootSeeds);dd=np.array([D[int(i)] for i in comp]);mx=dd.max();groups=np.clip(np.rint(dd/max(mx,1e-20)*(stations-1)).astype(int),0,stations-1);valid=[];center=[]
  for j in range(stations):
   part=comp[groups==j]
   if len(part):valid.append(j);center.append(V[part].mean(0))
  center=np.array(center);Q=np.column_stack([np.interp(np.arange(stations),valid,center[:,k]) for k in range(3)]);rootSource=Q[0].copy();pt,no,fi,dist=bvh.find_nearest(Vector(rootSource));fi=int(faces[fi]);tri=T[fi];edge1=W[tri[1]]-W[tri[0]];edge2=W[tri[2]]-W[tri[0]];co=np.linalg.lstsq(np.column_stack([edge1,edge2]),np.array(pt)-W[tri[0]],rcond=None)[0];bc=np.array([1-co.sum(),co[0],co[1]]);bc=np.maximum(bc,0);bc/=bc.sum();root=bc@W[tri];normal=np.cross(edge1,edge2);normal/=np.linalg.norm(normal);Q[0]=root+normal*.00005;Q[1]=.5*(Q[1]+root+normal*.001);arc=float(np.linalg.norm(np.diff(Q,axis=0),axis=1).sum());compFaces=F[labels[F[:,0]]==label];area=float(np.linalg.norm(np.cross(V[compFaces[:,1]]-V[compFaces[:,0]],V[compFaces[:,2]]-V[compFaces[:,0]]),axis=1).sum()*.5);w=area/max(arc,1e-8);P.append(Q);width.append(w);roots.append((fi,bc));reports.append({'component':int(label),'vertices':len(comp),'geodesicDiameterM':length,'guideArcM':arc,'sourceEndpointToActualScalpM':float(dist),'areaDerivedWidthM':w,'actualSkinTriangle':fi,'rootBarycentric':bc,'rootSource':rootSource,'actualRootWorld':root,'rootProjectionIsBindingNotContactProof':True})
 P=np.array(P);data=bpy.data.hair_curves.new('AFN140_NATIVE_OPEN_SOURCE_CLUMP_GUIDE_DATA');data.add_curves([stations]*len(P));data.position_data.foreach_set('vector',P.astype('f4').ravel());data.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',np.full(P.size//3,.00015,dtype='f4'));ob=bpy.data.objects.new('AFN140_NATIVE_OPEN_SOURCE_CLUMP_GUIDES',data);bpy.context.scene.collection.objects.link(ob);ob.hide_render=True;ob['role']='Actual editable original source-clump open root-to-tip scaffold, not a complete hairstyle/character improvement or natural follicle proof.';ob['sourceCredit']='Derived from original Angelica Hair / DarkNik original NikZava284 CC-BY4.0, inherited full source/legal retained. New Aevrynd source-native graph medials and actual current scalp bindings; no source UV isocontour, foreign whole-groom fit or synthetic closed loft.';bpy.data.libraries.write(str(LIB),{ob},compress=True);np.savez_compressed(E/'native-open-clump-guides.npz',guides=P,width=np.array(width),rootFaces=np.array([x[0] for x in roots]),rootBarycentric=np.array([x[1] for x in roots]),scalpFaces=faces);save('native-open-guide-construction.json',{'source':str(SRC),'library':str(LIB),'sha256':a.a.sha(LIB),'bytes':LIB.stat().st_size,'sourceClumpComponents':len(P),'all470ComponentsRepresented':len(P)==470,'openNativeGuideStations':stations,'actualGuideObject':ob.name,'actualCurrentSkin':a.FIXED[0],'actualCurrentScalpTriangleCount':len(faces),'semanticScalpReferenceExactCoordinateMappingMaxM':max(r[2] for r in matches),'sourceScalpMappingIsNotForeignHeadCapFit':True,'sourceComponentGuides':reports,'construction':'Original component edge-geodesic diameter, scalp-selected actual source end, multi-source intrinsic distance stations/3D cross-section centroids. Native open guide curves retain source macro shape; endpoints/follicles are newly authored, not claimed original artist root semantics.','noRetiredUVContourOrClosedSyntheticLoftUsed':True,'appearanceOperationContactRuntimeAccepted':False,'libraryIsIntermediateNotCompleteCandidate':True,'seconds':time.time()-tick});print('R140_NATIVE_ACTUAL_OPEN_CLUMP_GUIDES_AUTHORED',len(P),LIB.stat().st_size,time.time()-tick,flush=True)
if __name__=='__main__':main()
