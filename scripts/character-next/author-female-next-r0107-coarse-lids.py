"""Direct native quad-cage eyelid sculpt with Blender's existing deformation tool.

Original rings are retained; no radial/geodesic fine-vertex rotation field.
The Ellie helper is a volume-guide reference, not a complete closed-eye model.
"""
from pathlib import Path
import bpy,numpy as np,json,time,datetime,importlib.util
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0107-native-coarse-lid-cage';SOURCE=R/'Reference/character/blender-human-base-meshes-v1.4.1/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend'
sp=importlib.util.spec_from_file_location('r107quad',Path(__file__).with_name('build-female-next-r0104-native-head-union.py'));u=importlib.util.module_from_spec(sp);sp.loader.exec_module(u);q=u.q
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8',newline='\n')
def main():
 tick=time.time();save('coarse-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':'Direct native coarse eye-ring edit and Laplacian deformation of existing quad hood; complete character assembly follows.','referenceLimits':'Ellie Blink helper is only an inspected smooth deformation volume, not actual eyelid closure or anatomy proof.'});data=np.load(E/'native-coarse-source.npz');rings=json.loads((E/'actual-native-quad-rings.json').read_text('utf8'));meta=json.loads((E.parent/'r0104-native-artist-ocular-foundation/native-head-references.json').read_text('utf8'))['animation'];M=np.array(meta['evaluatedWorldMatrix']);opt=json.loads((E.parent/'r0100-native-eyelid-assembly/native-eye-topology.json').read_text('utf8'))['eyes'];C=np.mean([x['posteriorSphereFitCentreWorld'] for x in opt.values()],0);scale=np.linalg.norm(np.array(opt['L']['posteriorSphereFitCentreWorld'])-opt['R']['posteriorSphereFitCentreWorld'])/.060;M[:3,:3]*=scale;M[:3,3]=(M[:3,3]-C)*scale+C
 with bpy.data.libraries.load(str(SOURCE),link=False) as (a,b):b.objects=['GEO-head_animation_realistic']
 ob=b.objects[0];bpy.context.scene.collection.objects.link(ob);ob.parent=None;ob.matrix_world=Matrix(M);ob.name='AFN107_ORIGINAL_COARSE_LID_AUTHORING_CAGE';raw=ob.data;local=q.arr(raw.vertices,'co',len(raw.vertices),3);P=local@M[:3,:3].T+M[:3,3];inverse=np.linalg.inv(M[:3,:3]);external=np.zeros(len(P),bool)
 for start,count in zip(data['faceStarts'],data['faceCounts']):
  uv=data['uv'][start:start+count]
  if np.all((uv[:,0]>.2)&(uv[:,0]<.8)&(uv[:,1]>.5)):external[data['loopVertexIDs'][start:start+count]]=True
 free=np.zeros(len(P),bool);margins=[]
 for side in ['L','R']:
  ids=np.array(rings[side]['rings'][0]);points=P[ids];margins.extend(ids.tolist());lo=points.min(0);hi=points.max(0);free|=external&(P[:,0]>lo[0]-.006)&(P[:,0]<hi[0]+.006)&(P[:,2]>lo[2]-.005)&(P[:,2]<hi[2]+.009)&(P[:,1]<hi[1]+.004)
 free[np.array(margins)]=False;anchors=np.flatnonzero(~free);group=ob.vertex_groups.new(name='AFN107_NATIVE_MARGIN_AND_ORBITAL_ANCHORS');group.add(anchors.tolist(),1.,'REPLACE');md=ob.modifiers.new('AFN107_NATIVE_QUAD_HOOD_LAPLACIAN_SCULPT','LAPLACIANDEFORM');md.vertex_group=group.name
 for x in bpy.context.selected_objects:x.select_set(False)
 ob.select_set(True);bpy.context.view_layer.objects.active=ob
 while ob.modifiers[0]!=md:bpy.ops.object.modifier_move_up(modifier=md.name)
 multi=[x for x in ob.modifiers if x.type=='MULTIRES']
 for x in multi:x.show_viewport=False;x.show_render=False
 bpy.context.view_layer.update();result=bpy.ops.object.laplaciandeform_bind(modifier=md.name);assert 'FINISHED' in result
 for x in multi:x.show_viewport=True;x.show_render=True;x.levels=x.render_levels=1
 bpy.context.view_layer.update();dd,V0,T=u.b.geom(ob);V0=V0.copy();T=T.copy();arrays={'neutralFineWorld':V0,'fineTriangles':T,'neutralCoarseLocal':local};reference=np.load(E.parent/'r0104-native-artist-ocular-foundation/animation-actual-source-geometry.npz');report={}
 for side in ['L','R']:
  ids=np.array(rings[side]['rings'][0]);points=P[ids];imin=int(points[:,0].argmin());imax=int(points[:,0].argmax());arcs=[]
  for direction in [1,-1]:
   path=[imin]
   while path[-1]!=imax:path.append((path[-1]+direction)%len(ids))
   arcs.append(ids[path])
  upper=max(arcs,key=lambda x:P[x,2].mean());lower=min(arcs,key=lambda x:P[x,2].mean());lp=P[lower[np.argsort(P[lower,0])]];ev=reference['GEO-head_animation_realistic.sclera.'+side+'-world'];ev=(ev-C)*scale+C;et=reference['GEO-head_animation_realistic.sclera.'+side+'-triangles'];tree=BVHTree.FromPolygons(ev.tolist(),et.tolist(),all_triangles=True)
  for label,value in [('half',.5),('closed',1.)]:
   target=P.copy();hits=0
   for i in ids:
    if i in [ids[imin],ids[imax]]:continue
    z=np.interp(P[i,0],lp[:,0],lp[:,2])+( .0001 if i in upper else -.0001);z=P[i,2]+value*(z-P[i,2]);hit,no,fi,distance=tree.ray_cast(Vector((P[i,0],ev[:,1].min()-.02,z)),Vector((0,1,0)))
    if hit is None:continue
    target[i]=[P[i,0],hit.y-.0004,z];hits+=1
   posed=(target-M[:3,3])@inverse.T;raw.vertices.foreach_set('co',posed.astype('f4').ravel());raw.update();ob.update_tag();bpy.context.view_layer.update();dd,V,TT=u.b.geom(ob);assert np.array_equal(T,TT);arrays[side+'_'+label+'_fineDelta']=V-V0;arrays[side+'_'+label+'_coarseLocal']=posed;report[side+'_'+label]={'actualNativeMarginAnchorVertices':len(ids),'actualOpticalRayHits':hits,'freeNativeQuadCageVertices':int(free.sum()),'fineMaximumMoveM':float(np.linalg.norm(V-V0,axis=1).max()),'nativeCoarseTopologyRetained':True,'guideClearanceNotFiniteContactProofM':.0004};raw.vertices.foreach_set('co',local.astype('f4').ravel());raw.update();ob.update_tag();bpy.context.view_layer.update()
 ob.shape_key_add(name='Basis')
 for side in ['L','R']:
  for label in ['half','closed']:ob.shape_key_add(name='AFN107_AUTHORING_'+side+'_'+label).data.foreach_set('co',arrays[side+'_'+label+'_coarseLocal'].astype('f4').ravel())
 ob.hide_render=True;ob['scope']='Original native coarse quad authoring source. Existing whole-body fine skin receives baked pose deltas; edits here are not automatically live-linked to that baked skin.';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(E/'native-coarse-authoring.blend'),compress=True);np.savez_compressed(E/'native-coarse-lid-poses.npz',**arrays);save('coarse-authoring.json',{'source':str(SOURCE),'nativeCoarseVertices':len(local),'nativeFineVertices':len(V0),'nativeFineTriangles':len(T),'construction':'Direct20-vertex native external lid edges, upper closure toward native lower margin, native original quad hood deformed by Blender Laplacian Deform with fixed outer orbital anchors; original Multires detail retained. No fine-vertex geodesic/radial rotation field.','poses':report,'freeVertices':np.flatnonzero(free),'fixedAnchorVertices':anchors,'reference':'Dan Ulrich original native head/quad flow CC0; Ellie native Blink helper inspected only as a smooth support-volume example, not a closed-eye anatomical measurement.','elapsedSeconds':time.time()-tick});print('R107_NATIVE_COARSE_POSES_AUTHORED',time.time()-tick,flush=True)
if __name__=='__main__':main()
