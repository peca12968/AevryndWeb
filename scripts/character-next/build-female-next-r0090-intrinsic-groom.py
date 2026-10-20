"""Actual target scalp routes, authored section ends, live native guide data.
One candidate, sparse guide diagnostic before full fibres. Projection constructs
scalp-conforming art routes, not a contact solver or collision certificate.
No r48 root-normal rotation, r61 common ponytail exit or r89 global bob formula.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,heapq,time,sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
R=Path(r'D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0090-native-scalp-groom';SRC=S/'aevrynd-female-next-r0088-b-supported-lid-aperture.blend'
FULL='--full' in sys.argv;OUT=S/('aevrynd-female-next-r0090-a-intrinsic-'+('full-groom' if FULL else 'guide-pilot')+'.blend');N=64;COUNT=21908;GUIDES=96;CENTER=np.array([0.,-.042,1.474]);BOUND_A=np.array([0,.55,1.,1.57,2.05,2.55,np.pi]);BOUND_E=np.array([.45,.43,.18,.025,-.26,-.58,-.69])
def mod(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
m=mod('r90_source','build-female-next-r0081-editable-curly.py');q=m.q;views=mod('r90_views','render-female-next-r0081-retained-study.py');views.E=E;live=mod('r90_liveguides','build-female-next-r0089-posterior-bundles.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(E/n).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def unit(v):return v/np.maximum(np.linalg.norm(v,axis=-1,keepdims=True),1e-20)
def smooth(a,b,t):
 t=np.clip((t-a)/(b-a),0,1);return t*t*(3-2*t)
def resample(P,n):
 arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(P,axis=0),axis=1))];keep=np.r_[True,np.diff(arc)>1e-9];arc=arc[keep];P=P[keep]
 if len(P)==1:return np.repeat(P,n,axis=0)
 return np.column_stack([np.interp(np.linspace(0,arc[-1],n),arc,P[:,i]) for i in range(3)])
def mesh(name,P,T,A):
 d=bpy.data.meshes.new(name+'_DATA');d.from_pydata(P.tolist(),[],T.tolist());d.update();o=bpy.data.objects.new(name,d);bpy.context.scene.collection.objects.link(o);o.matrix_world=A.copy();o.hide_render=True;o.hide_set(True);return o
def native(name,P,radius,A):
 print('R90_NATIVE_BEGIN',name,len(P),flush=True);AA=np.array(A);local=(P-AA[:3,3])@np.linalg.inv(AA[:3,:3]).T;d=bpy.data.hair_curves.new(name+'_DATA');d.add_curves([N]*len(P));d.position_data.foreach_set('vector',local.astype('f4').ravel());at=d.attributes.get('radius') or d.attributes.new('radius','FLOAT','POINT');values=(np.broadcast_to(radius,(len(P),N))/np.linalg.norm(AA[:3,0])).astype('f4');at.data.foreach_set('value',values.ravel());d.materials.append(bpy.data.materials['Brown hair']);o=bpy.data.objects.new(name,d);bpy.context.scene.collection.objects.link(o);o.matrix_world=A.copy();print('R90_NATIVE_READY',name,flush=True);return o
def diagnostic(name,P,A):
 AA=np.array(A);local=(P-AA[:3,3])@np.linalg.inv(AA[:3,:3]).T;d=bpy.data.curves.new(name+'_DATA','CURVE');d.dimensions='3D';d.bevel_depth=.0005/np.linalg.norm(AA[:3,0]);d.bevel_resolution=1;d.resolution_u=1
 for p in local:
  sp=d.splines.new('POLY');sp.points.add(N-1);sp.points.foreach_set('co',np.column_stack((p,np.ones(N))).astype('f4').ravel())
 d.materials.append(bpy.data.materials['Brown hair']);o=bpy.data.objects.new(name,d);bpy.context.scene.collection.objects.link(o);o.matrix_world=A.copy();return o
def bind(o,body,bodyV,bodyT,old):
 raw=q.hair(o);d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;counts=np.array([c.points_length for c in d.curves]);starts=np.r_[0,np.cumsum(counts)[:-1]];tree=BVHTree.FromPolygons(bodyV.tolist(),bodyT.tolist(),all_triangles=True);ids=[];BC=[];anchors=[]
 for root in raw[starts]:
  co,_,f,_=tree.find_nearest(Vector(root));ix=bodyT[f];bc=m.rig.base.bary(np.array(co),bodyV[ix]);ids.append(ix);BC.append(bc);anchors.append(bc@bodyV[ix])
 ids=np.array(ids,'i4');BC=np.array(BC,'f4');anchors=np.array(anchors);tt,bb,nn=m.rig.frames(bodyV[ids]);kd=KDTree(len(bodyV))
 for i,p in enumerate(bodyV):kd.insert(Vector(p),i)
 kd.balance();F=np.array([[kd.find(Vector(z))[1] for z in (p-.01*t,p+.01*t,p+.01*b)] for p,t,b in zip(anchors,tt,bb)],'i4');area=np.linalg.norm(np.cross(bodyV[F[:,1]]-bodyV[F[:,0]],bodyV[F[:,2]]-bodyV[F[:,0]]),axis=1);assert area.min()>1e-6
 table=bpy.data.meshes.new(o.name+'_BINDING_DATA');table.vertices.add(len(counts));table.vertices.foreach_set('co',np.zeros(len(counts)*3,'f4'));table.update()
 for j in range(3):live.attribute(table,'AFN69_BodyVertex'+str(j),'INT',ids[:,j]);live.attribute(table,'AFN81_FrameVertex'+str(j),'INT',F[:,j])
 for n,v in [('Barycentric',BC),('RestAnchor',anchors),('RestTangent',tt),('RestBinormal',bb),('RestNormal',nn)]:live.attribute(table,'AFN69_'+n,'FLOAT_VECTOR',np.asarray(v,'f4'))
 ref=bpy.data.objects.new(o.name+'_ROOT_TABLE',table);bpy.context.scene.collection.objects.link(ref);ref.hide_render=True;ref.hide_set(True);ng=old.modifiers['AFN81_ACTUAL_RENDER_ROOT_TABLE'].node_group.copy();ng.name=o.name+'_ASSIGN_ROOTS'
 for nd in ng.nodes:
  if nd.bl_idname=='GeometryNodeObjectInfo':nd.inputs['Object'].default_value=ref
 md=o.modifiers.new('AFN90_ACTUAL_ROOT_TABLE','NODES');md.node_group=ng;md=o.modifiers.new('AFN90_ACTUAL_SKIN_ROOT_FRAMES','NODES');md.node_group=old.modifiers['AFN81_LIVE_RENDER_SCALP_FRAME'].node_group;bpy.context.view_layer.update();after=q.hair(o);error=float(np.linalg.norm(after-raw,axis=1).max());assert error<2e-6;return {'table':ref.name,'maximumNeutralFrameErrorM':error,'minimumDoubleFrameAreaM2':float(area.min())}
def main():
 tick=time.time();assert not OUT.exists() and sha(SRC)=='72435890a03cab26ff2f3e238060daf2b2cf797f85543d8fd6182583cc1101a7'
 if FULL:assert json.loads((E/'guide-review.json').read_text())['shapeDirectionWorthFullFibres']
 data=np.load(E/'actual-head-surface.npz');V=data['world'];T=data['triangles'];C=V[T].mean(1);Q=C-CENTER;az=np.arctan2(Q[:,0],-Q[:,1]);el=np.arctan2(Q[:,2],np.linalg.norm(Q[:,:2],axis=1));cross=np.cross(V[T[:,1]]-V[T[:,0]],V[T[:,2]]-V[T[:,0]]);keep=(el>=np.interp(abs(az),BOUND_A,BOUND_E))&(np.einsum('ij,ij->i',cross,Q)>0)&np.isin(data['materialIndex'],(4,5));fi=np.flatnonzero(keep);vi,inv=np.unique(T[fi],return_inverse=True);P=V[vi];F=inv.reshape(-1,3);faceN=unit(np.cross(P[F[:,1]]-P[F[:,0]],P[F[:,2]]-P[F[:,0]]));NN=np.zeros_like(P)
 for j in range(3):np.add.at(NN,F[:,j],faceN)
 NN=unit(NN);tree=BVHTree.FromPolygons(P.tolist(),F.tolist(),all_triangles=True);edges=np.concatenate((F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]));edges.sort(1);edges,ec=np.unique(edges,axis=0,return_counts=True);boundary=np.unique(edges[ec==1]);adj=[[] for _ in P]
 for i,j in edges:
  length=float(np.linalg.norm(P[i]-P[j]));adj[i].append((int(j),length));adj[j].append((int(i),length))
 bq=P[boundary]-CENTER;baz=np.arctan2(bq[:,0],-bq[:,1]);bEl=np.arctan2(bq[:,2],np.linalg.norm(bq[:,:2],axis=1));allowed=abs(baz)>1.25;boundary=boundary[allowed];baz=baz[allowed]
 # Surface-spread authoring roots; guides are a diagnostic scaffold, not follicles.
 selected=[int(np.linalg.norm(P-np.array([-.012,-.085,1.548]),axis=1).argmin())];minimum=np.linalg.norm(P-P[selected[0]],axis=1)**2
 for _ in range(GUIDES-1):
  nxt=int(minimum.argmax());selected.append(nxt);minimum=np.minimum(minimum,np.linalg.norm(P-P[nxt],axis=1)**2)
 def projected(points,lift):
  out=[]
  for p,h in zip(points,lift):
   co,_,f,_=tree.find_nearest(Vector(p));bc=m.rig.base.bary(np.array(co),P[F[f]]);n=unit(bc@NN[F[f]]);out.append(np.array(co)+float(h)*n)
  return np.array(out)
 def route(start,end):
  D=np.full(len(P),np.inf);D[end]=0;parent=np.full(len(P),-1,'i4');heap=[(0.,int(end))]
  while heap:
   dist,v=heapq.heappop(heap)
   if dist>D[v]:continue
   if v==start:break
   for w,cost in adj[v]:
    nd=dist+cost
    if nd<D[w]:D[w]=nd;parent[w]=v;heapq.heappush(heap,(nd,w))
  assert np.isfinite(D[start]),'Scalp domain disconnected; do not drop failed root'
  ids=[start]
  while ids[-1]!=end:ids.append(int(parent[ids[-1]]));assert len(ids)<len(P) and ids[-1]>=0
  return P[ids]
 guides=[];surfaceMasks=[];records=[]
 for gi,start in enumerate(selected):
  root=P[start];q0=root-CENTER;angle=float(np.arctan2(q0[0],-q0[1]));side=-1 if root[0]<-.012 else 1;target=side*(1.40+.13*abs(np.sin(gi*.73))) if abs(angle)<1.25 else angle+.055*np.sin(gi*1.9);error=abs((baz-target+np.pi)%(2*np.pi)-np.pi);end=int(boundary[error.argmin()]);surf=resample(route(start,end),40)
  for _ in range(5):
   surf[1:-1]=(surf[:-2]+2*surf[1:-1]+surf[2:])*.25;surf=projected(surf,np.zeros(len(surf)))
  length=np.linalg.norm(np.diff(surf,axis=0),axis=1).sum();u=np.linspace(0,1,len(surf));lift=.00016+(.008+.002*np.sin(gi*.71))*np.sin(np.pi*u*.5)**2 if length>.001 else np.full(len(surf),.00016);surf=projected(surf,lift);e=surf[-1];aa=abs(float(baz[error.argmin()]));sgn=-1 if e[0]<0 else 1
  if aa<1.67:K=np.array([[sgn*.087,-.073,1.440],[sgn*.094,-.064,1.395],[sgn*.079,-.047,1.337]])
  elif aa<2.22:K=np.array([[sgn*.090,-.024,1.430],[sgn*.099,-.005,1.385],[sgn*.082,.004,1.325]])
  elif aa<2.75:K=np.array([[sgn*.065,.058,1.410],[sgn*.072,.073,1.365],[sgn*.056,.061,1.315]])
  else:K=np.array([[sgn*.014,.062,1.408],[sgn*.020,.075,1.365],[sgn*.008,.064,1.315]])
  # Individual section variation, not a single shared exit/tip station.
  variation=np.array([.003*np.sin(gi*2.4),.003*np.cos(gi*1.7),.006*np.sin(gi*1.1)]);K+=variation;K[:,0]+=.15*(e[0]-sgn*.055);knots=np.vstack((e,K));free=[]
  for j in range(len(knots)-1):
   p0=knots[max(0,j-1)];p1=knots[j];p2=knots[j+1];p3=knots[min(len(knots)-1,j+2)]
   for t in np.linspace(0,1,16,endpoint=False):free.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t))
  free=np.array(free+[knots[-1]]);chain=np.vstack((surf,free[1:]));arcS=np.linalg.norm(np.diff(surf,axis=0),axis=1).sum();arcAll=np.linalg.norm(np.diff(chain,axis=0),axis=1).sum();g=resample(chain,N);mask=np.linspace(0,arcAll,N)<=arcS
  # Reproject smoothed scalp samples, keeping their authored volume offset.
  if mask.sum()>1:g[mask]=projected(g[mask],np.linspace(.00016,float(lift[-1]),int(mask.sum())))
  g[0]=root+NN[start]*.00016;guides.append(g);surfaceMasks.append(mask);records.append({'guide':gi,'scalpVertex':int(start),'actualBodyVertex':int(data['bodyVertexIDs'][vi[start]]),'exitVertex':end,'surfaceRouteArcM':float(length),'partSide':side,'freeKnotsWorldM':knots.tolist(),'rootWorldM':g[0].tolist()})
 guides=np.array(guides);surfaceMasks=np.array(surfaceMasks);assert np.isfinite(guides).all();bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);old=bpy.data.objects['AFN81_EDITABLE_CURLY_GUIDES'];A=old.matrix_world.copy();AA=np.array(A);invA=np.linalg.inv(AA[:3,:3]);old.hide_render=True;old.hide_set(True);mats={x.name:m.rig.k.f.v.v32.material_signature(x) for x in bpy.data.materials if x.use_nodes};lights=m.m.q.lights();cap=mesh('AFN90_TARGET_NATIVE_CONNECTED_SCALP',(P-AA[:3,3])@invA.T,F,A);live.attribute(cap.data,'AFN90_ActualBodyVertex','INT',data['bodyVertexIDs'][vi].astype('i4'));uv=cap.data.uv_layers.new(name='AFN90_ScalpUV');angle=np.arctan2((P-CENTER)[:,0],-(P-CENTER)[:,1]);elev=np.arctan2((P-CENTER)[:,2],np.linalg.norm((P-CENTER)[:,:2],axis=1));UV=np.column_stack(((angle+np.pi)/(2*np.pi),(elev+np.pi/2)/np.pi));loopUV=UV[np.array([l.vertex_index for l in cap.data.loops])]
  # Unwrap each seam-crossing face locally; no interpolation through the rear seam.
 for face in cap.data.polygons:
  ids=np.array(face.loop_indices);values=loopUV[ids,0]
  if values.max()-values.min()>.5:loopUV[ids,0]=np.where(values<.5,values+1,values)
 uv.data.foreach_set('uv',loopUV.astype('f4').ravel());cap['scope']='Actual target render-body scalp triangle subset in artist-designated continuous hairline. Native authoring UV chart, not a follicle scan, solver or contact proxy.';GL=(guides.reshape(-1,3)-AA[:3,3])@invA.T;guide=live.pointmesh('AFN90_INTRINSIC_EDITABLE_GUIDE_CAGES',GL,A,[(i*N+j,i*N+j+1) for i in range(GUIDES) for j in range(N-1)]);guide['scope']='96 editable64-point mesh guide cages; child sampling reads exact cage vertices. Actual target-scalp routes and section free knots. Not hair simulation or native surface-brush attachment.';guide['scalpAuthoringObject']=cap.name
 print('R90_GUIDE_CAGES_READY',flush=True);objects=None if FULL else diagnostic('AFN90_SPARSE_GUIDE_DIAGNOSTIC',guides,A);owners=None;roots=None;expected=guides.copy()
 if FULL:
  rng=np.random.default_rng(900090);area=np.linalg.norm(np.cross(P[F[:,1]]-P[F[:,0]],P[F[:,2]]-P[F[:,0]]),axis=1);faceIDs=rng.choice(len(F),COUNT,p=area/area.sum());uv0=rng.random((COUNT,2));flip=uv0.sum(1)>1;uv0[flip]=1-uv0[flip];BC=np.column_stack((1-uv0.sum(1),uv0));roots=np.einsum('ni,nij->nj',BC,P[F[faceIDs]])+unit(np.einsum('ni,nij->nj',BC,NN[F[faceIDs]]))*.00016;kd=KDTree(GUIDES)
  for i,g in enumerate(guides):kd.insert(Vector(g[0]),i)
  kd.balance();owners=np.array([kd.find(Vector(r))[1] for r in roots],'i4');children=[]
  for ci,(root,owner) in enumerate(zip(roots,owners)):
   g=guides[owner].copy();delta=root-g[0];u=np.linspace(0,1,N);g+=delta[None,:]*(1-.65*smooth(0,1,u))[:,None];mask=surfaceMasks[owner];ids=np.flatnonzero(mask)
   if len(ids)>1:g[ids]=projected(g[ids],np.linspace(.00016,.008,len(ids)))
   tangent=unit(np.gradient(g,axis=0));axis=unit(np.cross(tangent,np.array([0,0,1.])));micro=.00016*np.sin(6*np.pi*u+ci*2.39996)*np.sin(np.pi*u)**2;g+=axis*micro[:,None];g[0]=root;children.append(g)
  expected=np.array(children);objects=native('AFN90_INTRINSIC_RENDER_FIBRES',expected,.0000979784454,A);guide.hide_render=True;guide.hide_set(True);local=(expected-AA[:3,3])@invA.T;GL=(guides-AA[:3,3])@invA.T;meta=live.pointmesh('AFN90_CHILD_GUIDE_REST_OFFSETS',np.zeros((COUNT*N,3)),A);meta.hide_set(True);ids=(owners[:,None]*N+np.arange(N)).ravel().astype('i4');offset=(local-GL[owners]).reshape(-1,3).astype('f4');w=np.ones(COUNT*N,'f4');w[::N]=0;live.attribute(meta.data,'AFN89_GuidePointID','INT',ids);live.attribute(meta.data,'AFN89_ReferenceBundleOffset','FLOAT_VECTOR',offset);live.attribute(meta.data,'AFN89_RegionalWeight','FLOAT',w);dummy=objects.modifiers.new('TEMP_PUBLISHER_SLOT','NODES');dummy.node_group=bpy.data.node_groups.new('AFN81_PUBLISHER_CURLY_PROGRAM_R90_DUMMY','GeometryNodeTree');dummy.show_viewport=dummy.show_render=False;md=live.graph(objects,guide,meta);md.name='AFN90_LIVE_REST_GUIDES';objects.modifiers.remove(dummy);objects['scope']='21908 new actual target-scalp follicles, explicit native64-point POLY fibres at original98micrometre radius;96 editable live rest guides. All actual roots freshly bound. No self/body/continuous contact, natural dynamics or runtime qualification.'
 if FULL:
  body=m.rig.k.mesh(bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING']);attachment=bind(objects,body,body['V'],body['T'],old);bpy.context.view_layer.update();actual=q.hair(objects)
 else:attachment={'scope':'Static sparse diagnostic, no body-follow or root-frame qualification.'};actual=q.arr(guide.data.vertices,'co',len(guide.data.vertices),3).astype('f8')@AA[:3,:3].T+AA[:3,3]
 error=float(np.linalg.norm(actual-expected.reshape(-1,3),axis=1).max());assert error<2e-6;assert {n:m.rig.k.f.v.v32.material_signature(bpy.data.materials[n]) for n in mats}==mats and m.m.q.lights()==lights;m.rig.shade.settings();m.rig.k.b.camera('face');s.camera.data.lens=85;s.render.hair_subdiv=3;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
 tag='a-full' if FULL else 'a-guide';np.savez_compressed(E/(tag+'-lineage.npz'),scalpWorld=P,scalpTriangles=F,scalpActualBodyVertexIDs=data['bodyVertexIDs'][vi],scalpActualBodyTriangleIDs=data['bodyTriangleIDs'][fi],guidesWorld=guides,guideSurfaceMasks=surfaceMasks,actualWorld=actual,counts=np.full(len(expected),N,'i4'),matrix=AA,childOwners=owners if owners is not None else np.empty(0,'i4'),rootsWorld=roots if roots is not None else guides[:,0]);save(tag+'-build-summary.json',{'source':str(SRC),'sourceSha256':sha(SRC),'output':str(OUT),'outputSha256':sha(OUT),'outputBytes':OUT.stat().st_size,'fullFibres':FULL,'guideObject':guide.name,'renderObject':objects.name,'scalpObject':cap.name,'scalpVertices':len(P),'scalpTriangles':len(F),'guides':GUIDES,'guideRecords':records,'actualCurves':len(expected),'actualPoints':len(actual),'pointsEach':N,'curveType':'POLY','guideDiagnosticRadiusWorldM':.0005,'fibreRadiusWorldM':.0000979784454 if FULL else None,'actualNeutralMaximumReadbackErrorM':error,'attachment':attachment,'newFullyQualifiedCompleteCapability':False,'noContactNaturalDynamicsOrRuntimeAcceptance':True,'secondsBeforePreview':time.time()-tick})
 rows=[]
 for view in ('back','face','body-face'):rows.append(views.image(tag,view));save(tag+'-view-controls.json',rows)
 print('R90_INTRINSIC_GROOM_DONE',tag,len(actual),time.time()-tick,flush=True)
if __name__=='__main__':main()
