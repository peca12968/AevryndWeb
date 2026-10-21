"""One full woman with original artist head and explicitly reconstructed neck.
Planar cuts and shared angular edge partition replace unequal nonplanar zipper.
No head/teeth projection, source shape warp, or parameter sweep.
"""
from pathlib import Path
import bpy,bmesh,numpy as np,json,time,datetime,importlib.util,math
from mathutils import Matrix
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0126-individual-head-foundation';D=S/'r0126-source/individual-head-input';GLB=D/'artist-head-27f75fa94c384000bb6a79a3000f8e80.glb';SRC=S/'r0117-source/aevrynd-female-next-r0117-a-native-fibre-brows.blend';OUT=S/'r0126-source/aevrynd-female-next-r0126-a-individual-artist-head.blend'
sp=importlib.util.spec_from_file_location('r126base',Path(__file__).with_name('build-female-next-r0116-native-eye-character.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b;q=a.q;b.u.v.E=E
def save(n,d):(E/n).write_text(json.dumps(d,indent=2,default=lambda x:x.tolist() if isinstance(x,np.ndarray) else x.item())+'\n',encoding='utf-8',newline='\n')
def world_copy(ob,name):
 deps=bpy.context.evaluated_depsgraph_get();ev=ob.evaluated_get(deps);me=bpy.data.meshes.new_from_object(ev,preserve_all_data_layers=True,depsgraph=deps);me.transform(ob.matrix_world);copy=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(copy);return copy
def cut(ob,z,upper):
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-8);bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-9,plane_co=(0,0,z),plane_no=(0,0,1),clear_inner=upper,clear_outer=not upper);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-8);bm.normal_update();return bm
def ring(bm,z):
 edges=[e for e in bm.edges if len(e.link_faces)==1 and all(abs(v.co.z-z)<2e-7 for v in e.verts)];verts={v for e in edges for v in e.verts};assert len(edges)>8 and len(verts)==len(edges),(len(verts),len(edges));assert all(sum(e in edges for e in v.link_edges)==2 for v in verts);P=np.array([v.co[:] for v in verts]);center=(P[:,:2].min(0)+P[:,:2].max(0))*.5;ordered=sorted(verts,key=lambda v:math.atan2(v.co.y-center[1],v.co.x-center[0])%(2*math.pi));theta=np.array([math.atan2(v.co.y-center[1],v.co.x-center[0])%(2*math.pi) for v in ordered]);assert all(bm.edges.get((u,v)) in edges for u,v in zip(ordered,ordered[1:]+ordered[:1]));assert np.diff(np.r_[theta,theta[0]+2*math.pi]).max()<math.pi
 return ordered,theta,center
def split_partition(bm,ordered,theta,center,allAngles):
 result={};cross=lambda u,v:float(u[0]*v[1]-u[1]*v[0])
 for i,u in enumerate(ordered):
  v=ordered[(i+1)%len(ordered)];lo=theta[i];hi=theta[(i+1)%len(ordered)]+(2*math.pi if i==len(ordered)-1 else 0);result[float(lo)]=u;A=np.array(u.co[:2]);B=np.array(v.co[:2]);current=u;previous=0.
  candidates=[float(t) for t in allAngles if lo+1e-9<t<hi-1e-9]
  if i==len(ordered)-1:candidates += [float(t)+2*math.pi for t in allAngles if float(t)+2*math.pi<hi-1e-9]
  for t in sorted(candidates):
   direction=np.array([math.cos(t),math.sin(t)]);den=cross(B-A,direction);assert abs(den)>1e-12;part=cross(center-A,direction)/den;assert previous<part<1.;edge=bm.edges.get((current,v));assert edge;_,nv=bmesh.utils.edge_split(edge,current,(part-previous)/(1.-previous));result[float(t%(2*math.pi))]=nv;current=nv;previous=part
 return result
def main():
 tick=time.time();assert not OUT.exists();save('individual-head-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':'Direct original individual artist-head integration, native head/eyes/mouth/UV retained; reconstruct one common-partition neck connection on same complete body.'});inspection=json.loads((E/'original-artist-head-inspection.json').read_text('utf-8'));M=Matrix(inspection['stageWorldTransform']);bpy.ops.wm.open_mainfile(filepath=str(SRC));b.deliver(0.);protected=a.protected();skin=bpy.data.objects['AFN113_COMPLETE_WOMAN_COHERENT_HEAD'];before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(GLB));new=set(bpy.data.objects)-before;parts=[o for o in new if o.type=='MESH']
 for ob in new:A=ob.matrix_world.copy();ob.parent=None;ob.matrix_world=A;ob.name='AFN126_ORIGINAL_'+ob.name
 for ob in parts:ob.matrix_world=M@ob.matrix_world
 donor=next(o for o in parts if 'Head_Head_' in o.name);body=world_copy(skin,'AFN126_COMPLETE_WOMAN_BODY_AND_ARTIST_HEAD');head=world_copy(donor,'AFN126_NATIVE_ARTIST_HEAD_NECK_CONSTRUCTION');headUV=head.data.uv_layers.active;headUV.name='AngelicaOriginalUV'
 for slot in head.material_slots:
  if not slot.material:continue
  mat=slot.material.copy();slot.material=mat;mat.name='AFN126_NATIVE_ARTIST_HEAD_MATERIAL';uv=mat.node_tree.nodes.new('ShaderNodeUVMap');uv.uv_map='AngelicaOriginalUV'
  for n in list(mat.node_tree.nodes):
   if n.bl_idname=='ShaderNodeUVMap' and n!=uv:n.uv_map='AngelicaOriginalUV'
   if n.bl_idname=='ShaderNodeTexImage' and not n.inputs['Vector'].is_linked:mat.node_tree.links.new(uv.outputs['UV'],n.inputs['Vector'])
   if n.bl_idname=='ShaderNodeTexCoord':
    for link in list(n.outputs['UV'].links):mat.node_tree.links.new(uv.outputs['UV'],link.to_socket)
 z0=1.330;z1=1.355;low=cut(body,z0,False);high=cut(head,z1,True);lv,lt,lc=ring(low,z0);hv,ht,hc=ring(high,z1);angles=np.unique(np.r_[lt,ht]);assert np.diff(np.r_[angles,angles[0]+2*math.pi]).min()>1e-9;lr=split_partition(low,lv,lt,lc,angles);hr=split_partition(high,hv,ht,hc,angles);assert len(lr)==len(hr)==len(angles),(len(lr),len(hr),len(angles));low.to_mesh(body.data);high.to_mesh(head.data);low.free();high.free();bpy.ops.object.select_all(action='DESELECT');body.select_set(True);head.select_set(True);bpy.context.view_layer.objects.active=body;bpy.ops.object.join();bm=bmesh.new();bm.from_mesh(body.data);L,LA,LC=ring(bm,z0);H,HA,HC=ring(bm,z1);assert len(L)==len(H)==len(angles);assert np.max(abs(LA-HA))<3e-5
 # One ruled neck strip between two common-partition planar source contours.
 # Source surface vertices above/below cuts are retained; no facial warp.
 rings=[L]
 for value in [.25,.5,.75]:rings.append([bm.verts.new(u.co.lerp(v.co,value)) for u,v in zip(L,H)])
 rings.append(H);nativeUV=bm.loops.layers.uv.get('MakeHumanOriginalUV');artistUV=bm.loops.layers.uv.get('AngelicaOriginalUV');assert nativeUV and artistUV
 def boundary_uv(v,layer):
  loops=[loop for loop in v.link_loops if loop.face.is_valid];assert loops;return loops[0][layer].uv.copy()
 uv0=[boundary_uv(v,nativeUV) for v in L];uv1=[boundary_uv(v,artistUV) for v in H]
 # Junction-only material blends the two source color maps in their own UVs.
 nativeMat=next(m for m in body.data.materials if m and m.name.startswith('AFN113_COHERENT_NATIVE_HEAD_SKIN'));artistMat=next(m for m in body.data.materials if m and m.name.startswith('AFN126_NATIVE_ARTIST_HEAD_MATERIAL'));oldImage=bpy.data.images.get('young_lightskinned_female_diffuse.png') or next(im for im in bpy.data.images if 'young_lightskinned_female_diffuse' in im.name);artistImages=[n.image for n in artistMat.node_tree.nodes if n.bl_idname=='ShaderNodeTexImage' and n.image];assert artistImages;patch=bpy.data.materials.new('AFN126_ACTUAL_NECK_SOURCE_COLOR_TRANSITION');patch.use_nodes=True;N=patch.node_tree.nodes;links=patch.node_tree.links;p=next(n for n in N if n.bl_idname=='ShaderNodeBsdfPrincipled');p.inputs['Roughness'].default_value=.45;p.inputs['Subsurface Weight'].default_value=.12;p.inputs['Subsurface Scale'].default_value=.001;tex=[]
 for image,uvname in [(oldImage,'MakeHumanOriginalUV'),(artistImages[0],'AngelicaOriginalUV')]:
  n=N.new('ShaderNodeTexImage');n.image=image;u=N.new('ShaderNodeUVMap');u.uv_map=uvname;links.new(u.outputs['UV'],n.inputs['Vector']);tex.append(n.outputs['Color'])
 attr=N.new('ShaderNodeAttribute');attr.attribute_name='AFN126_NECK_BLEND';mix=N.new('ShaderNodeMixRGB');links.new(attr.outputs['Fac'],mix.inputs[0]);links.new(tex[0],mix.inputs[1]);links.new(tex[1],mix.inputs[2]);links.new(mix.outputs['Color'],p.inputs['Base Color']);body.data.materials.append(patch);patchIndex=len(body.data.materials)-1;blend=bm.verts.layers.float.new('AFN126_NECK_BLEND');newFaces=[]
 for j,row in enumerate(rings):
  for v in row:v[blend]=j/4.
 for j in range(4):
  for i in range(len(angles)):
   k=(i+1)%len(angles);face=bm.faces.new([rings[j][i],rings[j][k],rings[j+1][k],rings[j+1][i]]);face.material_index=patchIndex;face.smooth=True;newFaces.append(face)
   for loop,index in zip(face.loops,[i,k,k,i]):loop[nativeUV].uv=uv0[index];loop[artistUV].uv=uv1[index]
 bmesh.ops.recalc_face_normals(bm,faces=newFaces);assert all(len(bm.edges.get((row[i],row[(i+1)%len(row)])).link_faces)==2 for row in [L,H] for i in range(len(row)));bridgePoints=np.array([v.co[:] for row in rings for v in row]);bm.to_mesh(body.data);bm.free();body.data.update();body['sourceCredit']='Angelica / DarkNik (original NikZava284), CC-BY4.0, source URL/provenance/license retained; same native MakeHuman CC0 body below1.33m. Original artwork not exclusively owned.';body['scope']='One complete static development woman. Original artist head/UV/eyes/mouth/hair retained with uniform staging. Explicit shared-partition planar neck construction. No pose transfer/rig/blink/natural hair/finite contacts/runtime qualification.'
 for ob in before:
  if ob.type in ['MESH','CURVES','CURVE','SURFACE']:ob.hide_render=True
 for ob in new:
  if ob.type=='MESH':ob.hide_render=(ob==donor)
 body.hide_render=False;body.hide_set(False);donor.hide_render=True;donor.hide_set(True);bpy.context.view_layer.update();_,W,T=b.u.b.geom(body);assert np.isfinite(W).all();np.savez_compressed(E/'individual-head-neck-lineage.npz',sharedAngles=angles,bodyPlaneOriginalAngles=lt,headPlaneOriginalAngles=ht,bodyPlaneCenter=lc,headPlaneCenter=hc,bridgePoints=bridgePoints,stageWorldTransform=np.array(M));bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=False)
 save('a-build-summary.json',{'source':str(SRC),'sourceSha256':a.sha(SRC),'output':str(OUT),'sha256':a.sha(OUT),'bytes':OUT.stat().st_size,'originalArtistSource':str(GLB),'originalArtistSha256':a.sha(GLB),'actualSkinObject':body.name,'beforeProtected':protected,'sourceHeadObject':donor.name,'sourceParts':[o.name for o in parts],'sourceUniformStaging':inspection['stageWorldTransform'],'bodyCutWorldZ':z0,'headCutWorldZ':z1,'originalBodyCutVertices':len(lt),'originalHeadCutVertices':len(ht),'sharedNeckPartitionVertices':len(angles),'neckBridgeQuads':4*len(angles),'matchedActualPlanarContoursStarShapedAndTopologicallyOrdered':True,'allNeckInterfaceEdgesHaveTwoIncidentFaces':True,'wholeSelfAndFiniteContactNotProved':True,'originalHeadShapeAboveCutNotProjectedOrWarped':True,'oldCompleteSourceAndAllOldFibresPreservedHiddenRollback':True,'oldFibreBrowHairNotClaimedAsNewVisibleSource':True,'originalUVImportedMaterialsAndAllSourcePartsRetained':True,'newVisibleFullHeadAndHairStaticSourceHasNoOwnRigOrShapeKeys':True,'noNewCompleteOperationOrRuntimeAcceptance':True,'actualVertices':len(W),'actualTriangles':len(T),'secondsBeforePreview':time.time()-tick})
 rows=[]
 for view in ['face','body-face','profile','oblique','back']:
  rows.append(b.u.v.image('a-individual-artist-head',view));save('a-view-controls.json',rows)
 print('R126_COMPLETE_INDIVIDUAL_HEAD_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
