"""Replace the native socket disc with an explicitly open movable lid cup.
Original C outer body vertices/UVs are retained. Anatomical new faces join its
actual fine boundary by shared vertex IDs; the old cap is not front-projected.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time,collections
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0101-articulated-eyelid-topology';S=R/'engine/assets/characters/female-next/source';SRC=S/'aevrynd-female-next-r0099-c-continuous-artist-body.blend';OUT=S/'aevrynd-female-next-r0101-a-articulated-eyelids.blend'
sp=importlib.util.spec_from_file_location('r101art',Path(__file__).with_name('build-female-next-r0098-native-head.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);q=m.q;v=m.v;v.E=E
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8')
def tree_of(o):
 d,P=q.geom(o);d.calc_loop_triangles();T=q.arr(d.loop_triangles,'vertices',len(d.loop_triangles),3,dtype='i4');return BVHTree.FromPolygons(P.tolist(),T.tolist(),all_triangles=True),P
def fit_reference():
 p=S/'aevrynd-female-next-r0097-neutral-scalp-control-reference.blend';bpy.ops.wm.open_mainfile(filepath=str(p));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();d,P=q.geom(bpy.data.objects['AFN74_SKIN_AND_EXISTING_OCULAR_LINING']);d.calc_loop_triangles();T=q.arr(d.loop_triangles,'vertices',len(d.loop_triangles),3,dtype='i4');refs={}
 for side in ['L','R']:
  eye,EV=tree_of(bpy.data.objects['AFN60_'+side+'_EYE_OUTER_SHELL_APPROX']);c=(EV.min(0)+EV.max(0))/2;centres=P[T].mean(1);keep=(abs(centres[:,0]-c[0])<.025)&(abs(centres[:,2]-c[2])<.026);skin=BVHTree.FromPolygons(P.tolist(),T[keep].tolist(),all_triangles=True);xs=np.linspace(c[0]-.014,c[0]+.014,81);zs=np.linspace(c[2]-.012,c[2]+.012,161);mask=np.zeros((len(xs),len(zs)),bool)
  for i,x in enumerate(xs):
   for j,z in enumerate(zs):
    origin=Vector((x,-.2,z));ep,*_=eye.ray_cast(origin,Vector((0,1,0)),.2)
    if ep is None:continue
    hp,*_=skin.ray_cast(origin,Vector((0,1,0)),.2)
    mask[i,j]=hp is not None and hp.y>c[1]
  seed=(40,80);assert mask[seed],('Reference centre has no posterior socket separation',side);component={seed};queue=collections.deque([seed])
  while queue:
   i,j=queue.popleft()
   for a,b in [(i-1,j),(i+1,j),(i,j-1),(i,j+1)]:
    if 0<=a<len(xs) and 0<=b<len(zs) and mask[a,b] and (a,b) not in component:component.add((a,b));queue.append((a,b))
  columns=sorted({i for i,j in component});data=[]
  for i in columns:
   zi=[j for ii,j in component if ii==i];data.append([xs[i],zs[min(zi)],zs[max(zi)]])
  data=np.array(data);data=data if side=='L' else data[::-1];x0,x1=data[0,0],data[-1,0];u=(data[:,0]-x0)/(x1-x0);end0=data[0,1:].mean();end1=data[-1,1:].mean();line=(1-u)*end0+u*end1;basis=np.column_stack([np.sin(np.pi*u)*((2*u-1)**k) for k in range(3)]);upper=np.linalg.lstsq(basis,data[:,2]-line,rcond=None)[0];lower=np.linalg.lstsq(basis,data[:,1]-line,rcond=None)[0];refs[side]={'x0':x0,'x1':x1,'z0':end0,'z1':end1,'upper':upper,'lower':lower,'sampledContour':data,'rayCount':int(mask.size),'actualSkinReference':str(p),'referenceSha256':hashlib.sha256(p.read_bytes()).hexdigest(),'scope':'Evaluated r97 skin front/rear pocket separation contour, then one fitted authoring guide. Not a measured human aperture or contact certificate.'}
 save('actual-r97-render-skin-contour-guide.json',refs);return refs
def order_cycle(ids,adj,P):
 ids=set(map(int,ids));start=min(ids,key=lambda i:abs(P[i,0]));end=max(ids,key=lambda i:abs(P[i,0]))
 def dfs(path,used):
  if len(path)==len(ids):return path if start in adj[path[-1]] else None
  for j in sorted((adj[path[-1]]&ids)-used):
   r=dfs(path+[j],used|{j})
   if r is not None:return r
  return None
 loop=dfs([start],{start});assert loop is not None;at=loop.index(end);a=loop[:at+1];b=[start]+loop[:at-1:-1]
 if P[a,2].mean()<P[b,2].mean():a,b=b,a
 return np.array(a+b[-2:0:-1],'i4'),len(a)-1
def slerp(a,b,t):
 dot=np.clip(np.sum(a*b,axis=1),-.999999,.999999);angle=np.arccos(dot);out=(np.sin((1-t)*angle)[:,None]*a+np.sin(t*angle)[:,None]*b)/np.sin(angle)[:,None];return out/np.linalg.norm(out,axis=1)[:,None]
def main():
 tick=time.time();assert not OUT.exists();refs=fit_reference();bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();control=bpy.data.objects['AFN99_ORIGINAL_CONTINUOUS_ARTIST_SKIN'];cd,C=q.geom(control);cd.calc_loop_triangles();CT=q.arr(cd.loop_triangles,'vertices',len(cd.loop_triangles),3,dtype='i4');CL=q.arr(cd.loop_triangles,'loops',len(cd.loop_triangles),3,dtype='i4');UV={u.name:q.arr(u.data,'uv',len(u.data),2)[CL].copy() for u in cd.uv_layers};MI=q.arr(cd.polygons,'material_index',len(cd.polygons),dtype='i4');materials=list(control.data.materials);A=np.array(control.matrix_world);AI=np.linalg.inv(A[:3,:3]);to_local=lambda p:(p-A[:3,3])@AI.T
 donor0=bpy.data.objects['AFN99_ORIGINAL_ARTIST_FULL_SOURCE'];donor=donor0.copy();donor.data=donor0.data.copy();s.collection.objects.link(donor);donor.name='AFN101_NATIVE_SOCKET_FACE_MAP_SOURCE';donor.hide_render=True;donor.hide_set(True);d=donor.data;d.attributes.new('AFN101_SourceFaceID','INT','FACE').data.foreach_set('value',np.arange(len(d.polygons),dtype='i4'));base=q.arr(d.vertices,'co',len(d.vertices),3);edges=q.arr(d.edges,'vertices',len(d.edges),2,dtype='i4');adj=[set() for _ in base]
 for a,b in edges:adj[a].add(int(b));adj[b].add(int(a))
 selected=json.loads((E.parent/'r0100-native-eyelid-assembly/a-actual-native-rim-selection.json').read_text('utf8'));W=np.load(E.parent/'r0100-native-eyelid-assembly/native-eye-topology.npz')['baseAlignedWorld'];blocked=set();nativeLoops={}
 for side in ['L','R']:
  loop,k=order_cycle(selected[side],adj,W);nativeLoops[side]=loop
  blocked|={tuple(sorted((int(a),int(b)))) for a,b in zip(loop,np.roll(loop,-1))}
 edgeFaces={}
 for face in d.polygons:
  vv=list(face.vertices)
  for a,b in zip(vv,vv[1:]+vv[:1]):edgeFaces.setdefault(tuple(sorted((a,b))),[]).append(face.index)
 dual=[set() for _ in d.polygons]
 for edge,faces in edgeFaces.items():
  if edge not in blocked and len(faces)==2:a,b=faces;dual[a].add(b);dual[b].add(a)
 remaining=set(range(len(dual)));components=[]
 while remaining:
  seed=next(iter(remaining));seen={seed};queue=[seed]
  while queue:
   for j in dual[queue.pop()]-seen:seen.add(j);queue.append(j)
  remaining-=seen;components.append(seen)
 components.sort(key=len,reverse=True);assert len(components)==3,[len(c) for c in components];assert all(len(c)<1000 for c in components[1:]);removedBase=np.array(sorted(set.union(*components[1:])),'i4');bpy.context.view_layer.update();dd,DP=q.geom(donor);dd.calc_loop_triangles();DT=q.arr(dd.loop_triangles,'vertices',len(dd.loop_triangles),3,dtype='i4');assert np.array_equal(DT,CT),'Actual source fine triangle correspondence changed';tag=q.arr(dd.attributes['AFN101_SourceFaceID'].data,'value',len(dd.polygons),dtype='i4');pf=q.arr(dd.loop_triangles,'polygon_index',len(DT),dtype='i4');remove=np.isin(tag[pf],removedBase);assert 1000<remove.sum()<200000
 allEdges=np.sort(np.concatenate([CT[remove][:,[0,1]],CT[remove][:,[1,2]],CT[remove][:,[2,0]]]),axis=1);ue,count=np.unique(allEdges,axis=0,return_counts=True);boundary=ue[count==1];fa={}
 for a,b in boundary:fa.setdefault(int(a),set()).add(int(b));fa.setdefault(int(b),set()).add(int(a))
 assert all(len(x)==2 for x in fa.values());unseen=set(fa);fineLoops=[]
 while unseen:
  seed=next(iter(unseen));comp={seed};queue=[seed]
  while queue:
   for j in fa[queue.pop()]-comp:comp.add(j);queue.append(j)
  unseen-=comp;loop,k=order_cycle(comp,fa,C);fineLoops.append((loop,k))
 assert len(fineLoops)==2
 # All original C points remain as correspondence controls; deleted socket
 # faces are anatomically replaced. Unused cap points are not rendered and
 # must be removed/remapped by a later qualified runtime export.
 P=[];PC=[];pointSide=[];bind=[];follow=[];clear=[];adhere=[];centres=[];patchFaces=[];patchMat=[];hmap={};HP=[];HPC=[];Hside=[];perEye=[];outerSet=set(map(int,boundary.ravel()));outsideEdge={}
 for tri in CT[~remove]:
  for a,b in zip(tri,np.roll(tri,-1)):
   if int(a) in outerSet and int(b) in outerSet:outsideEdge[tuple(sorted((int(a),int(b))))]=(int(a),int(b))
 def guide(i):
  i=int(i)
  if i not in hmap:hmap[i]=len(HP);HP.append(C[i]);HPC.append(C[i]);Hside.append(0)
 def points(opened,closed,side,boundIDs,weights,gaps,conform,centre):
  ids=np.arange(len(C)+len(P),len(C)+len(P)+len(opened),dtype='i4')
  for i,p,pc,b,w,g,at in zip(ids,opened,closed,boundIDs,weights,gaps,conform):hmap[int(i)]=len(HP);HP.append(p);HPC.append(pc);Hside.append(1 if side=='L' else -1);P.append(p);PC.append(pc);pointSide.append(1 if side=='L' else -1);bind.append(b);follow.append(w);clear.append(g);adhere.append(at);centres.append(centre)
  return ids
 def stitch(a,pa,b,pb):
  faces=[];i=j=0
  while i<len(a) or j<len(b):
   aa=int(a[i%len(a)]);bb=int(b[j%len(b)]);na=pa[(i+1)%len(a)]+(1 if i+1>=len(a) else 0);nb=pb[(j+1)%len(b)]+(1 if j+1>=len(b) else 0)
   if j==len(b) or (i<len(a) and na<=nb):faces.append([aa,bb,int(a[(i+1)%len(a)])]);i+=1
   else:faces.append([aa,bb,int(b[(j+1)%len(b)])]);j+=1
  return faces
 for loop,k in fineLoops:
  side='L' if C[loop,0].mean()>0 else 'R';rr=refs[side];eye,EV=tree_of(bpy.data.objects['AFN60_'+side+'_EYE_OUTER_SHELL_APPROX']);fit=json.loads((E.parent/'r0100-native-eyelid-assembly/native-eye-topology.json').read_text('utf8'))['eyes'][side];centre=np.array(fit['posteriorSphereFitCentreWorld']);N=160;half=N//2;t=np.r_[np.linspace(0,1,half+1),np.linspace(1,0,half+1)[1:-1]];u=(1-np.cos(np.pi*t))/2;upper=np.arange(N)<=half;basis=np.column_stack([np.sin(np.pi*u)*(2*u-1)**j for j in range(3)]);line=(1-u)*rr['z0']+u*rr['z1'];zu=line+basis@rr['upper'];zl=line+basis@rr['lower'];x=(1-u)*rr['x0']+u*rr['x1'];z=np.where(upper,zu,zl);closedZ=zl+.18*(zu-zl);margin=np.c_[x,np.zeros(N),z];closed=np.c_[x,np.zeros(N),closedZ]
  def anterior(pts,gap):
   out=pts.copy()
   for i,p in enumerate(pts):
    hit,*_=eye.ray_cast(Vector((p[0],-.2,p[2])),Vector((0,1,0)),.2)
    if hit is None:out[i,1]=C[loop[np.argmin(np.linalg.norm(C[loop][:,[0,2]]-p[[0,2]],axis=1))],1]
    else:out[i,1]=hit.y-gap
   return out
  margin=anterior(margin,.00035);closed=anterior(closed,.00035);back=anterior(margin,.00010);backClosed=anterior(closed,.00010)
  par1=np.r_[0,np.cumsum(np.linalg.norm(np.diff(C[loop[:k+1]],axis=0),axis=1))];par1=.5*par1/par1[-1];tail=np.r_[loop[k:],loop[:1]];par2=np.r_[0,np.cumsum(np.linalg.norm(np.diff(C[tail],axis=0),axis=1))];par2=.5+.5*par2/par2[-1];param=np.r_[par1,par2[1:-1]];assert len(param)==len(loop);newParam=np.arange(N)/N;extended=np.r_[param,1];outer=np.vstack((C[loop],C[loop[:1]]));interp=np.column_stack([np.interp(newParam,extended,outer[:,j]) for j in range(3)]);nearest=np.argmin(abs(param[:,None]-newParam[None,:]),axis=0);boundIDs=loop[nearest]
  for i in loop:guide(i)
  start=len(patchFaces);mid=points(.55*interp+.45*margin,.55*interp+.45*closed,side,boundIDs,np.full(N,.55),np.full(N,.00035),np.full(N,.45),centre);ring=points(margin,closed,side,boundIDs,np.zeros(N),np.full(N,.00035),np.ones(N),centre);inner=points(back,backClosed,side,boundIDs,np.zeros(N),np.full(N,.00010),np.ones(N),centre)
  fs=stitch(loop,param,mid,newParam)+stitch(mid,newParam,ring,newParam);patchFaces+=fs;patchMat += [4]*len(fs);fs=stitch(ring,newParam,inner,newParam);patchFaces+=fs;patchMat += [7]*len(fs)
  startDir=back-centre;startDir/=np.linalg.norm(startDir,axis=1)[:,None];closedDir=backClosed-centre;closedDir/=np.linalg.norm(closedDir,axis=1)[:,None];phi=np.arctan2(back[:,2]-centre[2],back[:,0]-centre[0]);equator=np.c_[np.cos(phi),np.zeros(N),np.sin(phi)];posterior=np.c_[np.sin(.12)*np.cos(phi),np.full(N,np.cos(.12)),np.sin(.12)*np.sin(phi)];previous=inner;radius=fit['posteriorSphereRadiusM']
  for part in range(2):
   for step in range(1,17):
    f=step/16;a=startDir if part==0 else equator;b=equator if part==0 else posterior;ac=closedDir if part==0 else equator;direction=slerp(a,b,f);dc=slerp(ac,b,f);pp=centre+direction*(radius+.00010);cc=centre+dc*(radius+.00010);row=points(pp,cc,side,boundIDs,np.zeros(N),np.full(N,.00010),np.ones(N),centre);fs=stitch(previous,newParam,row,newParam);patchFaces+=fs;patchMat += [4]*len(fs);previous=row
  cap=points(np.array([centre+[0,radius+.00010,0]]),np.array([centre+[0,radius+.00010,0]]),side,np.array([loop[0]]),np.zeros(1),np.full(1,.00010),np.ones(1),centre)[0];patchFaces += [[int(previous[i]),int(cap),int(previous[(i+1)%N])] for i in range(N)];patchMat += [4]*N
  # Orient all replacement faces against the retained original seam.
  flip=None
  for tri in patchFaces[start:]:
   for a,b in zip(tri,tri[1:]+tri[:1]):
    key=tuple(sorted((a,b)))
    if key in outsideEdge:flip=(a,b)==outsideEdge[key];break
   if flip is not None:break
  assert flip is not None
  if flip:
   for tri in patchFaces[start:]:tri[1],tri[2]=tri[2],tri[1]
  perEye.append({'side':side,'actualFineBoundaryVertices':len(loop),'marginVertices':N,'liningMeridianRows':32,'newFaces':len(patchFaces)-start,'contourGuide':rr,'finiteMarginThicknessM':.00025})
 P=np.array(P);PC=np.array(PC);HP=np.array(HP);HPC=np.array(HPC);newV=np.vstack((C,P));newT=np.vstack((CT[~remove],np.array(patchFaces,'i4')));mesh=bpy.data.meshes.new('AFN101_CONTINUOUS_WOMAN_WITH_ARTICULATED_LIDS');mesh.from_pydata(to_local(newV).tolist(),[],newT.tolist());mesh.update();skin=bpy.data.objects.new(mesh.name,mesh);s.collection.objects.link(skin);skin.matrix_world=control.matrix_world.copy()
 for material in materials:mesh.materials.append(material)
 mesh.polygons.foreach_set('material_index',np.r_[MI[~remove],patchMat].astype('i4'));mesh.polygons.foreach_set('use_smooth',np.ones(len(newT),bool))
 # Inherit original outer skin UV and extrapolate only the new narrow lid.
 sourceTree=BVHTree.FromPolygons(C.tolist(),CT[~remove].tolist(),all_triangles=True);retainedTriangles=CT[~remove]
 uvPatch={name:np.zeros((len(newV),2),'f4') for name in UV};retainedUV={name:uv[~remove] for name,uv in UV.items()}
 for i,p in enumerate(P):
  hit,no,fi,dist=sourceTree.find_nearest(Vector(p));tri=retainedTriangles[fi];a=C[tri[1]]-C[tri[0]];b=C[tri[2]]-C[tri[0]];basis=np.column_stack((a,b));xy=np.linalg.lstsq(basis,p-C[tri[0]],rcond=None)[0];weights=np.array([1-xy.sum(),*xy])
  for name,uv in UV.items():uvPatch[name][len(C)+i]=weights@retainedUV[name][fi]
 for name,uv in UV.items():
  # New faces use shared original boundary vertex UV from an outside face.
  vv=np.zeros((len(C),2),'f4');vv[retainedTriangles.ravel()]=uv[~remove].reshape(-1,2);uvPatch[name][:len(C)]=vv;values=np.concatenate([uv[~remove],uvPatch[name][np.array(patchFaces,'i4')]]);mesh.uv_layers.new(name=name).data.foreach_set('uv',values.reshape(-1,2).ravel())
 mesh.uv_layers.active=mesh.uv_layers['VitruvianUV.UDIM'];mesh.uv_layers['VitruvianUV.UDIM'].active_render=True
 hm=bpy.data.meshes.new('AFN101_EDITABLE_LID_AND_SOCKET_COMPONENT');hm.from_pydata(to_local(HP).tolist(),[],[[hmap[i] for i in tri] for tri in patchFaces]);hm.update();helper=bpy.data.objects.new(hm.name,hm);s.collection.objects.link(helper);helper.matrix_world=skin.matrix_world.copy();helper.hide_render=True;helper.hide_set(True);helper.shape_key_add(name='Basis');face=bpy.data.objects['AFN59_FACE_CONTROLS']
 for side,sign,key in [('L',1,'blink_left'),('R',-1,'blink_right')]:
  kb=helper.shape_key_add(name='AFN101_Closed_'+side);pos=HP.copy();sel=np.array(Hside)==sign;pos[sel]=HPC[sel];kb.data.foreach_set('co',to_local(pos).astype('f4').ravel());dr=kb.driver_add('value').driver;dr.type='SCRIPTED';var=dr.variables.new();var.name='blink';var.targets[0].id=face;var.targets[0].data_path='["'+key+'"]';dr.expression='min(1,max(0,blink))'
 nold=len(C);nnew=len(P);N=nold+nnew
 def attr(name,kind,values,prop='value'):
  mesh.attributes.new('AFN101_'+name,kind,'POINT').data.foreach_set(prop,np.asarray(values).ravel())
 attr('OriginalCIndex','INT',np.r_[np.arange(nold),np.full(nnew,-1)].astype('i4'));attr('PatchIndex','INT',np.r_[np.zeros(nold),[hmap[nold+i] for i in range(nnew)]].astype('i4'));attr('BindIndex','INT',np.r_[np.zeros(nold),bind].astype('i4'));attr('FollowWeight','FLOAT',np.r_[np.zeros(nold),follow].astype('f4'));attr('Conform','FLOAT',np.r_[np.zeros(nold),adhere].astype('f4'));attr('Clearance','FLOAT',np.r_[np.zeros(nold),np.array(clear)/A[0,0]].astype('f4'));attr('Side','FLOAT',np.r_[np.zeros(nold),pointSide].astype('f4'));attr('EyeCentre','FLOAT_VECTOR',np.vstack((np.zeros((nold,3)),to_local(np.array(centres)))).astype('f4'),'vector');attr('BindRest','FLOAT_VECTOR',np.vstack((np.zeros((nold,3)),to_local(C[np.array(bind)]))).astype('f4'),'vector')
 am=bpy.data.meshes.new('AFN101_HEAD_AFFINE_BASIS');am.from_pydata([(0,0,0),(1,0,0),(0,1,0),(0,0,1)],[],[]);anchor=bpy.data.objects.new(am.name,am);s.collection.objects.link(anchor);anchor.parent=bpy.data.objects['AFN69_BODY_CONTROLS'];anchor.parent_type='BONE';anchor.parent_bone='Head';bpy.context.view_layer.update();anchor.matrix_world=skin.matrix_world.copy();anchor.hide_render=True;anchor.hide_set(True);bpy.context.view_layer.update();ng,n,L=m.interface('AFN101_JOINED_ANATOMICAL_LID_COMPONENT');inp=n.new('NodeGroupInput');out=n.new('NodeGroupOutput');position=n.new('GeometryNodeInputPosition')
 def info(ob):
  nd=n.new('GeometryNodeObjectInfo');nd.transform_space='RELATIVE';nd.inputs['Object'].default_value=ob;return nd.outputs['Geometry']
 def named(name,kind='FLOAT'):
  nd=n.new('GeometryNodeInputNamedAttribute');nd.data_type=kind;nd.inputs['Name'].default_value='AFN101_'+name;return nd.outputs['Attribute']
 def sample(geometry,index):
  nd=n.new('GeometryNodeSampleIndex');nd.data_type='FLOAT_VECTOR';nd.domain='POINT';L.new(geometry,nd.inputs['Geometry']);L.new(position.outputs['Position'],nd.inputs['Value'])
  if isinstance(index,int):nd.inputs['Index'].default_value=index
  else:L.new(index,nd.inputs['Index'])
  return nd.outputs['Value']
 def vec(op,a,b=None,scalar=None):
  nd=n.new('ShaderNodeVectorMath');nd.operation=op;L.new(a,nd.inputs[0])
  if b is not None:L.new(b,nd.inputs[1])
  if scalar is not None:L.new(scalar,nd.inputs['Scale'])
  return nd.outputs['Vector']
 ag=info(anchor);origin=sample(ag,0);axes=[vec('SUBTRACT',sample(ag,i),origin) for i in [1,2,3]]
 def transform(p):
  sep=n.new('ShaderNodeSeparateXYZ');L.new(p,sep.inputs[0]);terms=[vec('SCALE',axes[i],scalar=sep.outputs[i]) for i in range(3)];return vec('ADD',origin,vec('ADD',terms[0],vec('ADD',terms[1],terms[2])))
 cg=info(control);origIndex=named('OriginalCIndex','INT');sourcePosition=sample(cg,origIndex);posed=transform(sample(info(helper),named('PatchIndex','INT')));centre=transform(named('EyeCentre','FLOAT_VECTOR'));radial=vec('NORMALIZE',vec('SUBTRACT',posed,centre));hits=[]
 for side in ['L','R']:
  ray=n.new('GeometryNodeRaycast');ray.data_type='FLOAT';L.new(info(bpy.data.objects['AFN60_'+side+'_EYE_OUTER_SHELL_APPROX']),ray.inputs['Target Geometry']);L.new(centre,ray.inputs['Source Position']);L.new(radial,ray.inputs['Ray Direction']);ray.inputs['Ray Length'].default_value=.1;hits.append(vec('ADD',ray.outputs['Hit Position'],vec('SCALE',radial,scalar=named('Clearance'))))
 compare=n.new('ShaderNodeMath');compare.operation='GREATER_THAN';L.new(named('Side'),compare.inputs[0]);choose=n.new('GeometryNodeSwitch');choose.input_type='VECTOR';L.new(compare.outputs[0],choose.inputs['Switch']);L.new(hits[1],choose.inputs['False']);L.new(hits[0],choose.inputs['True']);conform=named('Conform');difference=vec('SUBTRACT',choose.outputs['Output'],posed);posed=vec('ADD',posed,vec('SCALE',difference,scalar=conform));followDelta=vec('SUBTRACT',sample(cg,named('BindIndex','INT')),transform(named('BindRest','FLOAT_VECTOR')));posed=vec('ADD',posed,vec('SCALE',followDelta,scalar=named('FollowWeight')));compare=n.new('ShaderNodeMath');compare.operation='GREATER_THAN';L.new(origIndex,compare.inputs[0]);compare.inputs[1].default_value=-.5;choose=n.new('GeometryNodeSwitch');choose.input_type='VECTOR';L.new(compare.outputs[0],choose.inputs['Switch']);L.new(posed,choose.inputs['False']);L.new(sourcePosition,choose.inputs['True']);setpos=n.new('GeometryNodeSetPosition');L.new(inp.outputs['Geometry'],setpos.inputs['Geometry']);L.new(choose.outputs['Output'],setpos.inputs['Position']);L.new(setpos.outputs['Geometry'],out.inputs['Geometry']);md=skin.modifiers.new('AFN101_LIVE_ORIGINAL_BODY_AND_OWN_LIDS','NODES');md.node_group=ng
 control.hide_render=True;control.hide_set(True);hair=bpy.data.objects['AFN97_TUCKED_ARTIST_BOB_CHILDREN']
 for md in hair.modifiers:
  if md.type=='NODES':
   md.node_group=md.node_group.copy();md.node_group.name='AFN101_ACTUAL_NEW_SKIN_ROOT_FRAMES'
   for node in md.node_group.nodes:
    if node.bl_idname=='GeometryNodeObjectInfo' and node.inputs['Object'].default_value==control:node.inputs['Object'].default_value=skin
 helper['scope']='Explicit upper/lower margins, finite short inner wall, orbital lining and posterior cap. Outer guide copies are read-only shared-boundary references. Own left/right closed source shapes. Original filled socket faces are removed anatomically, not hidden behind an overlay.';skin['scope']='Complete retained C body with a topologically joined replacement socket/lid component. Original cap vertices retained only as unrendered correspondence controls; later runtime export must remove/remap loose controls. New static/dynamic contacts and complete operation unaccepted.';skin['rights']='Original complete C and Dan Ulrich CC0 base/source notices retained. New anatomical topology/code; inherited materials/artist hair retain separate source licenses. No Epic assets/runtime imported.';bpy.context.view_layer.update();_,actual=q.geom(skin);assert len(actual)==len(newV) and np.isfinite(actual).all();outsideError=float(np.linalg.norm(actual[:len(C)]-C,axis=1).max());assert outsideError<4e-6;used=np.unique(newT);loose=int(len(newV)-len(used));save('a-build-summary.json',{'source':str(SRC),'sourceSha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'output':str(OUT),'renderSkin':skin.name,'oldControlSkin':control.name,'editablePatch':helper.name,'sourceBaseFaceComponents':[len(x) for x in components],'removedNativeSocketFaces':len(removedBase),'removedActualFineFaces':int(remove.sum()),'retainedFineFaces':int((~remove).sum()),'replacementFaces':len(patchFaces),'newActualVertices':len(newV),'newTriangles':len(newT),'originalVertexCorrespondenceMaximumWorldErrorM':outsideError,'unrenderedOriginalCupCorrespondenceVertices':loose,'perEye':perEye,'ownClosedReferenceUpperLidFraction':.82,'finite':True,'completeAppearanceOperationFiniteContactRuntimeAccepted':False,'secondsBeforePreview':time.time()-tick});np.savez_compressed(E/'a-anatomical-lid-lineage.npz',removedNativeFaceIDs=removedBase,removedFineFaceIDs=np.flatnonzero(remove),originalBoundaryEdges=boundary,newPatchBodyVertexIDs=np.arange(len(C),len(newV)),patchOpenWorld=P,patchClosedWorld=PC,patchFaces=np.array(patchFaces,'i4'),patchHelperOriginalBodyMapping=np.array(sorted(hmap.items()),'i4'))
 m.m.rig.shade.settings();m.m.rig.k.b.camera('face');s.camera.data.lens=85;s.render.hair_subdiv=3;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);rows=[]
 for view in ['face','profile','body-face']:rows.append(v.image('a-articulated-lids',view));save('a-view-controls.json',rows)
 print('R101_FIRST_COMPLETE_PREVIEW_DONE',time.time()-tick,flush=True);oral=bpy.data.objects['AFN74_ORAL_CONTROLS']
 for ob in [face,oral]:
  if ob.animation_data:ob.animation_data.action=None
 face['blink_left']=face['blink_right']=1.;face.update_tag();oral.update_tag()
 for name in m.m.rig.native_names():ob=bpy.data.objects[name];ob.update_tag();ob.data.shape_keys.update_tag()
 helper.update_tag();helper.data.shape_keys.update_tag();bpy.context.view_layer.update();rows.append(v.image('a-articulated-lids-closed','face'));save('a-view-controls.json',rows);print('R101_ARTICULATED_LIDS_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
