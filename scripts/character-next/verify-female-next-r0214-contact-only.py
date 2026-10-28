"""Independent native operation and discrete real mesh-contact falsifiers.
Card surface intersections are not full finite/self/continuous hair proof.
"""
from pathlib import Path
import bpy,numpy as np,json,datetime,hashlib,importlib.util
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=json.loads(Path('F:/AevryndStorage/character-development-paths.json').read_text('utf-8'));A=Path(p['directCharacterArchiveAccess']);E=A/'evidence/character-female-next/r0214-native-display-hair-modal-motion';b=json.loads((E/'build-summary.json').read_text());c=json.loads((E/'complete-display-modal-construction.json').read_text());n=np.load(E/'actual-display-modal-construction.npz');params=json.loads((E/'native-hair-modal-physics.json').read_text());spec=importlib.util.spec_from_file_location('r214base',A/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);a=m.a;h=m.h
def sha(f):return hashlib.file_digest(Path(f).open('rb'),'sha256').hexdigest()
def digest(x):return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
def save(name,q):(E/name).write_bytes((json.dumps(q,separators=(',',':'))+'\n').encode())
assert sha(b['output'])==b['sha256'];bpy.ops.wm.open_mainfile(filepath=b['output']);s=bpy.context.scene;hair=bpy.data.objects[b['actualHair']];old=bpy.data.objects[c['sourceOriginalHair']];skin=bpy.data.objects[b['actualSkin']];controls=[bpy.data.objects[x] for x in b['actualControls']];assert c['allSevenRawMeshUVSignaturesUnchanged']=={name:a.rawsig(bpy.data.objects[name]) for name in c['allSevenRawMeshUVSignaturesUnchanged']};ids=h.arr(hair.data.attributes['AFN214_PERSISTENT_ARTIST_VERTEX_ID'].data,'value',57424,dtype='i4');assert np.array_equal(ids,np.arange(57424));assert a.rawsig(hair)==a.rawsig(old)==c['newMeshUVSignature'];assert all(x.material==y.material for x,y in zip(old.material_slots,hair.material_slots));weights=np.column_stack([h.arr(hair.data.attributes['AFN214_VOLUME_WEIGHT_'+name].data,'value',57424) for name in params['regions']]);assert np.array_equal(weights,n['weights']);assert len(hair.data.shape_keys.key_blocks)==13 and len(hair.data.shape_keys.animation_data.drivers)==12
for fc in hair.data.shape_keys.animation_data.drivers:
 assert fc.driver.expression=='q' and len(fc.driver.variables)==1;target=fc.driver.variables[0].targets[0];assert target.id in controls;assert target.id.path_resolve(target.data_path) is not None
s.frame_set(1);bpy.context.view_layer.update();base,T=a.geometry(hair);oldBase,oldT=a.geometry(old);assert np.array_equal(base,oldBase) and np.array_equal(T,oldT);ctrl=controls[0];neutral=float(ctrl['offset_x_m']);ctrl['offset_x_m']=.001;ctrl.update_tag();bpy.context.view_layer.update();moved,MT=a.geometry(hair);expected=base+weights[:,0,None]*np.array([.001,0,0]);manualError=float(np.linalg.norm(moved-expected,axis=1).max());assert manualError<3e-6;manualMove=float(np.linalg.norm(moved-base,axis=1).max());assert manualMove>.0001;ctrl['offset_x_m']=neutral;ctrl.update_tag();bpy.context.view_layer.update();restored,_=a.geometry(hair);assert np.array_equal(restored,base);operation=[];maxPrediction=0;maxPin=0;triObservations=[];baseLoopIDs=h.arr(hair.data.loops,'vertex_index',len(hair.data.loops),dtype='i4');basePolyStart=h.arr(hair.data.polygons,'loop_start',len(hair.data.polygons),dtype='i4');basePolyCount=h.arr(hair.data.polygons,'loop_total',len(hair.data.polygons),dtype='i4');enginePath=Path(p['directProjectAccess'])/'engine/character/hair_modal_reference.py';engineSpec=importlib.util.spec_from_file_location('engine_r214_native_check',enginePath);engine=importlib.util.module_from_spec(engineSpec);engineSpec.loader.exec_module(engine);engineTrajectory=engine.simulate(params);assert np.max(abs(engineTrajectory-n['trajectoryMetres']))<1e-7
def triangleOverlap(A,B):
 ea=np.roll(A,-1,axis=1)-A;eb=np.roll(B,-1,axis=1)-B;na=np.cross(ea[:,0],ea[:,1]);nb=np.cross(eb[:,0],eb[:,1]);alive=np.ones(len(A),bool);axes=[na,nb]+[np.cross(ea[:,i],eb[:,j]) for i in range(3) for j in range(3)]+[np.cross(na,ea[:,i]) for i in range(3)]+[np.cross(nb,eb[:,i]) for i in range(3)]
 for axis in axes:
  norm=np.linalg.norm(axis,axis=1);valid=norm>1e-16;unit=axis/np.maximum(norm[:,None],1e-30);pa=np.einsum('nvc,nc->nv',A,unit);pb=np.einsum('nvc,nc->nv',B,unit);separate=(pa.max(1)<pb.min(1)-1e-8)|(pb.max(1)<pa.min(1)-1e-8);alive&=~(valid&separate)
 return alive
ref=np.array([[0,0,0],[1,0,0],[0,1,0]],'f8');cases=np.array([[[.2,.2,-1],[.2,.2,1],[.8,.2,0]],[[2,2,0],[3,2,0],[2,3,0]],[[.1,.1,0],[.2,.1,0],[.1,.2,0]],[[0,0,1],[1,0,1],[0,1,1]]]);assert np.array_equal(triangleOverlap(np.repeat(ref[None,:,:],4,axis=0),cases),[True,False,True,False])
def intersections(V,HV,W,SV):
 ha=BVHTree.FromPolygons(V.tolist(),HV.tolist(),all_triangles=True);sb=BVHTree.FromPolygons(W.tolist(),SV.tolist(),all_triangles=True);pairs=np.array(ha.overlap(sb),dtype='i4').reshape(-1,2);kept=[]
 for lo in range(0,len(pairs),4096):
  z=pairs[lo:lo+4096];mask=triangleOverlap(V[HV[z[:,0]]],W[SV[z[:,1]]]);kept.append(z[mask])
 return (np.vstack(kept) if kept else np.empty((0,2),'i4')),len(pairs)
def segmentTriangle(p,q,tri):
 d=q-p;e1=tri[1]-tri[0];e2=tri[2]-tri[0];h0=np.cross(d,e2);det=float(e1@h0)
 if abs(det)<1e-14:return None
 inv=1/det;v=p-tri[0];u=float(v@h0)*inv;r=np.cross(v,e1);w=float(d@r)*inv;t0=float(e2@r)*inv
 if min(u,w,t0)>=-1e-8 and u+w<=1+1e-8 and t0<=1+1e-8:return p+t0*d
 return None
def crossingPoint(a,b):
 for aa,bb in [(a,b),(b,a)]:
  for j in range(3):
   point=segmentTriangle(aa[j],aa[(j+1)%3],bb)
   if point is not None:return point
 return None
# Evaluate only the actual original Hair material alpha branch we can prove.
mat=hair.material_slots[0].material;out=next(x for x in mat.node_tree.nodes if x.type=='OUTPUT_MATERIAL' and x.is_active_output);surfaceNode=out.inputs['Surface'].links[0].from_node if out.inputs['Surface'].is_linked else None;pixelCache={};alphaEvidence={'material':mat.name,'activeSurfaceNode':surfaceNode.bl_idname if surfaceNode else None,'supported':bool(surfaceNode and surfaceNode.type=='BSDF_PRINCIPLED'),'note':'Alpha>=0.5 sampled at exact geometric crossing witness is an occupied-card opacity witness; not camera visibility, full filtered renderer occupancy or finite/continuous contact proof.'}
def socketValue(socket,uv):
 if not socket.is_linked:return float(socket.default_value)
 link=socket.links[0];node=link.from_node
 if node.type=='REROUTE':return socketValue(node.inputs[0],uv)
 if node.type=='VALUE':return float(node.outputs[0].default_value)
 if node.type=='MATH':
  vals=[socketValue(x,uv) for x in list(node.inputs)[:2]];op=node.operation
  if op=='MULTIPLY':v=vals[0]*vals[1]
  elif op=='ADD':v=vals[0]+vals[1]
  elif op=='SUBTRACT':v=vals[0]-vals[1]
  elif op=='MINIMUM':v=min(vals)
  elif op=='MAXIMUM':v=max(vals)
  elif op=='GREATER_THAN':v=float(vals[0]>vals[1])
  elif op=='LESS_THAN':v=float(vals[0]<vals[1])
  else:raise ValueError('Unsupported actual alpha math '+op)
  return float(np.clip(v,0,1)) if node.use_clamp else float(v)
 if node.type=='TEX_IMAGE' and link.from_socket.name=='Alpha':
  if node.inputs['Vector'].is_linked:
   vec=node.inputs['Vector'].links[0];assert vec.from_node.type in ['UVMAP','TEX_COORD'] and vec.from_socket.name in ['UV','UV Map'],'Unsupported actual texture coordinates'
  image=node.image;assert image is not None and image.source in ['FILE','GENERATED','VIEWER'] and image.tiles and len(image.tiles)==1;w,h0=image.size
  if image.name not in pixelCache:
   pixels=np.empty(w*h0*4,'f4');image.pixels.foreach_get(pixels);pixelCache[image.name]=pixels.reshape(h0,w,4)[:,:,3]
  pixels=pixelCache[image.name];xy=np.array(uv)*np.array([w,h0])-.5;lo=np.floor(xy).astype(int);f=xy-lo
  def alpha(x,y):
   if node.extension=='REPEAT':return float(pixels[y%h0,x%w])
   if node.extension=='EXTEND':return float(pixels[np.clip(y,0,h0-1),np.clip(x,0,w-1)])
   if node.extension=='CLIP':return float(pixels[y,x]) if 0<=x<w and 0<=y<h0 else 0.0
   raise ValueError('Unsupported extension')
  if node.interpolation=='Closest':return alpha(int(np.floor(xy[0]+.5)),int(np.floor(xy[1]+.5)))
  assert node.interpolation=='Linear','Unsupported alpha interpolation';return alpha(lo[0],lo[1])*(1-f[0])*(1-f[1])+alpha(lo[0]+1,lo[1])*f[0]*(1-f[1])+alpha(lo[0],lo[1]+1)*(1-f[0])*f[1]+alpha(lo[0]+1,lo[1]+1)*f[0]*f[1]
 raise ValueError('Unsupported actual alpha branch '+node.bl_idname+'/'+link.from_socket.name)
contact=[]
for frame in [1,b['peakFrame'],b['settledFrame']]:
 s.frame_set(frame);bpy.context.view_layer.update();V,HV=a.geometry(hair);OV,OT=a.geometry(old);SW,ST=a.geometry(skin);pairs,broad=intersections(V,HV,SW,ST);baseline,broadBase=intersections(OV,OT,SW,ST);factor=len(ST)+1;de=hair.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;de.calc_loop_triangles();od=old.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;od.calc_loop_triangles();hairPoly=np.array([z.polygon_index for z in de.loop_triangles],'i8');oldPoly=np.array([z.polygon_index for z in od.loop_triangles],'i8');encoded=hairPoly[pairs[:,0]]*factor+pairs[:,1];before=oldPoly[baseline[:,0]]*factor+baseline[:,1];new=np.setdiff1d(encoded,before);selected=pairs[np.isin(encoded,new)];loops=np.array([x.loops[:] for x in de.loop_triangles]);uvFaces=h.arr(de.uv_layers.active.data,'uv',len(de.uv_layers.active.data),2)[loops];witnesses=[];opaque=[];alphaError=None
 for hi,si in selected[:128]:
  point=crossingPoint(V[HV[hi]],SW[ST[si]])
  if point is None:continue
  tri=V[HV[hi]];bc0=np.linalg.lstsq(np.column_stack([tri[1]-tri[0],tri[2]-tri[0]]),point-tri[0],rcond=None)[0];bc=np.array([1-bc0.sum(),*bc0]);uv=bc@uvFaces[hi];row={'hairTriangle':int(hi),'skinTriangle':int(si),'worldPoint':point.tolist(),'hairBarycentric':bc.tolist(),'hairUV':uv.tolist()}
  if alphaEvidence['supported']:
   try:row['actualMaterialAlphaAtCrossing']=socketValue(surfaceNode.inputs['Alpha'],uv)
   except Exception as error:alphaError=repr(error)
  witnesses.append(row)
  if row.get('actualMaterialAlphaAtCrossing',0)>=.5:opaque.append(row)
  if len(opaque)>=8:break
 contact.append({'frame':frame,'actualHairVertices':len(V),'actualHairTriangles':len(HV),'actualSkinTriangles':len(ST),'broadCandidatePairs':broad,'surfaceIntersectionPairs':len(pairs),'originalRestHairSurfaceIntersectionsSameBodyPose':len(baseline),'newGeometricCrossingsVsOriginalHairSameBodyPose':len(new),'newCrossingIdentityDefinition':'Persistent hair polygon ID paired with same-pose Skin triangle ID; frame-specific render diagonals not treated as persistent triangle identities.','allIntersectionPairIDsSHA256':digest(pairs),'newPairIDsSHA256':digest(selected),'newCrossingWitnesses':witnesses[:16],'alphaAtLeastHalfNewCrossingWitnesses':opaque,'alphaEvaluationError':alphaError,'actualSkinWorldFloat32SHA256':digest(SW.astype('f4')),'allHairTrianglesIncludingFixedRootBandTested':True,'noFailureExcludedOrGeometryMovedToPass':True});save('actual-discrete-display-mesh-contact-falsifier.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':b['output'],'sourceSHA256':b['sha256'],'frames':contact,'materialAlphaBranch':alphaEvidence,'triangleSATPrimitiveCasesPassed':True,'surfaceIntersectionDefinition':'Triangle SAT with cross-edge and coplanar in-plane axes,1e-8m geometric tolerance, after actual evaluated world mesh BVH broad phase. Touch/intersection is not volumetric signed penetration depth.','scope':'Actual full mesh card surfaces, finite thickness/self/continuous contact not proved. Material alpha tested only sampled new crossing witnesses where supported, not full renderer occupancy.','fixedHeadWindOnlyNoHeadTurnAbruptStopOrClothing':True,'collisionResponseImplemented':False,'naturalHairAndFullContactAccepted':False,'globalMinimumSignedDistanceM':None})
assert sha(b['output'])==b['sha256'];print('R214_REAL_MESH_CONTACT_LOCATORS_ONLY_COMPLETE',json.dumps({'frameContacts':[{k:r[k] for k in ['frame','surfaceIntersectionPairs','newGeometricCrossingsVsOriginalHairSameBodyPose']} for r in contact],'opaqueNewWitnesses':sum(len(r['alphaAtLeastHalfNewCrossingWitnesses']) for r in contact),'nativeOperationExact':False}),flush=True)

exec(compile(Path('F:/AevryndEvidence/CharacterTemp/decode-r214-motion.py').read_text('utf-8'),'decode-r214-motion.py','exec'))
