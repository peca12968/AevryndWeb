"""Preserve the artist Bob, author local crown/ear sculpt controls, and attach
all original children to actual evaluated scalp triangles with live guide edits.
Static authoring/pose-follow construction, not a collision solver or dynamics.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0097-scalp-ear-authored-controls';S=R/'engine/assets/characters/female-next/source';E96=E.parent/'r0096-artist-bob-foundation';SRC=S/'aevrynd-female-next-r0096-a-artist-Bob-foundation.blend';OUT=S/'aevrynd-female-next-r0097-a-scalp-ear-live-controls.blend'
def mod(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);return a
v=mod('r97views','render-female-next-r0091-matched.py');v.E=E;m=v.m;q=m.q;r94=mod('r97bary','build-female-next-r0094-growth-volume.py')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8')
def live_graph(hair,guide,body,N):
 ng=bpy.data.node_groups.new('AFN97_LIVE_SCALP_AND_SOURCE_PARENT_CONTROLS','GeometryNodeTree');ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');nodes=ng.nodes;L=ng.links;inp=nodes.new('NodeGroupInput');out=nodes.new('NodeGroupOutput');pos=nodes.new('GeometryNodeInputPosition');index=nodes.new('GeometryNodeInputIndex')
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
 def sample(geom,ix):
  n=nodes.new('GeometryNodeSampleIndex');n.data_type='FLOAT_VECTOR';n.domain='POINT';n.clamp=False;L.new(geom,n.inputs['Geometry']);L.new(pos.outputs['Position'],n.inputs['Value']);L.new(ix,n.inputs['Index']);return n.outputs['Value']
 bg=obj(body);a=sample(bg,named('AFN97_ScalpVertex0','INT'));b=sample(bg,named('AFN97_ScalpVertex1','INT'));c=sample(bg,named('AFN97_ScalpVertex2','INT'));t=vec('NORMALIZE',vec('SUBTRACT',b,a));n=vec('NORMALIZE',vec('CROSS_PRODUCT',vec('SUBTRACT',b,a),vec('SUBTRACT',c,a)));bit=vec('NORMALIZE',vec('CROSS_PRODUCT',n,t));sep=nodes.new('ShaderNodeSeparateXYZ');L.new(named('AFN97_RootBarycentric'),sep.inputs[0]);anchor=vec('ADD',vec('ADD',vec('SCALE',a,sep.outputs['X']),vec('SCALE',b,sep.outputs['Y'])),vec('SCALE',c,sep.outputs['Z']));root=vec('ADD',anchor,vec('SCALE',n,named('AFN97_RootRadiusNative','FLOAT')))
 gi=math('ADD',math('MULTIPLY',named('AFN97_SourceParent','INT'),N),b=math('MODULO',index.outputs['Index'],N));gp=sample(obj(guide),gi);delta=vec('SCALE',vec('SUBTRACT',gp,named('AFN97_RestGuideAtPoint')),named('AFN97_FreeEditWeight','FLOAT'));offset=vec('ADD',vec('SUBTRACT',pos.outputs['Position'],named('AFN97_RestRoot')),delta);transport=vec('ADD',vec('ADD',vec('SCALE',t,vec('DOT_PRODUCT',offset,named('AFN97_RestT'))),vec('SCALE',bit,vec('DOT_PRODUCT',offset,named('AFN97_RestB')))),vec('SCALE',n,vec('DOT_PRODUCT',offset,named('AFN97_RestN'))));setpos=nodes.new('GeometryNodeSetPosition');L.new(inp.outputs['Geometry'],setpos.inputs['Geometry']);L.new(vec('ADD',root,transport),setpos.inputs['Position']);L.new(setpos.outputs['Geometry'],out.inputs['Geometry']);md=hair.modifiers.new('AFN97_LIVE_SCALP_AND_GUIDE_EDITING','NODES');md.node_group=ng
def main():
 tick=time.time();assert not OUT.exists() and sha(SRC)=='bac9e57dd0209977ffc9656d8e01d596007b0ea483386503a372d8bb17b5fc17';z=np.load(E96/'a-artist-Bob-lineage.npz');parents=np.load(E/'original-SIMPLE-child-parent.npy');assert np.array_equal(parents,np.arange(24800)%248);bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();old=bpy.data.objects['AFN96_ARTIST_BOB_RENDER_CHILDREN'];body=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING'];A=np.array(old.matrix_world);inv=np.linalg.inv(A[:3,:3]);scale=np.linalg.norm(A[:3,0]);N=17;P=q.hair(old).reshape(24800,N,3);allNative=z['allResampledNative'].astype('f8');G=allNative[:248]@A[:3,:3].T+A[:3,3];assert np.max(abs(P-(allNative[248:]@A[:3,:3].T+A[:3,3])))<1e-6;oldP=P.copy();oldG=G.copy();radius=q.arr(old.data.attributes['radius'].data,'value',P.size//3).reshape(24800,N);radiusNative=float(radius.max());row=m.rig.k.mesh(body);V,T=row['V'],row['T'];eligible=np.flatnonzero(np.isin(row['nativeTriangleFace'],np.load(E.parent/'r0094-authored-growth-routing/a-growth-volume-lineage.npz')['allowedNativeFaces']));scalp=BVHTree.FromPolygons(V.tolist(),T[eligible].tolist(),all_triangles=True)
 # Reconstruct bounded actual scalp anchors, preserving source root lineage.
 rootTri=np.empty((24800,3),'i4');rootFace=np.empty(24800,'i4');bary=np.empty((24800,3));restRoot=np.empty((24800,3));restT=np.empty_like(restRoot);restB=np.empty_like(restRoot);restN=np.empty_like(restRoot);rootDeltas=[]
 def bind(root):
  co,no,j,dist=scalp.find_nearest(Vector(root));ti=int(eligible[j]);tri=V[T[ti]];w=r94.barycentric_closest(np.array(co),tri);normal=np.cross(tri[1]-tri[0],tri[2]-tri[0]);normal/=np.linalg.norm(normal);return ti,w,w@tri+normal*(radiusNative*scale),normal
 def junction(path,newRoot):
  arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(path,axis=0),axis=1))];u=np.minimum(arc/(.02*scale),1);blend=1-u*u*(3-2*u);return path+(newRoot-path[0])*blend[:,None]
 for i in range(24800):
  ti,w,root,normal=bind(P[i,0]);rootDeltas.append(root-P[i,0]);P[i]=junction(P[i],root);rootTri[i]=T[ti];rootFace[i]=row['nativeTriangleFace'][ti];bary[i]=w;restRoot[i]=(root-A[:3,3])@inv.T;tri=(V[T[ti]]-A[:3,3])@inv.T;t=tri[1]-tri[0];t/=np.linalg.norm(t);n=np.cross(tri[1]-tri[0],tri[2]-tri[0]);n/=np.linalg.norm(n);restT[i]=t;restN[i]=n;restB[i]=np.cross(n,t)
 for i in range(248):G[i]=junction(G[i],bind(G[i,0])[2])
 # Reproducible local sculpt strokes on the retained original artist paths.
 # These are deliberate crown volume and ear-wrap controls, not replacement
 # analytic guide families or a nearest-plane/point collision response.
 strokes=[{'name':'crown_front_volume','centre':[0,-.064,1.547],'radius':.045,'delta':[0,-.003,.006]},{'name':'crown_posterior_volume','centre':[0,.029,1.531],'radius':.045,'delta':[0,.006,.005]}]
 for side in [-1,1]:
  strokes += [{'name':str(side)+'_temple_volume','centre':[side*.057,-.074,1.515],'radius':.038,'delta':[side*.007,-.001,.004]}]
  for k,(x,y,zz,dx) in enumerate([(.076,-.031,1.475,.013),(.079,-.027,1.458,.018),(.077,-.024,1.441,.018),(.072,-.020,1.423,.012)]):strokes.append({'name':str(side)+'_ear_wrap_'+str(k),'centre':[side*x,y,zz],'radius':.026,'delta':[side*dx,0,0]})
 sculpt=np.zeros_like(G);total=np.zeros(G.shape[:2])
 for stroke in strokes:
  d=np.linalg.norm(G-np.array(stroke['centre']),axis=2)/stroke['radius'];w=np.maximum(1-d*d,0)**2;sculpt+=w[:,:,None]*np.array(stroke['delta']);total+=w
 sculpt/=np.maximum(total,1)[:,:,None];arc=np.concatenate([np.zeros((248,1)),np.cumsum(np.linalg.norm(np.diff(G,axis=1),axis=2),axis=1)],axis=1);u=np.minimum(arc/.025,1);sculpt*=((u*u*(3-2*u))[:,:,None]);sculpt[:,0]=0;authoredG=G+sculpt;nativeG=(G-A[:3,3])@inv.T;nativeAuthored=(authoredG-A[:3,3])@inv.T
 mesh=bpy.data.meshes.new('AFN97_ARTIST_BOB_EDITABLE_17_POINT_GUIDES');mesh.from_pydata(nativeG.reshape(-1,3).tolist(),[(g*N+j,g*N+j+1) for g in range(248) for j in range(N-1)],[]);mesh.update();guide=bpy.data.objects.new(mesh.name,mesh);s.collection.objects.link(guide);guide.matrix_world=old.matrix_world.copy();guide.hide_render=True;guide.display_type='WIRE';guide.show_in_front=True;guide.shape_key_add(name='Basis');key=guide.shape_key_add(name='Crown_Ear_Anatomical_Recomb');key.data.foreach_set('co',nativeAuthored.astype('f4').ravel());key.value=1;guide['scope']='248 original artist source parent paths, sampled at original17 cache slots. Local crown/ear sculpt shape plus manual free-point editing. Roots of actual children independently pinned to evaluated scalp; guide editing is neutral-pose authoring, not natural dynamics.'
 d=old.data.copy();d.name='AFN97_SCALP_BOUND_ARTIST_BOB_CHILDREN';d.position_data.foreach_set('vector',((P-A[:3,3])@inv.T).astype('f4').ravel())
 def attr(name,kind,domain,data):
  a=d.attributes.get(name) or d.attributes.new(name,kind,domain);a.data.foreach_set('vector' if kind=='FLOAT_VECTOR' else 'value',np.asarray(data,'i4' if kind=='INT' else 'f4').ravel())
 for j in range(3):attr('AFN97_ScalpVertex'+str(j),'INT','CURVE',rootTri[:,j])
 for name,data in [('RootBarycentric',bary),('RestRoot',restRoot),('RestT',restT),('RestB',restB),('RestN',restN)]:attr('AFN97_'+name,'FLOAT_VECTOR','CURVE',data)
 attr('AFN97_RootRadiusNative','FLOAT','CURVE',np.full(24800,radiusNative));attr('AFN97_SourceParent','INT','CURVE',parents);attr('AFN97_RestGuideAtPoint','FLOAT_VECTOR','POINT',nativeG[parents]);freeWeight=np.ones((24800,N));freeWeight[:,0]=0;attr('AFN97_FreeEditWeight','FLOAT','POINT',freeWeight)
 hair=bpy.data.objects.new(d.name,d);s.collection.objects.link(hair);hair.matrix_world=old.matrix_world.copy();hair['scope']='All24800 source children, source-backed SIMPLE parent identity, bounded actual scalp barycentric roots with finite radius exit, live per-root evaluated scalp frame and248 original spatial guide controls. Crown/ear sculpt authored, original free-length shape retained. Not a collision solver, exact Cycles occupancy/contact, continuous or natural motion acceptance.';hair['sourceCredit']=old.get('sourceCredit','');live_graph(hair,guide,body,N);old.hide_render=True;old.hide_set(True);bpy.context.view_layer.update();actual=q.hair(hair).reshape(P.shape);expected=P+sculpt[parents];err=float(np.linalg.norm(actual-expected,axis=2).max());assert np.isfinite(actual).all() and err<4e-6,err
 m.rig.shade.settings();m.rig.k.b.camera('face');s.camera.data.lens=85;s.render.hair_subdiv=3;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
 np.savez_compressed(E/'a-scalp-ear-lineage.npz',oldChildWorld=oldP,oldParentWorld=oldG,boundChildWorld=P,boundGuideWorld=G,authoredGuideWorld=authoredG,sculptWorld=sculpt,sourceParent=parents,rootBodyVertices=rootTri,rootNativeFace=rootFace,rootBarycentric=bary,restRootNative=restRoot,restTNative=restT,restBNative=restB,restNNative=restN,radiusNative=radius,actualWorld=actual.astype('f4'),objectMatrix=A)
 save('a-build-summary.json',{'source':str(SRC),'sourceSha256':sha(SRC),'output':str(OUT),'outputSha256':sha(OUT),'outputBytes':OUT.stat().st_size,'curveObject':hair.name,'guideObject':guide.name,'recombShapeKey':key.name,'sourceParents':248,'renderChildren':24800,'pointsEach':N,'allOriginalSourceFibresAndGuideLineageRetained':True,'radiusMaterialLightsExposureUnchanged':True,'allRootBarycentricBounded':bool(np.all(bary>=0)),'rootJunctionNativeM':.02,'rootDeltaWorldQuantilesM':np.quantile(np.linalg.norm(rootDeltas,axis=1),[0,.5,.95,1]),'guideSculptWorldDisplacementQuantilesM':np.quantile(np.linalg.norm(sculpt,axis=2),[0,.5,.95,1]),'strokes':strokes,'sculptArtIntent':'Retain the actual artist jaw-length and posterior contour; provide crown volume and a continuous outer-ear wrap rather than the ear strip clipping through a flat side sheet. Strokes operate on retained independent artist paths, not a new global analytic groom.','liveNeutralReadbackMaximumWorldErrorM':err,'sourceSemanticDomainNotAnatomicalFollicleAcceptance':True,'liveConstruction':'Every child samples its exact original parent control; evaluated actual body triangle anchors/normals transport its complete relative path. Per-child roots remain pinned even when free guide points are edited.','naturalMotionContactRuntimeOrCompleteOperationAccepted':False,'secondsBeforePreview':time.time()-tick})
 rows=[]
 for view in ['face','profile','back','body-face']:rows.append(v.image('a-scalp-ear',view));save('a-view-controls.json',rows)
 print('R97_COMPLETE_SCALP_EAR_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
