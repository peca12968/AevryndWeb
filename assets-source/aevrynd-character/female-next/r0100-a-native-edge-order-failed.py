"""Direct source-native eyelid sculpt and delivered-pose corrective assembly.
One complete C woman; original donor and all rollback files remain immutable.
The native Multires controls are editable; no globe/IOR/aperture sweep.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0100-native-eyelid-assembly';S=R/'engine/assets/characters/female-next/source';OLD=E.parent/'r0098-whole-head-foundation';SRC=S/'aevrynd-female-next-r0099-c-continuous-artist-body.blend';OUT=S/'aevrynd-female-next-r0100-a-native-lid-assembly.blend'
sp=importlib.util.spec_from_file_location('r100native','build-female-next-r0098-native-head.py' if False else Path(__file__).with_name('build-female-next-r0098-native-head.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);q=m.q;v=m.v;v.E=E
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8')
def main():
 tick=time.time();assert not OUT.exists();bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects['AFN99_ORIGINAL_CONTINUOUS_ARTIST_SKIN'];body=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING'];face=bpy.data.objects['AFN59_FACE_CONTROLS'];oral=bpy.data.objects['AFN74_ORAL_CONTROLS'];donor0=bpy.data.objects['AFN99_ORIGINAL_ARTIST_FULL_SOURCE'];donor=donor0.copy();donor.data=donor0.data.copy();s.collection.objects.link(donor);donor.name='AFN100_EDITABLE_NATIVE_LID_SCULPT';donor.hide_render=True;donor.hide_set(True)
 ref=json.loads((OLD/'official-female-reference.json').read_text('utf8'));plan=json.loads((OLD/'a-head-envelope-plan.json').read_text('utf8'));stage=np.array(ref['stageWorldTransform']);rot=np.array(plan['sourceRotation']);scale=plan['sourceScale'];dm=np.array(donor.matrix_world);B=scale*rot@stage[:3,:3]@dm[:3,:3];origin=(stage[:3,:3]@dm[:3,3]+stage[:3,3]-np.array(plan['sourceMean']))@rot.T*scale+np.array(plan['targetMean']);BI=np.linalg.inv(B)
 def world(local):return local@B.T+origin
 def local(world):return (world-origin)@BI.T
 def fine():
  d,p=q.geom(donor);return (p@stage[:3,:3].T+stage[:3,3]-np.array(plan['sourceMean']))@rot.T*scale+np.array(plan['targetMean'])
 base=q.arr(donor.data.vertices,'co',len(donor.data.vertices),3).astype('f8');W=world(base);edges=q.arr(donor.data.edges,'vertices',len(donor.data.edges),2,dtype='i4');adj=[set() for _ in W]
 for a,b in edges:adj[a].add(int(b));adj[b].add(int(a))
 selection=json.loads((E/'native-rim-selection.json').read_text('utf8'));refz=np.load(E.parent/'r0088-lid-aperture/actual-native-margin-data.npz');refIDs=refz['bodyNativeIDs'][refz['rimLocalIndices']];oldWorld=np.load(OLD/'a-whole-head-lineage.npz')['oldNativeWorld'];seams=json.loads((E.parent/'r0060-ocular-assembly/native-socket-patches.json').read_text('utf8'))['seams'];radj={int(i):set() for i in refIDs}
 for a,b in seams:
  if a in radj and b in radj:radj[a].add(b);radj[b].add(a)
 def arcs(ids,adjacency,P):
  ids=set(map(int,ids));start=min(ids,key=lambda i:abs(P[i,0]));end=max(ids,key=lambda i:abs(P[i,0]));paths=[]
  assert len(adjacency[start]&ids)==2,(start,adjacency[start]&ids)
  for nxt in sorted(adjacency[start]&ids):
   path=[start];prev=start;cur=nxt
   for _ in range(len(ids)+2):
    path.append(cur)
    if cur==end:break
    choices=(adjacency[cur]&ids)-{prev};assert len(choices)==1,(cur,choices);prev,cur=cur,next(iter(choices))
   assert path[-1]==end;paths.append(np.array(path,'i4'))
  return sorted(paths,key=lambda p:float(P[p,2].mean()),reverse=True)
 def curve(P,ids,t):
  pts=P[ids];a=np.r_[0,np.cumsum(np.linalg.norm(np.diff(pts,axis=0),axis=1))];a/=a[-1];return np.array([np.interp(t,a,pts[:,j]) for j in range(3)]).T
 openW=W.copy();closedW=W.copy();allRoi=set();sculptRows=[]
 for side,sign in [('L',1),('R',-1)]:
  ids=np.array(selection[side],'i4');paths=arcs(ids,adj,W);rid=refIDs[oldWorld[refIDs,0]*sign>0];rp=arcs(rid,radj,oldWorld);eye=bpy.data.objects['AFN60_'+side+'_EYE_OUTER_SHELL_APPROX'];ed,EV=q.geom(eye);ed.calc_loop_triangles();ET=q.arr(ed.loop_triangles,'vertices',len(ed.loop_triangles),3,dtype='i4');tree=BVHTree.FromPolygons(EV.tolist(),ET.tolist(),all_triangles=True)
  def front(pt,clearance):
   loc,no,index,dist=tree.ray_cast(Vector((pt[0],-.2,pt[2])),Vector((0,1,0)),.2)
   p=pt.copy()
   if loc is not None:p[1]=loc.y-clearance
   return p
  pins={};cpins={};targets={}
  # Native upper/lower topology is reconstructed against the retained good
  # contour. Both closed margins share one authored seam, not inherited blink1.
  for path,refpath in zip(paths,rp):
   a=np.r_[0,np.cumsum(np.linalg.norm(np.diff(W[path],axis=0),axis=1))];a/=a[-1];target=curve(oldWorld,refpath,a)
   for i,t,p in zip(path,a,target):
    p=front(p,.00035);c=p.copy();p0=oldWorld[rp[0][0]];p1=oldWorld[rp[0][-1]];c[2]=(1-t)*p0[2]+t*p1[2]-.0007*np.sin(np.pi*t);c=front(c,.00035);targets[int(i)]=p;pins[int(i)]=p-W[i];cpins[int(i)]=c-W[i]
  # Source lining is continuous with the outer lid. Pin its first inner row
  # to a separate finite tissue surface, keeping the posterior cup fixed.
  pol=donor.data.polygons
  for poly in pol:
   vv=list(poly.vertices)
   if not any(i in targets for i in vv):continue
   pp=W[vv];normal=np.cross(pp[1]-pp[0],pp[2]-pp[0]);centre=np.mean(EV,axis=0)
   if np.dot(normal,pp.mean(0)-centre)>=0:continue
   for i in vv:
    if i in targets:continue
    near=min(targets,key=lambda j:float(np.linalg.norm(W[j]-W[i])));p=targets[near].copy();p[[0,2]]+=.35*(W[i]-W[near])[[0,2]];p=front(p,.00010);c=W[i]+cpins[near];c=front(c,.00010);pins[i]=p-W[i];cpins[i]=c-W[i]
  roi=set(pins);frontier=set(pins)
  for _ in range(5):frontier=set().union(*(adj[i] for i in frontier))-roi;roi|=frontier
  boundary={i for i in roi if any(j not in roi for j in adj[i])}|set(selection['posterior'+side]);roi|=boundary
  for i in boundary:
   if i not in pins:pins[i]=np.zeros(3);cpins[i]=np.zeros(3)
  free=sorted(roi-set(pins));index={j:i for i,j in enumerate(free)};A=np.eye(len(free));rhs=np.zeros((len(free),6))
  for i,row in index.items():
   neighbours=adj[i];weight=1/len(neighbours)
   for j in neighbours:
    if j in index:A[row,index[j]]-=weight
    elif j in pins:rhs[row,:3]+=weight*pins[j];rhs[row,3:]+=weight*cpins[j]
  solution=np.linalg.solve(A,rhs) if free else np.empty((0,6))
  for i in roi:
   if i in pins:openW[i]+=pins[i];closedW[i]+=cpins[i]
   elif i in index:openW[i]+=solution[index[i],:3];closedW[i]+=solution[index[i],3:]
  allRoi|=roi;sculptRows.append({'side':side,'nativeMarginIDs':ids,'innerAndMarginPins':len(pins)-len(boundary),'patchVertices':len(roi),'freeVertices':len(free)})
 baselineFine=fine();donor.shape_key_add(name='Basis');op=donor.shape_key_add(name='AFN100_NATIVE_OPEN');cl=donor.shape_key_add(name='AFN100_NATIVE_CLOSED');op.data.foreach_set('co',local(openW).astype('f4').ravel());cl.data.foreach_set('co',local(closedW).astype('f4').ravel());op.value=1;bpy.context.view_layer.update();openFine=fine();op.value=0;cl.value=1;bpy.context.view_layer.update();closedFine=fine();cl.value=0;op.value=1;bpy.context.view_layer.update();assert len(openFine)==len(skin.data.vertices)
 _,C=q.geom(skin);neutral=C.copy();actions={o.name:o.animation_data.action if o.animation_data else None for o in [face,oral]}
 for o in [face,oral]:
  if o.animation_data:o.animation_data.action=None
 def inputs(left,right):
  face['blink_left']=left;face['blink_right']=right;oral['jaw_open']=0
  for o in [face,oral]:o.update_tag()
  for n in m.m.rig.native_names():o=bpy.data.objects[n];o.update_tag();o.data.shape_keys.update_tag()
  bpy.context.view_layer.update()
 inputs(0,0);_,neutral=q.geom(skin);inputs(1,0);_,oldLeft=q.geom(skin);inputs(0,1);_,oldRight=q.geom(skin);inputs(0,0)
 deltaOpen=openFine-baselineFine;desiredClosed=neutral+closedFine-baselineFine;roiFine=np.linalg.norm(deltaOpen,axis=1)+np.linalg.norm(closedFine-baselineFine,axis=1)>1e-8;left=roiFine&(neutral[:,0]>0);right=roiFine&(neutral[:,0]<0);dcL=np.zeros_like(neutral);dcR=np.zeros_like(neutral);dcL[left]=desiredClosed[left]-oldLeft[left]-deltaOpen[left];dcR[right]=desiredClosed[right]-oldRight[right]-deltaOpen[right];AM=np.array(skin.matrix_world);AI=np.linalg.inv(AM[:3,:3]);deltas=[deltaOpen@AI.T,dcL@AI.T,dcR@AI.T]
 for name,delta in zip(['Open','LeftClosure','RightClosure'],deltas):skin.data.attributes.new('AFN100_'+name,'FLOAT_VECTOR','POINT').data.foreach_set('vector',delta.astype('f4').ravel())
 # Post-deformer correction, with an actual bone-parented affine basis.
 # It cancels inherited blink only within the sculpted native patch.
 anchorMesh=bpy.data.meshes.new('AFN100_HEAD_AFFINE_BASIS');anchorMesh.from_pydata([(0,0,0),(1,0,0),(0,1,0),(0,0,1)],[],[]);anchor=bpy.data.objects.new(anchorMesh.name,anchorMesh);s.collection.objects.link(anchor);anchor.parent=bpy.data.objects['AFN69_BODY_CONTROLS'];anchor.parent_type='BONE';anchor.parent_bone='Head';bpy.context.view_layer.update();anchor.matrix_world=skin.matrix_world.copy();anchor.hide_render=True;anchor.hide_set(True);bpy.context.view_layer.update()
 ng,n,L=m.interface('AFN100_NATIVE_LID_POSE_CORRECTIVE');inp=n.new('NodeGroupInput');out=n.new('NodeGroupOutput');info=n.new('GeometryNodeObjectInfo');info.transform_space='RELATIVE';info.inputs['Object'].default_value=anchor;pos=n.new('GeometryNodeInputPosition');samples=[]
 for k in range(4):
  sam=n.new('GeometryNodeSampleIndex');sam.data_type='FLOAT_VECTOR';sam.domain='POINT';sam.inputs['Index'].default_value=k;L.new(info.outputs['Geometry'],sam.inputs['Geometry']);L.new(pos.outputs['Position'],sam.inputs['Value']);samples.append(sam.outputs['Value'])
 basis=[]
 for k in range(1,4):
  sub=n.new('ShaderNodeVectorMath');sub.operation='SUBTRACT';L.new(samples[k],sub.inputs[0]);L.new(samples[0],sub.inputs[1]);basis.append(sub.outputs['Vector'])
 attrs=[]
 for name in ['Open','LeftClosure','RightClosure']:
  at=n.new('GeometryNodeInputNamedAttribute');at.data_type='FLOAT_VECTOR';at.inputs['Name'].default_value='AFN100_'+name;attrs.append(at.outputs['Attribute'])
 total=attrs[0]
 for attr,key in zip(attrs[1:],['blink_left','blink_right']):
  value=n.new('ShaderNodeValue');driver=value.outputs[0].driver_add('default_value').driver;driver.type='SCRIPTED';var=driver.variables.new();var.name='blink';var.targets[0].id=face;var.targets[0].data_path='["'+key+'"]';driver.expression='min(1,max(0,blink))';sc=n.new('ShaderNodeVectorMath');sc.operation='SCALE';L.new(attr,sc.inputs[0]);L.new(value.outputs[0],sc.inputs['Scale']);add=n.new('ShaderNodeVectorMath');add.operation='ADD';L.new(total,add.inputs[0]);L.new(sc.outputs['Vector'],add.inputs[1]);total=add.outputs['Vector']
 separate=n.new('ShaderNodeSeparateXYZ');L.new(total,separate.inputs[0]);terms=[]
 for k in range(3):
  sc=n.new('ShaderNodeVectorMath');sc.operation='SCALE';L.new(basis[k],sc.inputs[0]);L.new(separate.outputs[k],sc.inputs['Scale']);terms.append(sc.outputs['Vector'])
 total=terms[0]
 for term in terms[1:]:
  add=n.new('ShaderNodeVectorMath');add.operation='ADD';L.new(total,add.inputs[0]);L.new(term,add.inputs[1]);total=add.outputs['Vector']
 setpos=n.new('GeometryNodeSetPosition');L.new(inp.outputs['Geometry'],setpos.inputs['Geometry']);L.new(total,setpos.inputs['Offset']);L.new(setpos.outputs['Geometry'],out.inputs['Geometry']);md=skin.modifiers.new('AFN100_NATIVE_LIDS_AFTER_ORIGINAL_DEFORM','NODES');md.node_group=ng
 donor['authoringScope']='Editable original continuous native eyelid topology, own open/closed shapes. Original Dan Ulrich selected asset CC0; this reconstruction is unaccepted. No new Epic assets/runtime.';skin['AFN100_scope']='Source-native eyelid/lining rest sculpt plus actual-input endpoint correction after retained whole-skin deformation. Intermediate finite contacts and natural blink timing are unaccepted; no zero-clipping claim.'
 inputs(0,0);_,newOpen=q.geom(skin);inputs(1,1);_,newClosed=q.geom(skin);inputs(0,0)
 save('a-build-summary.json',{'source':str(SRC),'sourceSha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'output':str(OUT),'renderSkin':skin.name,'nativeSculpt':donor.name,'nativePatch':sculptRows,'sourceNativeVertices':len(base),'fineVertices':len(C),'fineAffectedVertices':int(roiFine.sum()),'openMaximumSculptM':float(np.linalg.norm(deltaOpen,axis=1).max()),'newOpenReferenceMaximumErrorM':float(np.linalg.norm(newOpen-(neutral+deltaOpen),axis=1).max()),'closedEndpointReferenceMaximumErrorM':float(np.linalg.norm((newClosed-desiredClosed)[roiFine],axis=1).max()),'finite':bool(np.isfinite(newOpen).all() and np.isfinite(newClosed).all()),'completeAppearanceFunctionFiniteContactRuntimeAccepted':False,'secondsBeforePreview':time.time()-tick,'primaryReference':selection['primaryDesignReference'],'referenceScope':selection['referenceScope']})
 # Save original actions and neutral inputs. Independent reopen is separate.
 for o in [face,oral]:
  if o.animation_data:o.animation_data.action=actions[o.name]
  o.update_tag()
 s.frame_set(1);bpy.context.view_layer.update();m.m.rig.shade.settings();m.m.rig.k.b.camera('face');s.camera.data.lens=85;s.render.hair_subdiv=3;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
 rows=[]
 for view in ['face','profile','body-face']:rows.append(v.image('a-native-lids',view));save('a-view-controls.json',rows)
 print('R100_FIRST_COMPLETE_PREVIEW_DONE',time.time()-tick,flush=True)
 for o in [face,oral]:
  if o.animation_data:o.animation_data.action=None
 inputs(1,1);rows.append(v.image('a-native-lids-closed','face'));save('a-view-controls.json',rows);print('R100_NATIVE_LID_BLINK_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
