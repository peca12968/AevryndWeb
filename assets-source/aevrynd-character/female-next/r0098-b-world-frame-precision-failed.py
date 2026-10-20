"""Different head construction: retain the artist's original fine topology,
bridge its neck to the existing body boundary, and drive it from the retained
head control cage. Do not non-rigidly warp the original eyes or rigid teeth.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0098-whole-head-foundation';S=R/'engine/assets/characters/female-next/source';SRC=S/'aevrynd-female-next-r0097-neutral-scalp-control-reference.blend';OUT=S/'aevrynd-female-next-r0098-b-native-artist-head.blend'
def mod(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);return a
v=mod('r98nativeviews','render-female-next-r0091-matched.py');v.E=E;m=v.m;q=m.q;barymod=mod('r98nativebary','build-female-next-r0094-growth-volume.py')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8')
def loop_low(V,T):
 edges=np.sort(np.concatenate([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]),axis=1);unique,count=np.unique(edges,axis=0,return_counts=True);boundary=unique[count==1];adj={}
 for a,b in boundary:adj.setdefault(int(a),[]).append(int(b));adj.setdefault(int(b),[]).append(int(a))
 remaining=set(adj);loops=[]
 while remaining:
  start=next(iter(remaining));chain=[start];prev=-1;cur=start
  for _ in range(len(adj)+1):
   choices=[x for x in adj[cur] if x!=prev];assert choices;following=choices[0]
   if following==start:break
   assert following not in chain;chain.append(following);prev,cur=cur,following
  remaining-=set(chain);loops.append(np.array(chain,'i4'))
 assert loops;loop=min(loops,key=lambda a:V[a,2].mean());p=V[loop];area=np.sum(p[:,0]*np.roll(p[:,1],-1)-np.roll(p[:,0],-1)*p[:,1]);loop=loop if area>0 else loop[::-1];i=int(np.argmax(V[loop,0]));return np.roll(loop,-i),len(loops)
def interface(name):
 ng=bpy.data.node_groups.new(name,'GeometryNodeTree');ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');return ng,ng.nodes,ng.links
def mask_graph(geometryObject,lookup,keep_head=False):
 ng,n,L=interface('AFN98_HEAD_FACE_SELECTION');inp=n.new('NodeGroupInput');out=n.new('NodeGroupOutput')
 if geometryObject:
  obj=n.new('GeometryNodeObjectInfo');obj.transform_space='RELATIVE';obj.inputs['Object'].default_value=geometryObject;obj.inputs['As Instance'].default_value=False;geom=obj.outputs['Geometry']
 else:geom=inp.outputs['Geometry']
 tab=n.new('GeometryNodeObjectInfo');tab.transform_space='RELATIVE';tab.inputs['Object'].default_value=lookup;tab.inputs['As Instance'].default_value=False;ids=n.new('GeometryNodeInputNamedAttribute');ids.data_type='INT';ids.inputs['Name'].default_value='AFN60_NativeFaceID';flag=n.new('GeometryNodeInputNamedAttribute');flag.data_type='FLOAT';flag.inputs['Name'].default_value='AFN98_IsHead';sample=n.new('GeometryNodeSampleIndex');sample.data_type='FLOAT';sample.domain='POINT';sample.clamp=False;L.new(tab.outputs['Geometry'],sample.inputs['Geometry']);L.new(ids.outputs['Attribute'],sample.inputs['Index']);L.new(flag.outputs['Attribute'],sample.inputs['Value']);test=n.new('ShaderNodeMath');test.operation='LESS_THAN' if keep_head else 'GREATER_THAN';test.inputs[1].default_value=.5;L.new(sample.outputs['Value'],test.inputs[0]);delete=n.new('GeometryNodeDeleteGeometry');delete.domain='FACE';L.new(geom,delete.inputs['Geometry']);L.new(test.outputs[0],delete.inputs['Selection']);L.new(delete.outputs['Geometry'],out.inputs['Geometry']);return ng
def pin_neck(head,body,body_indices,collar):
 d=head.data;a=d.attributes.new('AFN98_NeckBodyVertex','INT','POINT');a.data.foreach_set('value',body_indices);a=d.attributes.new('AFN98_NeckPin','BOOLEAN','POINT');a.data.foreach_set('value',collar);ng,n,L=interface('AFN98_EXACT_SHARED_NECK_BOUNDARY');inp=n.new('NodeGroupInput');out=n.new('NodeGroupOutput');obj=n.new('GeometryNodeObjectInfo');obj.transform_space='RELATIVE';obj.inputs['Object'].default_value=body;obj.inputs['As Instance'].default_value=False;ids=n.new('GeometryNodeInputNamedAttribute');ids.data_type='INT';ids.inputs['Name'].default_value='AFN98_NeckBodyVertex';selection=n.new('GeometryNodeInputNamedAttribute');selection.data_type='BOOLEAN';selection.inputs['Name'].default_value='AFN98_NeckPin';pos=n.new('GeometryNodeInputPosition');sample=n.new('GeometryNodeSampleIndex');sample.data_type='FLOAT_VECTOR';sample.domain='POINT';sample.clamp=False;L.new(obj.outputs['Geometry'],sample.inputs['Geometry']);L.new(pos.outputs['Position'],sample.inputs['Value']);L.new(ids.outputs['Attribute'],sample.inputs['Index']);setpos=n.new('GeometryNodeSetPosition');L.new(inp.outputs['Geometry'],setpos.inputs['Geometry']);L.new(selection.outputs['Attribute'],setpos.inputs['Selection']);L.new(sample.outputs['Value'],setpos.inputs['Position']);L.new(setpos.outputs['Geometry'],out.inputs['Geometry']);md=head.modifiers.new('AFN98_LIVE_NECK_VERTEX_ATTACHMENT','NODES');md.node_group=ng
def main():
 tick=time.time();assert not OUT.exists() and sha(SRC)=='353a3067e87bd6617cabb709ac5e8fc23f947f6841d2af95e835824369cec69b';ref=json.loads((E/'official-female-reference.json').read_text('utf8'));plan=json.loads((E/'a-head-envelope-plan.json').read_text('utf8'));h0=np.load(E/'a-whole-head-lineage.npz');current=h0['oldNativeWorld'];canonical=np.load(R/'Evidence/character-female-next/r0057-coherent-foundation/canonical-mesh-data.npz');nativeSource=np.load(E.parent/'r0092-native-compatible-groom/native-Eve-source.npz');T0=nativeSource['triangles'];faceIDs=np.repeat(np.arange(len(nativeSource['sourceFaceCounts'])),nativeSource['sourceFaceCounts']-2);mi=np.repeat(canonical['materials'],nativeSource['sourceFaceCounts']-2);selectedFaces=np.unique(faceIDs[np.isin(mi,[4,5])&(current[T0,2].min(1)>1.32)])
 bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();body=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING'];skin=bpy.data.objects['AFN74_SKIN_AND_EXISTING_OCULAR_LINING'];oldRow=m.rig.k.mesh(skin);OV,OT=oldRow['V'],oldRow['T'];remove=np.isin(oldRow['nativeTriangleFace'],selectedFaces);oldLoop,oldBoundaryComponents=loop_low(OV,OT[remove]);assert OV[oldLoop,2].mean()<1.4;data,oldWorld=q.geom(skin);data.calc_loop_triangles();assert np.array_equal(OT,q.arr(data.loop_triangles,'vertices',len(data.loop_triangles),3,dtype='i4'));triLoops=q.arr(data.loop_triangles,'loops',len(data.loop_triangles),3,dtype='i4');uvs={u.name:q.arr(u.data,'uv',len(data.loops),2) for u in data.uv_layers};oldMatIndices=q.arr(data.polygons,'material_index',len(data.polygons),dtype='i4');oldTriMats=np.array([oldMatIndices[t.polygon_index] for t in data.loop_triangles]);oldTree=BVHTree.FromPolygons(OV.tolist(),OT.tolist(),all_triangles=True);materials=list(data.materials)
 # Read the original fine sculpt level, not the projected old-head topology.
 with bpy.data.libraries.load(ref['source'],link=False) as (a,b):b.objects=['GEO-body_female_realistic']
 donor=b.objects[0];s.collection.objects.link(donor);donor.hide_render=True
 for md in donor.modifiers:
  if md.type=='MULTIRES':md.levels=md.render_levels=md.total_levels
 bpy.context.view_layer.update();dd,DV=q.geom(donor);dd.calc_loop_triangles();DT=q.arr(dd.loop_triangles,'vertices',len(dd.loop_triangles),3,dtype='i4');M=np.array(ref['stageWorldTransform']);DV=DV@M[:3,:3].T+M[:3,3];DV=(DV-np.array(plan['sourceMean']))@np.array(plan['sourceRotation']).T*plan['sourceScale']+np.array(plan['targetMean']);donorLevel=max(md.total_levels for md in donor.modifiers if md.type=='MULTIRES');bpy.data.objects.remove(donor,do_unlink=True);headFaces=DT[DV[DT,2].min(1)>1.34];used,inverse=np.unique(headFaces,return_inverse=True);HV=DV[used];HT=inverse.reshape(-1,3);donorLoop,donorBoundaryComponents=loop_low(HV,HT);neck=OV[oldLoop];start=len(HV);vertices=np.vstack((HV,neck));bottom=np.arange(start,len(vertices),dtype='i4');upper=donorLoop
 def arc(p):
  a=np.r_[0,np.cumsum(np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1))];return a/a[-1]
 u=arc(vertices[upper]);w=arc(neck);i=j=0;bridge=[]
 while i<len(upper) or j<len(bottom):
  ai=int(upper[i%len(upper)]);bj=int(bottom[j%len(bottom)])
  if j==len(bottom) or (i<len(upper) and u[i+1]<=w[j+1]):tri=[ai,bj,int(upper[(i+1)%len(upper)])];i+=1
  else:tri=[ai,bj,int(bottom[(j+1)%len(bottom)])];j+=1
  pts=vertices[tri];normal=np.cross(pts[1]-pts[0],pts[2]-pts[0]);radial=pts.mean(0)-neck.mean(0);radial[2]=0
  if np.dot(normal,radial)<0:tri[1],tri[2]=tri[2],tri[1]
  bridge.append(tri)
 faces=np.vstack((HT,np.array(bridge,'i4')));mesh=bpy.data.meshes.new('AFN98_ORIGINAL_ARTIST_HEAD_AND_NECK_COLLAR');mesh.from_pydata(vertices.tolist(),[],faces.tolist());mesh.update();head=bpy.data.objects.new(mesh.name,mesh);s.collection.objects.link(head)
 for mat in materials:mesh.materials.append(mat)
 # Data transfer of existing skin UVs/materials, without changing source head
 # vertex positions or pretending the two UV atlases originally correspond.
 vertexUV={name:np.empty((len(vertices),2),'f4') for name in uvs};nearestFace=np.empty(len(vertices),'i4')
 for k,pt in enumerate(vertices):
  co,no,f,distance=oldTree.find_nearest(Vector(pt));nearestFace[k]=f;weights=barymod.barycentric_closest(np.array(co),OV[OT[f]])
  for name,uv in uvs.items():vertexUV[name][k]=weights@uv[triLoops[f]]
 for name,uv in vertexUV.items():layer=mesh.uv_layers.new(name=name);layer.data.foreach_set('uv',uv[np.array([l.vertex_index for l in mesh.loops])].ravel())
 for poly in mesh.polygons:poly.use_smooth=True;poly.material_index=int(oldTriMats[nearestFace[poly.vertices[0]]])
 # Exact old/native face-ID table provides a fixed topology control patch.
 tm=bpy.data.meshes.new('AFN98_HEAD_FACE_ID_TABLE');tm.vertices.add(len(nativeSource['sourceFaceCounts']));at=tm.attributes.new('AFN98_IsHead','FLOAT','POINT');flags=np.zeros(len(tm.vertices),'f4');flags[selectedFaces]=1;at.data.foreach_set('value',flags);lookup=bpy.data.objects.new(tm.name,tm);s.collection.objects.link(lookup);lookup.hide_render=True;lookup.hide_set(True);cm=bpy.data.meshes.new('AFN98_LIVE_ORIGINAL_HEAD_CAGE');cage=bpy.data.objects.new(cm.name,cm);s.collection.objects.link(cage);cage.hide_render=True;md=cage.modifiers.new('AFN98_ORIGINAL_HEAD_CONTROL_PATCH','NODES');md.node_group=mask_graph(body,lookup,True);triangulate=cage.modifiers.new('AFN98_FIXED_CAGE_TRIANGULATION','TRIANGULATE');triangulate.quad_method='FIXED';bpy.context.view_layer.update();cd,cw=q.geom(cage);assert len(cd.polygons)>1000;sd=head.modifiers.new('AFN98_RETAINED_FACIAL_CONTROL_DRIVER','SURFACE_DEFORM');sd.target=cage
 for ob in bpy.context.selected_objects:ob.select_set(False)
 head.select_set(True);bpy.context.view_layer.objects.active=head;bpy.context.view_layer.update();bpy.ops.object.surfacedeform_bind(modifier=sd.name);assert sd.is_bound
 # Match the actual existing body's boundary vertex identities, including
 # under motion. Independent head/body surfaces share this exact geometric
 # boundary; welded export/manifold qualification is still pending.
 bRow=m.rig.k.mesh(body);BV=bRow['V'];kd=KDTree(len(BV))
 for k,pt in enumerate(BV):kd.insert(pt,k)
 kd.balance();bodyNeck=[];neckMatch=[]
 for pt in neck:co,k,dist=kd.find(Vector(pt));bodyNeck.append(k);neckMatch.append(dist)
 assert max(neckMatch)<2e-6;indices=np.zeros(len(vertices),'i4');indices[bottom]=bodyNeck;collar=np.zeros(len(vertices),bool);collar[bottom]=True;pin_neck(head,body,indices,collar);mask=skin.modifiers.new('AFN98_REPLACE_OUTER_HEAD_REGION_ONLY','NODES');mask.node_group=mask_graph(None,lookup,False);bpy.context.view_layer.update()
 # Preserve rigid eyes and teeth. External facial fibre helpers use only the
 # small retained outer attachment offsets; A's large tooth warp is discarded.
 deltas=h0['attachmentAppliedWorldDelta'];offset=0;facial=[]
 for name in ['AFN59_BROWS_NATIVE_POINT_POSES','AFN59_LASHES_NATIVE_POINT_POSES']:
  ob=bpy.data.objects[name];count=len(ob.data.vertices);delta=deltas[offset:offset+count]@np.linalg.inv(np.array(ob.matrix_world)[:3,:3]).T;offset+=count
  for block in ob.data.shape_keys.key_blocks:
   p=q.arr(block.data,'co',count,3);block.data.foreach_set('co',(p+delta).astype('f4').ravel())
  facial.append({'object':name,'points':count,'maximumWorldDeltaM':float(np.linalg.norm(deltas[offset-count:offset],axis=1).max())})
 bpy.context.view_layer.update();hd,actualHead=q.geom(head);hd.calc_loop_triangles();headT=q.arr(hd.loop_triangles,'vertices',len(hd.loop_triangles),3,dtype='i4');eligible=np.flatnonzero(actualHead[headT,2].min(1)>np.mean(plan['targetEyeCentres'],axis=0)[2]-.09);scalp=BVHTree.FromPolygons(actualHead.tolist(),headT[eligible].tolist(),all_triangles=True);hair=bpy.data.objects['AFN97_TUCKED_ARTIST_BOB_CHILDREN'];oldHair=q.hair(hair).reshape(24800,17,3);HA=np.array(hair.matrix_world);Hinv=np.linalg.inv(HA[:3,:3]);radius=float(q.arr(hair.data.attributes['radius'].data,'value',24800*17).max());rootVerts=np.empty((24800,3),'i4');bary=np.empty((24800,3));root=np.empty((24800,3));rt=np.empty_like(root);rb=np.empty_like(root);rn=np.empty_like(root)
 for k,pt in enumerate(oldHair[:,0]):
  co,no,j,dist=scalp.find_nearest(Vector(pt));ids=headT[eligible[j]];tri=actualHead[ids];weight=barymod.barycentric_closest(np.array(co),tri);local=(tri-HA[:3,3])@Hinv.T;t=local[1]-local[0];t/=np.linalg.norm(t);n=np.cross(local[1]-local[0],local[2]-local[0]);n/=np.linalg.norm(n);rootVerts[k]=ids;bary[k]=weight;rt[k]=t;rn[k]=n;rb[k]=np.cross(n,t);root[k]=weight@local+n*radius
 def set_attr(name,data):hair.data.attributes[name].data.foreach_set('vector' if np.asarray(data).ndim==2 else 'value',np.asarray(data,'i4' if np.issubdtype(np.asarray(data).dtype,np.integer) else 'f4').ravel())
 for j in range(3):set_attr('AFN97_ScalpVertex'+str(j),rootVerts[:,j])
 for name,data in [('RootBarycentric',bary),('RestRoot',root),('RestT',rt),('RestB',rb),('RestN',rn)]:set_attr('AFN97_'+name,data)
 for md in hair.modifiers:
  if md.type=='NODES':
   md.node_group=md.node_group.copy();md.node_group.name='AFN98_ACTUAL_NEW_HEAD_ROOT_FRAMES'
   for node in md.node_group.nodes:
    if node.bl_idname=='GeometryNodeObjectInfo' and node.inputs['Object'].default_value==body:node.inputs['Object'].default_value=head
 bpy.context.view_layer.update();P=q.hair(hair).reshape(oldHair.shape);assert np.isfinite(P).all();freeError=float(np.linalg.norm(P[:,1:]-oldHair[:,1:],axis=2).max());assert freeError<6e-6,freeError;neckError=float(np.linalg.norm(actualHead[bottom]-BV[bodyNeck],axis=1).max());head['scope']='Original Dan Ulrich CC0 fine female head topology, transferred existing skin UV/material, triangulated collar to exactly matching old neck boundary, SurfaceDeform driver from unchanged original head control cage plus live boundary vertex pin. Independent geometric seam not yet welded/certified as one manifold or fully qualified facial motion/contact/runtime.';head['sourceCredit']='Dan Ulrich / Blender Human Base Meshes1.4.1, selected asset metadata CC0. Original source geometry, not exclusively owned Aevrynd artwork; inherited skin/Brown notices remain.';m.rig.shade.settings();m.rig.k.b.camera('face');s.camera.data.lens=85;s.render.hair_subdiv=3;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
 np.savez_compressed(E/'b-native-head-lineage.npz',headRestWorld=vertices,headTriangles=faces,sourceHeadVertexIDs=used,sourceHeadOriginalTriangles=HT,neckHeadVertexIDs=bottom,neckBodyVertexIDs=np.array(bodyNeck,'i4'),originalNeckSkinVertexIDs=oldLoop,selectedOriginalHeadFaceIDs=selectedFaces,hairOldWorld=oldHair,hairNewWorld=P.astype('f4'),hairRootHeadVertices=rootVerts,hairRootBarycentric=bary,hairRestRootNative=root,hairRestT=rt,hairRestB=rb,hairRestN=rn)
 save('b-build-summary.json',{'source':str(SRC),'sourceSha256':sha(SRC),'output':str(OUT),'outputSha256':sha(OUT),'outputBytes':OUT.stat().st_size,'headObject':head.name,'controlCageObject':cage.name,'lookupObject':lookup.name,'hairObject':hair.name,'sourceReference':ref['source'],'sourceReferenceSha256':ref['sourceSha256'],'sourceMetadata':ref['metadata'],'sourceSculptLevel':donorLevel,'originalHeadVertices':len(HV),'originalHeadTriangles':len(HT),'collarVertices':len(bottom),'collarTriangles':len(bridge),'donorBoundaryComponents':donorBoundaryComponents,'originalControlBoundaryComponents':oldBoundaryComponents,'headNativeTopologyAndGeometryRetainedExceptNeckCollar':True,'neckOriginalBodyVertexMatchMaximumM':max(neckMatch),'neutralActualNeckBoundaryMaximumWorldErrorM':neckError,'eyesAndRigidTeethOriginalDataUnchanged':True,'externalFacialHelperRetarget':facial,'all24800HairRootsReboundToActualNewHeadTopology':True,'hairFreeControlPointsMaximumWorldChangeM':freeError,'rootRegionScope':'Reconstructed spatial scalp-region attachment from retained original roots; not source-author follicle/emission identity or finite-root validation. Old head triangle IDs/certificates not reused.','neckScope':'Exact coincident live boundary across two rendered component meshes; joined/welded export and actual whole-skin manifold not yet certified.','newHeadControlScope':'Retained actual head control cage drives source head; full expression/skin/teeth contacts and natural hair movement not qualified.','appearanceFunctionContactsRuntimeOrCompleteGainAccepted':False,'secondsBeforePreview':time.time()-tick});rows=[]
 for view in ['face','profile','oblique','body-face']:rows.append(v.image('b-native-head',view));save('b-view-controls.json',rows)
 print('R98_COMPLETE_NATIVE_ARTIST_HEAD_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
