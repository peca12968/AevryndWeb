"""Artist-authored connected ocular annulus and shared topological cut contour."""
from pathlib import Path
from collections import defaultdict,deque
import bpy,numpy as np,json,time,datetime,importlib.util
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0112-topological-ocular-graft';OLD=E.parent/'r0111-native-mobile-lid-mesh'
sp=importlib.util.spec_from_file_location('r112author',Path(__file__).with_name('build-female-next-r0104-native-head-union.py'));u=importlib.util.module_from_spec(sp);sp.loader.exec_module(u);q=u.q
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8',newline='\n')
def boundary(faceIDs,polys):
 edge=defaultdict(list)
 for f in faceIDs:
  p=polys[f]
  for a,b in zip(p,p[1:]+p[:1]):edge[tuple(sorted((a,b)))].append(f)
 adj=defaultdict(list)
 for (a,b),fs in edge.items():
  if len(fs)==1:adj[a].append(b);adj[b].append(a)
 assert all(len(ns)==2 for ns in adj.values()),'Non-simple component boundary';seen=set();loops=[]
 for v in adj:
  if v in seen:continue
  loop=[v];prev=-1
  while True:
   seen.add(loop[-1]);n=next(x for x in adj[loop[-1]] if x!=prev)
   if n==v:break
   prev=loop[-1];loop.append(n);assert len(loop)<len(adj)+1
  loops.append(loop)
 return loops
def main():
 tick=time.time()
 if not (E/'topological-authoring-start.json').exists():save('topological-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':'Direct connected anatomical source annulus, fixed shared cut contour and finite union attachment construction; no rectangular crop or pose transfer.'})
 data=np.load(OLD/'actual-rain-ocular-geometry.npz');prev=np.load(OLD/'mobile-ocular-authoring.npz');groups=np.load(E/'actual-rain-lid-groups.npz');ginfo=json.loads((E/'actual-rain-lid-groups.json').read_text('utf8'));A=data['head_neutralWorld'];counts=data['head_neutralPolygonCounts'];ids=data['head_neutralLoopVertexIndices'];starts=np.r_[0,np.cumsum(counts)[:-1]];polys=[ids[s:s+n].tolist() for s,n in zip(starts,counts)];ef=defaultdict(list);va=defaultdict(set)
 for f,p in enumerate(polys):
  for a,b in zip(p,p[1:]+p[:1]):ef[tuple(sorted((a,b)))].append(f);va[a].add(b);va[b].add(a)
 fa=defaultdict(set)
 for fs in ef.values():
  if len(fs)==2:fa[fs[0]].add(fs[1]);fa[fs[1]].add(fs[0])
 badGroups={i for i,n in enumerate(ginfo['groupNames']) if any(x in n.lower() for x in ['nose','lip','mouth','jaw','teeth','tongue'])};dom=groups['dominantGroup'];bad=np.isin(dom,list(badGroups));loops=json.loads((E/'actual-rain-eye-boundaries.json').read_text('utf8'))['boundaries'];native=np.load(E.parent/'r0107-native-coarse-lid-cage/native-coarse-lid-poses-pinned.npz');P=native['neutralFineWorld'];T=native['fineTriangles'];tree=BVHTree.FromPolygons(P.tolist(),T.tolist(),all_triangles=True);Vall=[];Fall=[];states={k:[] for k in ['L_half','L_closed','R_half','R_closed']};fixedAll=[];arrays={};report={};offset=0
 for side,sign in [('L',1),('R',-1)]:
  own=min((r['loop'] for r in loops if np.mean(A[r['loop'],0]) * sign>0),key=lambda l:abs(np.mean(A[l,2])-1.46));seeds={f for a,b in zip(own,np.roll(own,-1)) for f in ef[tuple(sorted((int(a),int(b))))]};support=groups['shapeSupport'+side];eligible={f for f,p in enumerate(polys) if (np.any(support[p]>0) or np.any(np.isin(dom[p],ginfo['lidGroupIndices'][side]))) and np.count_nonzero(bad[p])*2<=len(p)};region=set(seeds);todo=list(seeds)
  while todo:
   f=todo.pop()
   for n in fa[f]:
    if n in eligible and n not in region:region.add(n);todo.append(n)
  # Fill only enclosed complement islands; retain the large exterior component.
  remain=set(range(len(polys)))-region;parts=[]
  while remain:
   first=next(iter(remain));part={first};remain.remove(first);todo=[first]
   while todo:
    for n in fa[todo.pop()]:
     if n in remain:remain.remove(n);part.add(n);todo.append(n)
   parts.append(part)
  outside=max(parts,key=len);region=set(range(len(polys)))-outside;core=set(region);cutRegion=region|{n for f in region for n in fa[f]};patch=cutRegion|{n for f in cutRegion for n in fa[f]};cl=boundary(cutRegion,polys);pl=boundary(patch,polys);assert len(cl)==len(pl)==2,'Ocular annulus needs exactly inner and outer boundary';innerSet=set(own);cutLoop=max(cl,key=lambda l:len(set(l)-innerSet));outer=max(pl,key=lambda l:len(set(l)-innerSet));used=np.unique(np.concatenate([polys[f] for f in patch]));inverse=np.full(len(A),-1,int);inverse[used]=np.arange(len(used));M=prev[side+'_sourceToNativeMatrix'];N=A[used]@M[:3,:3].T+M[:3,3];outerDist={i:0 for i in outer};todo=deque(outer)
  while todo:
   v=todo.popleft()
   for n in va[v]:
    if inverse[n]>=0 and n not in outerDist:outerDist[n]=outerDist[v]+1;todo.append(n)
  insideCut=set(np.concatenate([polys[f] for f in cutRegion]));distance={i:0 for i in cutLoop};todo=deque(cutLoop)
  while todo:
   v=todo.popleft()
   for n in va[v]:
    if n in insideCut and n not in distance:distance[n]=distance[v]+1;todo.append(n)
  motion=np.array([min(distance.get(int(i),0)/2,1.) if i in insideCut else 0. for i in used]);fitted=0;miss=[]
  for j,vi in enumerate(used):
   weight=max(0.,1-outerDist[int(vi)]/3)
   if weight==0:continue
   hit,no,fi,dist=tree.ray_cast(Vector((N[j,0],-.30,N[j,2])),Vector((0,1,0)))
   if hit is None:miss.append(int(vi));continue
   N[j,1]+=weight*(hit.y+.0004-N[j,1]);fitted+=1
  assert not miss,'Shared native collar ray misses';sourceTri=data['head_neutralTriangles'];chosen=np.flatnonzero(np.all(np.isin(sourceTri,list(used)),axis=1));chosen=chosen[np.array([set(map(int,t)).issubset(set(used)) for t in sourceTri[chosen]])];# Keep exactly triangles of chosen source polygons.
  faceSet={tuple(sorted((int(p[0]),int(p[1]),int(p[2])))) for p in []};polyMask=np.zeros(len(polys),bool);polyMask[list(patch)]=True;triToPoly=np.repeat(np.arange(len(polys)),counts-2);assert len(triToPoly)==len(sourceTri);chosen=np.flatnonzero(polyMask[triToPoly]);localTri=inverse[sourceTri[chosen]];Vall.append(N);Fall.append(localTri+offset)
  for key in states:
   ss,label=key.split('_');W=N.copy()
   if ss==side:W+=(data['head_'+label+'World'][used]-A[used])@M[:3,:3].T*motion[:,None]
   states[key].append(W)
  cutWorld=A[cutLoop]@M[:3,:3].T+M[:3,3];arrays[side+'_cutContourWorld']=cutWorld;eyeNeutral=prev['eyes_'+side+'_neutralWorld'];allEye=np.concatenate([prev['eyes_'+side+'_'+s+'World'] for s in ['neutral','half','closed']]);arrays[side+'_cutterYRange']=np.array([eyeNeutral[:,1].min()-.08,allEye[:,1].max()+.003]);arrays[side+'_rawEyeOpeningIndices']=inverse[np.array(own)]+offset;arrays[side+'_artistSourceVertexIDs']=used;arrays[side+'_sourceArtistTriangleIDs']=chosen;report[side]={'sourceCoreFaces':len(core),'cutRegionFaces':len(cutRegion),'patchFaces':len(patch),'newSurfaceVertices':len(used),'sourceOpeningVertices':len(own),'sharedCutContourVertices':len(cutLoop),'outerAttachmentVertices':len(outer),'sourceComponentBoundaryLoops':len(pl),'noseMouthDominantFacesExcluded':True,'fixedCollarVertices':int(np.count_nonzero(motion==0)),'collarRayFittedVertices':fitted};offset+=len(used);fixedAll.append(motion==0)
 V=np.concatenate(Vall);F=np.concatenate(Fall);fixed=np.concatenate(fixedAll);mesh=bpy.data.meshes.new('AFN112_TOPOLOGICAL_MOBILE_OCULAR_SURFACE');mesh.from_pydata(V.tolist(),[],F.tolist());mesh.update();ob=bpy.data.objects.new(mesh.name,mesh);bpy.context.scene.collection.objects.link(ob);ob.shape_key_add(name='Basis');at=mesh.attributes.new(name='AFN112_RawVertexID',type='INT',domain='POINT');at.data.foreach_set('value',np.arange(len(V),dtype='i4'))
 for key,rows in states.items():ob.shape_key_add(name='AFN112_'+key).data.foreach_set('co',np.concatenate(rows).astype('f4').ravel())
 for p in mesh.polygons:p.use_smooth=True
 md=ob.modifiers.new('AFN112_FINITE_OUTWARD_0p8MM','SOLIDIFY');md.thickness=.0008;md.offset=1.;md.use_even_offset=False;bpy.context.view_layer.update();d,N,NT=u.b.geom(ob);N=N.copy();NT=NT.copy();origin=q.arr(d.attributes['AFN112_RawVertexID'].data,'value',len(N),dtype='i4');assert len(N)==2*len(V) and np.array_equal(origin[:len(V)],np.arange(len(V))) and np.array_equal(origin[len(V):],np.arange(len(V)));arrays['finiteNeutralWorld']=N;arrays['finiteTriangles']=NT;arrays['rawSurfaceNeutralWorld']=V;arrays['rawSurfaceTriangles']=F;arrays['fixedFiniteCollar']=fixed[origin];poseStats={}
 for key in states:
  sk=ob.data.shape_keys.key_blocks['AFN112_'+key];sk.value=1;ob.data.shape_keys.update_tag();ob.update_tag();bpy.context.view_layer.update();dd,W,WT=u.b.geom(ob);W=W.copy();W[fixed[origin]]=N[fixed[origin]];arrays['finite_'+key+'World']=W;poseStats[key]={'actualPairedDisplacementQuantilesM':np.quantile(np.linalg.norm(W[len(V):]-W[:len(V)],axis=1),[0,.5,.95,1]),'fixedFiniteCollarMaximumMoveM':float(np.linalg.norm(W[fixed[origin]]-N[fixed[origin]],axis=1).max())};sk.value=0;ob.data.shape_keys.update_tag();ob.update_tag();bpy.context.view_layer.update()
 for key in prev.files:
  if key.startswith(('eyes_','cornea_')):arrays[key]=prev[key]
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(E/'topological-ocular-authoring.blend'),compress=True);np.savez_compressed(E/'topological-ocular-authoring.npz',**arrays);save('topological-ocular-authoring.json',{'construction':'Connected artist closure-support/lid-group annulus excluding nasal/oral domains, same explicit inner collar contour drives body cutter; true volumetric union planned. Finite outward0.8mm shell without even-offset amplification, fixed finite collar. Own source geometry/core poses, no pose transfer to old skin.','artist':'Rain Rig (CC) Blender Foundation | studio.blender.org / CC-BY4.0','parts':report,'finitePoseChecks':poseStats,'noGlobalThicknessContactOrFullCharacterAcceptance':True,'seconds':time.time()-tick});print('R112_TOPOLOGICAL_FINITE_OCULAR_COMPONENT_AUTHORED',time.time()-tick,flush=True)
if __name__=='__main__':main()
