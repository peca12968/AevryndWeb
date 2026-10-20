"""Different construction after rejected outward ear sculpt: reconstruct only
selected original side locks behind the ear and sweep true source-child offsets
in each edited guide's tangent frame. Keep actual per-child scalp attachment.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0097-scalp-ear-authored-controls';S=R/'engine/assets/characters/female-next/source';SRC=S/'aevrynd-female-next-r0097-a-scalp-ear-live-controls.blend';OUT=S/'aevrynd-female-next-r0097-b-anatomical-ear-tuck.blend'
def mod(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);return a
v=mod('r97tuckviews','render-female-next-r0091-matched.py');v.E=E;m=v.m;q=m.q;art=mod('r97sample','build-female-next-r0095-layered-guides.py')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8')
def unit(x):return x/max(np.linalg.norm(x),1e-12)
def guide_frames(G,seed):
 t=np.empty_like(G);t[:,0]=G[:,1]-G[:,0];t[:,-1]=G[:,-1]-G[:,-2];t[:,1:-1]=G[:,2:]-G[:,:-2];t/=np.linalg.norm(t,axis=2)[:,:,None];n=np.empty_like(t)
 for i in range(len(G)):
  n[i,0]=unit(seed[i]-t[i,0]*np.dot(seed[i],t[i,0]))
  for j in range(1,G.shape[1]):n[i,j]=unit(n[i,j-1]-t[i,j]*np.dot(n[i,j-1],t[i,j]))
 return t,n,np.cross(t,n)
def graph(hair,guide,body,N):
 ng=bpy.data.node_groups.new('AFN97_SCALP_BOUND_TRUE_PARENT_SWEPT_CHILDREN','GeometryNodeTree');ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');nodes=ng.nodes;L=ng.links;inp=nodes.new('NodeGroupInput');out=nodes.new('NodeGroupOutput');pos=nodes.new('GeometryNodeInputPosition');ix=nodes.new('GeometryNodeInputIndex')
 def named(name,kind='FLOAT_VECTOR'):
  n=nodes.new('GeometryNodeInputNamedAttribute');n.data_type=kind;n.inputs['Name'].default_value=name;return n.outputs['Attribute']
 def vec(op,a,b=None):
  n=nodes.new('ShaderNodeVectorMath');n.operation=op;L.new(a,n.inputs[0])
  if b is not None:L.new(b,n.inputs[3] if op=='SCALE' else n.inputs[1])
  return n.outputs['Value' if op=='DOT_PRODUCT' else 'Vector']
 def math(op,a,value=None,b=None):
  n=nodes.new('ShaderNodeMath');n.operation=op;L.new(a,n.inputs[0])
  if b is not None:L.new(b,n.inputs[1])
  elif value is not None:n.inputs[1].default_value=value
  return n.outputs[0]
 def obj(ob):
  n=nodes.new('GeometryNodeObjectInfo');n.transform_space='RELATIVE';n.inputs['Object'].default_value=ob;n.inputs['As Instance'].default_value=False;return n.outputs['Geometry']
 def sample(geom,index):
  n=nodes.new('GeometryNodeSampleIndex');n.data_type='FLOAT_VECTOR';n.domain='POINT';n.clamp=False;L.new(geom,n.inputs['Geometry']);L.new(pos.outputs['Position'],n.inputs['Value']);L.new(index,n.inputs['Index']);return n.outputs['Value']
 def separate(vector):
  n=nodes.new('ShaderNodeSeparateXYZ');L.new(vector,n.inputs[0]);return [n.outputs[x] for x in ['X','Y','Z']]
 bg=obj(body);a=sample(bg,named('AFN97_ScalpVertex0','INT'));b=sample(bg,named('AFN97_ScalpVertex1','INT'));c=sample(bg,named('AFN97_ScalpVertex2','INT'));t=vec('NORMALIZE',vec('SUBTRACT',b,a));normal=vec('NORMALIZE',vec('CROSS_PRODUCT',vec('SUBTRACT',b,a),vec('SUBTRACT',c,a)));bit=vec('NORMALIZE',vec('CROSS_PRODUCT',normal,t));w=separate(named('AFN97_RootBarycentric'));anchor=vec('ADD',vec('ADD',vec('SCALE',a,w[0]),vec('SCALE',b,w[1])),vec('SCALE',c,w[2]));root=vec('ADD',anchor,vec('SCALE',normal,named('AFN97_RootRadiusNative','FLOAT')))
 gg=obj(guide);base=math('MULTIPLY',named('AFN97_SourceParent','INT'),N);j=math('MODULO',ix.outputs['Index'],N);at=math('ADD',base,b=j);lo=math('ADD',base,b=math('MAXIMUM',math('SUBTRACT',j,1),0));hi=math('ADD',base,b=math('MINIMUM',math('ADD',j,1),N-1));gp=sample(gg,at);gt=vec('NORMALIZE',vec('SUBTRACT',sample(gg,hi),sample(gg,lo)));restGN=named('AFN97_SweepRestGuideN');gn=vec('NORMALIZE',vec('SUBTRACT',restGN,vec('SCALE',gt,vec('DOT_PRODUCT',restGN,gt))));gb=vec('CROSS_PRODUCT',gt,gn);coef=separate(named('AFN97_SweepChildCoefficients'));swept=vec('ADD',gp,vec('ADD',vec('ADD',vec('SCALE',gt,coef[0]),vec('SCALE',gn,coef[1])),vec('SCALE',gb,coef[2])));offset=vec('SCALE',vec('SUBTRACT',swept,named('AFN97_RestRoot')),named('AFN97_FreeEditWeight','FLOAT'));transport=vec('ADD',vec('ADD',vec('SCALE',t,vec('DOT_PRODUCT',offset,named('AFN97_RestT'))),vec('SCALE',bit,vec('DOT_PRODUCT',offset,named('AFN97_RestB')))),vec('SCALE',normal,vec('DOT_PRODUCT',offset,named('AFN97_RestN'))));setpos=nodes.new('GeometryNodeSetPosition');L.new(inp.outputs['Geometry'],setpos.inputs['Geometry']);L.new(vec('ADD',root,transport),setpos.inputs['Position']);L.new(setpos.outputs['Geometry'],out.inputs['Geometry']);md=hair.modifiers.new('AFN97_EVALUATED_SCALP_AND_EDITED_GUIDE_FRAMES','NODES');md.node_group=ng
def main():
 tick=time.time();assert not OUT.exists();a=read=json.loads((E/'a-build-summary.json').read_text('utf8'));assert sha(SRC)==a['outputSha256'];z=np.load(E/'a-scalp-ear-lineage.npz');G=z['boundGuideWorld'].astype('f8');P=z['boundChildWorld'].astype('f8');parents=z['sourceParent'];A=z['objectMatrix'];inv=np.linalg.inv(A[:3,:3]);N=17;new=G.copy();selected=[];controls={}
 for g,path in enumerate(G):
  hit=np.flatnonzero((abs(path[:,0])>.055)&(path[:,1]>-.065)&(path[:,1]<.010)&(path[:,2]>1.43)&(path[:,2]<1.49))
  if not len(hit) or path[0,2]<1.485:continue
  k=int(hit[np.argmin(abs(path[hit,2]-1.46))]);side=1 if path[k,0]>0 else -1;u=float(np.clip((path[k,1]+.065)/.075,0,1));peak=int(np.argmax(path[:,2]));descent=np.flatnonzero((np.arange(N)>peak)&(path[:,2]<1.505));release=int(descent[0]) if len(descent) else min(peak+1,N-2);prefix=path[:release+1].tolist();tip=path[-1].copy();tip[1]=max(tip[1],.020+.015*u)
  landmarks=np.array([[side*(.071+.004*u),.008+.015*u,1.490],[side*(.067+.005*u),.023+.015*u,1.458],[side*(.066+.005*u),.021+.018*u,1.414],tip.tolist()]);control=np.array(prefix+landmarks.tolist());new[g]=art.resample(art.smooth_polyline(control),N);new[g,0]=path[0];selected.append(g);controls[str(g)]={'originalEarControl':path[k],'prefixReleaseIndex':release,'orderedControlPolylineWorld':control,'artIntent':'Original crown/root prefix -> upper-ear bend -> posterior ear corridor -> nape/free tip. Original per-guide frontal/posterior ordering retained; face-framing source guides outside this side corridor stay unchanged.'}
 assert 0<len(selected)<248
 bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();old=bpy.data.objects[a['curveObject']];oldGuide=bpy.data.objects[a['guideObject']];body=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING'];nativeG=(G-A[:3,3])@inv.T;nativeNew=(new-A[:3,3])@inv.T;nativeP=(P-A[:3,3])@inv.T;seed=np.array([unit(z['restNNative'][parents==g].mean(0)) for g in range(248)]);gt,gn,gb=guide_frames(nativeG,seed);off=nativeP-nativeG[parents];coef=np.stack((np.sum(off*gt[parents],axis=2),np.sum(off*gn[parents],axis=2),np.sum(off*gb[parents],axis=2)),axis=2)
 mesh=bpy.data.meshes.new('AFN97_TUCK_EDITABLE_SOURCE_GUIDES');mesh.from_pydata(nativeG.reshape(-1,3).tolist(),[(g*N+j,g*N+j+1) for g in range(248) for j in range(N-1)],[]);mesh.update();guide=bpy.data.objects.new(mesh.name,mesh);s.collection.objects.link(guide);guide.matrix_world=old.matrix_world.copy();guide.hide_render=True;guide.display_type='WIRE';guide.show_in_front=True;guide.shape_key_add(name='Basis');key=guide.shape_key_add(name='Anatomical_Ear_Tuck');key.data.foreach_set('co',nativeNew.astype('f4').ravel());key.value=1;guide['scope']='Original248 spatial Bob guides. Selected side locks reconstructed through explicit upper-ear/posterior/nape controls. Live child cross-section follows each edited tangent; neutral-pose authoring, not physical twist or natural dynamics.';d=old.data.copy();d.name='AFN97_TUCKED_ARTIST_BOB_CHILDREN'
 for name,data in [('AFN97_SweepRestGuideN',gn[parents]),('AFN97_SweepChildCoefficients',coef)]:
  at=d.attributes.get(name) or d.attributes.new(name,'FLOAT_VECTOR','POINT');at.data.foreach_set('vector',data.astype('f4').ravel())
 hair=bpy.data.objects.new(d.name,d);s.collection.objects.link(hair);hair.matrix_world=old.matrix_world.copy();graph(hair,guide,body,N);hair['scope']='Different ear-tuck/swept cross-section construction after rejected outward scalp sculpt. Actual independently bounded scalp roots remain. All original24800 children use exact source parent identity and edited guide tangent frames, original width/close-tip unchanged. No contact/natural dynamics/runtime or complete operation acceptance.';hair['sourceCredit']=old.get('sourceCredit','');old.hide_render=True;old.hide_set(True);oldGuide.hide_set(True);bpy.context.view_layer.update();actual=q.hair(hair).reshape(P.shape)
 # Same Gram-Schmidt current frame as the actual native node construction.
 nt=np.empty_like(nativeNew);nt[:,0]=nativeNew[:,1]-nativeNew[:,0];nt[:,-1]=nativeNew[:,-1]-nativeNew[:,-2];nt[:,1:-1]=nativeNew[:,2:]-nativeNew[:,:-2];nt/=np.linalg.norm(nt,axis=2)[:,:,None];nn=gn-nt*np.sum(gn*nt,axis=2)[:,:,None];nn/=np.linalg.norm(nn,axis=2)[:,:,None];nb=np.cross(nt,nn);expectedNative=nativeNew[parents]+nt[parents]*coef[:,:,0,None]+nn[parents]*coef[:,:,1,None]+nb[parents]*coef[:,:,2,None];expectedNative[:,0]=nativeP[:,0];expected=expectedNative@A[:3,:3].T+A[:3,3];err=float(np.linalg.norm(actual-expected,axis=2).max());assert np.isfinite(actual).all() and err<5e-6,err;m.rig.shade.settings();m.rig.k.b.camera('face');s.camera.data.lens=85;s.render.hair_subdiv=3;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
 np.savez_compressed(E/'b-ear-tuck-lineage.npz',boundChildWorld=P,boundGuideWorld=G,authoredGuideWorld=new,sourceParent=parents,selectedGuides=np.array(selected,'i4'),guideRestT=gt,guideRestN=gn,guideRestB=gb,childCoefficients=coef,actualWorld=actual.astype('f4'),objectMatrix=A)
 save('b-build-summary.json',{'source':str(SRC),'sourceSha256':sha(SRC),'output':str(OUT),'outputSha256':sha(OUT),'outputBytes':OUT.stat().st_size,'curveObject':hair.name,'guideObject':guide.name,'recombShapeKey':key.name,'sourceParents':248,'renderChildren':24800,'pointsEach':N,'selectedSideGuides':len(selected),'selectedGuideIDs':selected,'sourceWidthCloseTipMaterialsBodyFaceRigPreserved':True,'originalCrownAndFaceFramingOutsideSelectedSideLocksPreserved':True,'newConstruction':'Selected original artist side locks explicitly routed over/behind the ear and to nape, with true-parent tangent-frame child sweeps, rather than the rejected outward sculpt or static world-space child offsets.','controlPolylines':controls,'maximumSavedNativeNodeWorldErrorM':err,'allRootDomainAndParentageBindingsUnchangedFromA':True,'naturalMotionContactRuntimeOrCompleteOperationAccepted':False,'secondsBeforePreview':time.time()-tick});rows=[]
 for view in ['face','profile','back','body-face']:rows.append(v.image('b-ear-tuck',view));save('b-view-controls.json',rows)
 print('R97_COMPLETE_EAR_TUCK_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
