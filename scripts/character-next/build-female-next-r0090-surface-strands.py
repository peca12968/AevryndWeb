"""Third r90 construction: UV-tangent trajectories on authored hair surfaces.
Not DreamWorks sparse-volume advection, not opposite-card-rail extraction.
All attempted roots remain in the pilot; any trace failure blocks expansion.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,heapq,time,sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(r'D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0090-native-scalp-groom';SRC=S/'aevrynd-female-next-r0090-b-rain-hair-shape-study.blend';FULL='--full' in sys.argv;LONGITUDINAL='--longitudinal' in sys.argv;TAG=('c-v-full' if FULL else 'c-v-guide') if LONGITUDINAL else ('c-full' if FULL else 'c-guide');OUT=S/('aevrynd-female-next-r0090-c-'+('v' if LONGITUDINAL else 'uv')+'-flow-'+('fibres' if FULL else 'pilot')+'.blend');COUNT=21908 if FULL else 128;N=96
def mod(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
m=mod('r90fieldsource','build-female-next-r0081-editable-curly.py');q=m.q;v=mod('r90fieldview','render-female-next-r0081-retained-study.py');v.E=E;k=mod('r90fieldnative','build-female-next-r0090-intrinsic-groom.py')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(E/n).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def unit(p):return p/max(float(np.linalg.norm(p)),1e-20)
def field(o,target):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());d=ev.to_mesh(preserve_all_data_layers=True,depsgraph=bpy.context.evaluated_depsgraph_get());P=q.arr(d.vertices,'co',len(d.vertices),3).astype('f8');A=np.array(o.matrix_world);P=P@A[:3,:3].T+A[:3,3];d.calc_loop_triangles();T=q.arr(d.loop_triangles,'vertices',len(d.loop_triangles),3,'i4');loops=q.arr(d.loop_triangles,'loops',len(d.loop_triangles),3,'i4');UV=q.arr(d.uv_layers['UVMap.tangent'].data,'uv',len(d.loops),2).astype('f8')[loops];ev.to_mesh_clear();tri=P[T];e1=tri[:,1]-tri[:,0];e2=tri[:,2]-tri[:,0];du=UV[:,1]-UV[:,0];dv=UV[:,2]-UV[:,0];det=du[:,0]*dv[:,1]-du[:,1]*dv[:,0];valid=abs(det)>1e-12;tangent=((-e1*dv[:,0,None]+e2*du[:,0,None]) if LONGITUDINAL else (e1*dv[:,1,None]-e2*du[:,1,None]))/np.where(valid,det,1)[:,None]
 edges=np.unique(np.sort(np.concatenate((T[:,[0,1]],T[:,[1,2]],T[:,[2,0]])),axis=1),axis=0);adj=[[] for _ in P]
 for a,b in edges:
  c=float(np.linalg.norm(P[a]-P[b]));adj[a].append((int(b),c));adj[b].append((int(a),c))
 seen=np.zeros(len(P),bool);components=[];D=np.full(len(P),np.inf);seeds=[]
 for start in range(len(P)):
  if seen[start]:continue
  stack=[start];seen[start]=True;cc=[]
  while stack:
   a=stack.pop();cc.append(a)
   for b,_ in adj[a]:
    if not seen[b]:seen[b]=True;stack.append(b)
  cc=np.array(cc,'i4');components.append(cc);end=int(cc[np.linalg.norm(P[cc]-target,axis=1).argmin()]);seeds.append(end);D[end]=0;heap=[(0.,end)]
  while heap:
   dist,a=heapq.heappop(heap)
   if dist>D[a]:continue
   for b,c in adj[a]:
    nd=dist+c
    if nd<D[b]:D[b]=nd;heapq.heappush(heap,(nd,b))
 da=D[T[:,1]]-D[T[:,0]];db=D[T[:,2]]-D[T[:,0]];g11=np.einsum('ij,ij->i',e1,e1);g22=np.einsum('ij,ij->i',e2,e2);g12=np.einsum('ij,ij->i',e1,e2);den=np.maximum(g11*g22-g12*g12,1e-30);grad=e1*((g22*da-g12*db)/den)[:,None]+e2*((g11*db-g12*da)/den)[:,None];dot=np.einsum('ij,ij->i',tangent,grad);tangent=np.where((dot>0)[:,None],-tangent,tangent);tangent[~valid]=-grad[~valid];tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-20);tree=BVHTree.FromPolygons(P.tolist(),T.tolist(),all_triangles=True)
 return {'P':P,'T':T,'D':D,'tangent':tangent,'tree':tree,'components':len(components),'seeds':seeds,'UVValidTriangleFraction':float(valid.mean())}
def sample(f,p):
 co,_,face,_=f['tree'].find_nearest(Vector(p));bc=m.rig.base.bary(np.array(co),f['P'][f['T'][face]]);return np.array(co),f['tangent'][face],float(bc@f['D'][f['T'][face]])
def trace(f,p):
 co,_,dist=sample(f,p);P=[co];dist0=dist;best=dist;stall=0;reason=None
 for i in range(700):
  co,d,dist=sample(f,P[-1])
  if dist<.002:break
  mid,md,_=sample(f,co+d*.0005);nxt,_,nd=sample(f,co+md*.001)
  if np.linalg.norm(nxt-co)>.003:reason='SURFACE_PROJECTION_JUMP';break
  stall=stall+1 if nd>=best-.00002 else 0;best=min(best,nd);P.append(nxt)
  if stall>=20:reason='NONDECREASING_OR_STALLED_UV_TRACE';break
 else:reason='STEP_BOUND_REACHED'
 return np.array(P),{'initialGeodesicToEndM':dist0,'lastGeodesicToEndM':sample(f,P[-1])[2],'steps':len(P)-1,'failure':reason}
def main():
 tick=time.time();assert not OUT.exists() and sha(SRC)=='b28711d6b4f747829def389ada85440a2f3d6bd6016c5c0053d3ca38ae7f7d9f'
 if LONGITUDINAL:
  audit=json.loads((E/'flow-parameter-audit.json').read_text());assert audit['source']==str(SRC) and min(row['medianAbsVAlignment'] for row in audit['rows'])>.8,'No audited basis for changing growth coordinate'
 if FULL:assert json.loads((E/'c-guide-review.json').read_text())['worthFullFibres']
 bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();names=['AFN90_RAIN_HAIR_MAIN','AFN90_RAIN_HAIR_PONYTAIL','AFN90_RAIN_HAIR_STRAND'];o=[bpy.data.objects[n] for n in names];band=bpy.data.objects['AFN90_RAIN_HAIRBAND'];B=q.geom(band)[1].mean(0);targets=[B,q.geom(o[1])[1][q.geom(o[1])[1][:,2].argmin()],q.geom(o[2])[1][q.geom(o[2])[1][:,2].argmin()]];fields=[field(ob,target) for ob,target in zip(o,targets)];data=np.load(E/'a-guide-lineage.npz');P=data['scalpWorld'];F=data['scalpTriangles'];tri=P[F];area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1);rng=np.random.default_rng(903090);fi=rng.choice(len(F),COUNT,p=area/area.sum());uv=rng.random((COUNT,2));fl=uv.sum(1)>1;uv[fl]=1-uv[fl];bc=np.column_stack((1-uv.sum(1),uv));norm=unit(np.array([1.,0,0])) # overwritten per actual scalp triangle
 roots=np.einsum('ni,nij->nj',bc,tri[fi]);nn=np.cross(tri[fi,1]-tri[fi,0],tri[fi,2]-tri[fi,0]);nn/=np.maximum(np.linalg.norm(nn,axis=1)[:,None],1e-20);roots+=nn*.00016;paths=[];records=[];failed=[]
 for ci,root in enumerate(roots):
  a,_,_=sample(fields[0],root);b,_,_=sample(fields[2],root);loose=(np.linalg.norm(root-b)<np.linalg.norm(root-a)) and root[0]<0 and root[1]<-.08;idx=2 if loose else 0;chain,row=trace(fields[idx],root);lead=np.linspace(root,chain[0],6);whole=np.vstack((lead[:-1],chain));sub=None
  if not loose and row['failure'] is None:
   tail,sub=trace(fields[1],chain[-1]);bridge=np.linspace(chain[-1],tail[0],5);whole=np.vstack((whole,bridge[1:-1],tail));fraction=.82+.18*((ci*.61803398875)%1);whole=k.resample(whole,128);whole=whole[:max(10,int(len(whole)*fraction))]
  if row['failure'] or (sub and sub['failure']):failed.append(ci)
  whole=k.resample(whole,N);whole[0]=root;paths.append(whole);records.append({'root':ci,'looseFrontStrand':bool(loose),'mainOrLoose':row,'tail':sub,'worldStart':root.tolist(),'failed':ci in failed})
  if ci%1000==0:print('R90_UV_FLOW',ci,'failed',len(failed),flush=True)
 paths=np.array(paths);assert np.isfinite(paths).all();A=bpy.data.objects['AFN81_EDITABLE_CURLY_GUIDES'].matrix_world.copy();AA=np.array(A);local=(paths.reshape(-1,3)-AA[:3,3])@np.linalg.inv(AA[:3,:3]).T;guide=k.live.pointmesh('AFN90_UV_FLOW_GUIDE_CAGES',local,A,[(i*N+j,i*N+j+1) for i in range(COUNT) for j in range(N-1)]);guide['scope']='All attempted actual scalp roots retained; UV tangent trajectory cage, not a sparse volumetric field, collision solver or live skin attachment.'
 for ob in o:ob.hide_render=True;ob.hide_set(True)
 if FULL:
  assert not failed,'Do not discard failed traces to qualify a groom';old=bpy.data.objects['AFN81_EDITABLE_CURLY_GUIDES'];data=bpy.data.hair_curves.new('AFN90_UV_FLOW_NATIVE_FIBRES');data.add_curves([N]*COUNT);data.position_data.foreach_set('vector',local.astype('f4').ravel());at=data.attributes.new('radius','FLOAT','POINT');at.data.foreach_set('value',np.full(COUNT*N,.001,'f4'));data.materials.append(bpy.data.materials['Brown hair']);render=bpy.data.objects.new('AFN90_UV_FLOW_RENDER_FIBRES',data);s.collection.objects.link(render);render.matrix_world=A.copy();body=m.rig.k.mesh(bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING']);attachment=k.bind(render,body,body['V'],body['T'],old)
 else:
  legacy=bpy.data.curves.new('AFN90_UV_FLOW_DIAGNOSTIC','CURVE');legacy.dimensions='3D';legacy.bevel_depth=.0005/np.linalg.norm(AA[:3,0]);legacy.bevel_resolution=1
  for p in paths:
   L=(p-AA[:3,3])@np.linalg.inv(AA[:3,:3]).T;sp=legacy.splines.new('POLY');sp.points.add(N-1);sp.points.foreach_set('co',np.column_stack((L,np.ones(N))).astype('f4').ravel())
  mat=bpy.data.materials.new('AFN90_UV_FLOW_OPAQUE_DIAGNOSTIC');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.16,.075,.025,1);bs.inputs['Roughness'].default_value=.65;legacy.materials.append(mat);render=bpy.data.objects.new(legacy.name,legacy);s.collection.objects.link(render);render.matrix_world=A.copy();attachment={'scope':'Static0.5mm sparse diagnostic, not physical strands, skin following or contact.'}
 guide.hide_set(True);s['AFN90_C_scope']='Artist UV-tangent traces from actual target-scalp roots, followed on attributed Rain surfaces with geodesic sign orientation. All failed roots retained and expansion blocked on any failure. Not sparse-volume reconstruction, no body/self/continuous contact or natural-motion/runtime qualification.';m.rig.shade.settings();m.rig.k.b.camera('face');s.camera.data.lens=85;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);np.savez_compressed(E/(TAG+'-lineage.npz'),pathsWorld=paths,rootsWorld=roots,scalpFaces=fi,scalpBarycentric=bc,failedRootIDs=np.array(failed,'i4'),matrix=AA);save(TAG+'-build-summary.json',{'source':str(SRC),'sourceSha256':sha(SRC),'output':str(OUT),'outputSha256':sha(OUT),'outputBytes':OUT.stat().st_size,'construction':'Actual target-scalp roots connected to trajectories on author-created hair surfaces using UVMap.tangent derivative with geodesic-to-end sign orientation. Source solid meshes hidden; no opposite-quad rail extraction or shared XYZ template. Surface-coating hypothesis, not full volume filling.','actualRoots':COUNT,'pointsEach':N,'failedTraceCount':len(failed),'failedRootIDs':failed,'traceRecords':records,'fieldScope':[{'object':n,'connectedComponents':f['components'],'UVValidTriangleFraction':f['UVValidTriangleFraction']} for n,f in zip(names,fields)],'allAttemptedRootsRetained':True,'guideObject':guide.name,'renderObject':render.name,'attachment':attachment,'worthExpansionNumerically':not failed,'noRealismContactMotionOrRuntimeAcceptance':True,'secondsBeforePreview':time.time()-tick})
 rows=[]
 for view in ('back','face','body-face'):rows.append(v.image(TAG+'-uv-flow',view));save(TAG+'-view-controls.json',rows)
 print('R90_UV_FLOW_DONE',TAG,len(failed),time.time()-tick,flush=True)
if __name__=='__main__':main()
