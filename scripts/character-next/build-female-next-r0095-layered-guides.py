"""Complete authored parent-guide groom with group-aware live child coupling.

Surface-root routes are only the beginning of each guide. Individually stored
3-D shoulder/chest/S-curve landmarks and layered tips replace the old shafts;
root angular coordinates and depth/length continue into the free geometry.
Ordinary guide curves + interpolation, not Hair Meshes/Hair Farm implementation.
No source strand/root removal, density/radius/shader or tolerance sweep.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0095-authored-layered-groom';E94=E.parent/'r0094-authored-growth-routing';S=R/'engine/assets/characters/female-next/source';SRC=S/'aevrynd-female-next-r0094-b-source-width-growth-volume.blend';OUT=S/'aevrynd-female-next-r0095-a-authored-layered-guides.blend'
def mod(n,p):
 sp=importlib.util.spec_from_file_location(n,p);a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);return a
v=mod('r95views',Path(__file__).with_name('render-female-next-r0091-matched.py'));v.E=E;m=v.m;q=m.q
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8')
def unit(v):return v/max(np.linalg.norm(v),1e-12)
def resample(P,N):
 P=np.asarray(P);seg=np.linalg.norm(np.diff(P,axis=0),axis=1);keep=np.r_[True,seg>1e-8];P=P[keep];arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(P,axis=0),axis=1))];u=np.linspace(0,arc[-1],N);j=np.clip(np.searchsorted(arc,u,side='right')-1,0,len(P)-2);a=(u-arc[j])/(arc[j+1]-arc[j]);return P[j]*(1-a[:,None])+P[j+1]*a[:,None]
def smooth_polyline(P):
 P=np.asarray(P);out=[]
 for j in range(len(P)-1):
  a=P[max(j-1,0)];b=P[j];c=P[j+1];d=P[min(j+2,len(P)-1)]
  for t in np.linspace(0,1,5,endpoint=False):out.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
 return np.array(out+[P[-1]])
def frames(P,rootNormal):
 T=np.diff(P,axis=0);T=np.vstack((T,T[-1]));T/=np.maximum(np.linalg.norm(T,axis=1)[:,None],1e-12);N=np.empty_like(T);N[0]=unit(rootNormal-T[0]*np.dot(rootNormal,T[0]))
 if np.linalg.norm(N[0])<.1:N[0]=unit(np.cross(T[0],(0,1,0)))
 for i in range(1,len(T)):N[i]=unit(N[i-1]-T[i]*np.dot(N[i-1],T[i]))
 B=np.cross(T,N);return np.stack((T,N,B),axis=2)
def live_modifier(hair,guide,indices,weights,offset):
 d=hair.data
 for j in range(4):
  a=d.attributes.new('AFN95_Guide'+str(j),'INT','CURVE');a.data.foreach_set('value',indices[:,j]);a=d.attributes.new('AFN95_Weight'+str(j),'FLOAT','CURVE');a.data.foreach_set('value',weights[:,j].astype('f4'))
 a=d.attributes.new('AFN95_TransportedChildOffset','FLOAT_VECTOR','POINT');a.data.foreach_set('vector',offset.astype('f4').ravel());ng=bpy.data.node_groups.new('AFN95_LIVE_AUTHORED_GUIDES_TO_ALL_CHILDREN','GeometryNodeTree');ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');n=ng.nodes;L=ng.links;i=n.new('NodeGroupInput');out=n.new('NodeGroupOutput');info=n.new('GeometryNodeObjectInfo');info.transform_space='RELATIVE';info.inputs['Object'].default_value=guide;info.inputs['As Instance'].default_value=False;pos=n.new('GeometryNodeInputPosition');ix=n.new('GeometryNodeInputIndex');point=n.new('ShaderNodeMath');point.operation='PINGPONG';point.operation='MODULO';point.inputs[1].default_value=33;L.new(ix.outputs['Index'],point.inputs[0])
 def named(name,kind):
  a=n.new('GeometryNodeInputNamedAttribute');a.data_type=kind;a.inputs['Name'].default_value=name;return a.outputs['Attribute']
 def vec(op,a,b):
  x=n.new('ShaderNodeVectorMath');x.operation=op;L.new(a,x.inputs[0]);L.new(b,x.inputs[3] if op=='SCALE' else x.inputs[1]);return x.outputs['Vector']
 total=named('AFN95_TransportedChildOffset','FLOAT_VECTOR')
 for j in range(4):
  mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=33;L.new(named('AFN95_Guide'+str(j),'INT'),mul.inputs[0]);add=n.new('ShaderNodeMath');add.operation='ADD';L.new(mul.outputs[0],add.inputs[0]);L.new(point.outputs[0],add.inputs[1]);sample=n.new('GeometryNodeSampleIndex');sample.data_type='FLOAT_VECTOR';sample.domain='POINT';sample.clamp=False;L.new(info.outputs['Geometry'],sample.inputs['Geometry']);L.new(pos.outputs['Position'],sample.inputs['Value']);L.new(add.outputs[0],sample.inputs['Index']);weighted=vec('SCALE',sample.outputs['Value'],named('AFN95_Weight'+str(j),'FLOAT'));total=vec('ADD',total,weighted)
 setpos=n.new('GeometryNodeSetPosition');L.new(i.outputs['Geometry'],setpos.inputs['Geometry']);L.new(total,setpos.inputs['Position']);L.new(setpos.outputs['Geometry'],out.inputs['Geometry']);md=hair.modifiers.new('AFN95_LIVE_GUIDE_EDITING','NODES');md.node_group=ng
def main():
 tick=time.time();assert not OUT.exists() and sha(SRC)=='72380d7007379598372d501bdeca7c97e346f87fe59e2408cf4b9f06bf8790dd';bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();old=bpy.data.objects['AFN94_SOURCE_WIDTH_RENDER_FIBRES'];P=q.hair(old).reshape(-1,33,3);roots=P[:,0].copy();A=np.array(old.matrix_world);inv=np.linalg.inv(A[:3,:3]);z=np.load(E94/'a-growth-volume-lineage.npz');normal=z['rootNormals'];body=m.rig.k.mesh(bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING']);V,T=body['V'],body['T'];eligible=np.flatnonzero(np.isin(body['nativeTriangleFace'],z['allowedNativeFaces']));scalp=BVHTree.FromPolygons(V.tolist(),T[eligible].tolist(),all_triangles=True);actualBody=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True);rad=q.arr(old.data.attributes['radius'].data,'value',P.size//3).reshape(-1,33);radiusWorld=rad[:,0]*np.linalg.norm(A[:3,0]);G=[];controls=[];routeRows=[];cy=-.04
 def ray_landmark(theta,zvalue,lift):
  direction=np.array((math.sin(theta),math.cos(theta),0.));origin=np.array((0.,cy,zvalue));hit=actualBody.ray_cast(Vector(origin),Vector(direction),.4)
  if hit[0] is None:return origin+direction*.11+np.array((0,0,0)),False
  return np.array(hit[0])+np.array(hit[1])*lift,True
 for g,root in enumerate(roots[:1077]):
  side=1 if root[0]>=0 else -1;phi=math.atan2(abs(root[0]),root[1]-cy);front=phi>math.pi/2;u=(phi-math.pi/2)/(math.pi/2) if front else phi/(math.pi/2);u=float(np.clip(u,0,1));layer=float(np.clip((root[2]-1.41)/.15,0,1));exitPhi=.18+1.6*(phi/math.pi)**.65;exitZ=min(1.445,root[2]-.015);desired=np.array((side*.078*math.sin(exitPhi),cy+.078*math.cos(exitPhi),exitZ));foot,nn,fi,dist=scalp.find_nearest(Vector(desired));exitFoot=np.array(foot);p=root-normal[g]*radiusWorld[g];route=[root.copy()];travel=0.;previous=p.copy()
  for k in range(75):
   co,no,face,dist=scalp.find_nearest(Vector(p));no=np.array(no);direction=exitFoot-p;direction-=no*np.dot(direction,no)
   if np.linalg.norm(direction)<.0015:break
   trial=p+unit(direction)*min(.003,np.linalg.norm(direction));co,no,face,dist=scalp.find_nearest(Vector(trial));p=np.array(co);step=np.linalg.norm(p-previous)
   if step<.00025:break
   travel+=step;previous=p.copy();lift=.0002+.0055*(1-math.exp(-travel/.025));route.append(p+np.array(no)*(radiusWorld[g]+lift))
   if np.linalg.norm(p-exitFoot)<.0025:break
  release=route[-1];freePhi=(1.95+.85*u) if front else (.05+1.15*u);phase=phi*1.7+layer*2.;tipZ=1.085+.155*(1-layer)+(.025*u if front else 0.);z1=min(release[2]-.035,1.365);zz=np.linspace(z1,tipZ,5);free=[release];hits=0
  for j,zvalue in enumerate(zz):
   angle=side*(freePhi+.11*math.sin(phase+j*math.pi*.85));lift=.018+.009*math.sin(phase+j*math.pi*.8);point,hit=ray_landmark(angle,float(zvalue),lift);hits+=hit;point[2]=zvalue;free.append(point)
  # Every guide's angular coordinate, layer depth and tip height stay in its
  # own controls. No shared endpoint or collapsed section for a root family.
  tail=smooth_polyline(free);curve=resample(np.vstack((route,tail[1:])),33);curve[0]=root;G.append(curve);controls.append(free);routeRows.append({'guide':g,'region':('front' if front else 'back')+('-R' if side>0 else '-L'),'rootAngularU':u,'layer':layer,'surfaceRoutePoints':len(route),'surfaceRouteLengthM':travel,'actualBodyLandmarkHits':hits,'tipWorld':curve[-1].tolist()})
 G=np.array(G);assert np.isfinite(G).all();print('R95_AUTHORED_PARENT_GUIDES_READY',G.shape,flush=True);group=(roots[:,0]>=0).astype('i4')*2+(roots[:,1]<cy).astype('i4');trees={}
 for part in range(4):
  ids=np.flatnonzero(group[:1077]==part);assert len(ids)>=4;tree=KDTree(len(ids))
  for i in ids:tree.insert(Vector(roots[i]),int(i))
  tree.balance();trees[part]=tree
 ids=np.zeros((len(P),4),'i4');weights=np.zeros((len(P),4));offset=np.empty_like(P);Q=np.empty_like(P)
 for i,root in enumerate(roots):
  if i<1077:ids[i]=i;weights[i,0]=1
  else:
   near=trees[int(group[i])].find_n(Vector(root),4);ids[i]=[n[1] for n in near];distance=np.array([n[2] for n in near]);w=1/np.maximum(distance,.0001)**2;weights[i]=w/w.sum()
  centre=np.einsum('i,ijk->jk',weights[i],G[ids[i]]);frame=frames(centre,normal[i]);rootOffset=root-centre[0];local=frame[0].T@rootOffset;off=np.einsum('nij,j->ni',frame,local);offset[i]=off;Q[i]=centre+off;Q[i,0]=root
 localGuides=(G.reshape(-1,3)-A[:3,3])@inv.T;mesh=bpy.data.meshes.new('AFN95_AUTHORED_PARENT_GUIDE_CONTROLS');edges=[(g*33+j,g*33+j+1) for g in range(1077) for j in range(32)];mesh.from_pydata(localGuides.tolist(),edges,[]);mesh.update();guide=bpy.data.objects.new(mesh.name,mesh);s.collection.objects.link(guide);guide.matrix_world=old.matrix_world.copy();guide.hide_render=True;guide.hide_set(True);guide['instructions']='Edit these1077 complete33-point parent polylines in neutral pose; AFN95 live output interpolates their points to every original child. Roots/normal-frame correction must be revalidated after root or large shape edits. No dynamics or pose follow acceptance.'
 d=old.data.copy();d.name='AFN95_GUIDE_DRIVEN_RENDER_CURVES';d.position_data.foreach_set('vector',((Q.reshape(-1,3)-A[:3,3])@inv.T).astype('f4').ravel());d.attributes['curve_type'].data.foreach_set('value',np.zeros(len(P),'i4'));hair=bpy.data.objects.new('AFN95_AUTHORED_LAYERED_RENDER_FIBRES',d);s.collection.objects.link(hair);hair.matrix_world=old.matrix_world.copy();localOffset=offset@inv.T;live_modifier(hair,guide,ids,weights,localOffset);old.hide_render=True;old.hide_set(True);hair['scope']='Complete newly authored1077 parent paths: source-semantic scalp route plus individual3-D actual-body shoulder/chest landmarks, S-shaped free sections and layered tips; group-aware4-guide interpolation and transported child root cross-sections drive all28002 original roots/strands live. Native CatmullRom display type0. Static appearance pilot; no exact render-contact, finite shaft/self/CCD, natural movement, full pose follow or engine acceptance.';bpy.context.view_layer.update();actual=q.hair(hair).reshape(Q.shape);error=float(np.linalg.norm(actual-Q,axis=2).max());assert error<3e-6,error;m.rig.shade.settings();m.rig.k.b.camera('face');s.camera.data.lens=85;s.render.hair_subdiv=3;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);np.savez_compressed(E/'a-authored-groom-lineage.npz',sourceWorld=P.astype('f4'),guideWorld=G.astype('f4'),actualWorld=Q.astype('f4'),guideIndices=ids,guideWeights=weights.astype('f4'),transportedChildOffsetWorld=offset.astype('f4'),rootGroup=group,rootTriangle=z['rootBodyTriangle'],rootBarycentric=z['rootBarycentric'],rootNormals=normal,allowedNativeFaces=z['allowedNativeFaces'],objectMatrix=A,radiusNative=rad);save('a-authored-guide-controls.json',routeRows);save('a-build-summary.json',{'source':str(SRC),'sourceSha256':sha(SRC),'output':str(OUT),'outputSha256':sha(OUT),'outputBytes':OUT.stat().st_size,'guideObject':guide.name,'curveObject':hair.name,'sourceStrands':28002,'authoredGuides':1077,'pointsEach':33,'curveType':'Native CatmullRom0; actual Cycles swept occupancy not independently certified.','allOriginalRootsStrandsAndCorrectedWidthsRetained':True,'sourceRootMaximumWorldErrorM':float(np.linalg.norm(actual[:,0]-roots,axis=1).max()),'actualLiveGuideOutputMaximumWorldErrorM':error,'regions':{str(k):int((group==k).sum()) for k in range(4)},'guideTipUniqueCount':len(np.unique(G[:,-1].round(7),axis=0)),'construction':'Individually stored complete scalp-to-tip parent paths, actual semantic scalp routes, body-derived3D shoulder/chest/S-section control landmarks and layered lengths; group-aware live interpolation plus transported child cross-sections. No unchanged-source-guide field/particle fit or shared XYZ-family endpoint.','newDynamicsContactRuntimeOrCompleteGainAccepted':False,'secondsBeforePreview':time.time()-tick});rows=[]
 for view in ['face','back','body-face']:rows.append(v.image('a-layered-guides',view));save('a-view-controls.json',rows)
 print('R95_COMPLETE_LAYERED_GUIDE_PREVIEW',time.time()-tick,flush=True)
if __name__=='__main__':main()
