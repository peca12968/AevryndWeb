"""Minimum independent source/UV/material and native displayed mesh edit restoration.
Rejected appearance: no second light, shader variants or claimed natural hair action.
"""
from pathlib import Path
import bpy,numpy as np,json,datetime,time,importlib.util
from mathutils import Vector
from mathutils.bvhtree import BVHTree
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0173-artist-fibre-surface'
sp=importlib.util.spec_from_file_location('r173verify',C/'scripts/character-next/build-female-next-r0173-artist-fibre-surface.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h;timing=json.loads((E/'before.json').read_text());b=json.loads((E/'a-build-summary.json').read_text());tick=time.time();reference=None
def save(n,x):(E/n).write_bytes((json.dumps(x,indent=2)+'\n').encode())
for tag,path,digest in [('input',timing['source'],timing['sourceSha256']),('candidate',b['engineAlias'],b['sha256'])]:
 assert a.a.sha(Path(path))==digest;bpy.ops.wm.open_mainfile(filepath=path);s=bpy.context.scene;s.frame_set(1);hair=bpy.data.objects[b['actualHair']];hair.material_slots[0].link='DATA';bpy.context.view_layer.update();names=a.FIXED+a.MOVING;raw={n:a.rawsig(bpy.data.objects[n]) for n in names if n!=hair.name};mesh=hair.data;sourceUV=h.arr(mesh.uv_layers['UVMap'].data,'uv',len(mesh.loops),2);rawHair={'vertices':a.a.hasharray(h.arr(mesh.vertices,'co',len(mesh.vertices),3)),'loopVertices':a.a.hasharray(h.arr(mesh.loops,'vertex_index',len(mesh.loops),dtype='i4')),'sourceUV':a.a.hasharray(sourceUV)};poses=[]
 for frame in range(1,50):
  s.frame_set(frame);bpy.context.view_layer.update();poses.append({'frame':frame,'worldHashes':{n:[a.a.hasharray(x) for x in a.geometry(bpy.data.objects[n])] for n in names}})
 if tag=='input':reference=raw;hairRef=rawHair;poseRef=poses;continue
 assert raw==reference and rawHair==hairRef and poses==poseRef;s.frame_set(1);bpy.context.view_layer.update();rest,F=a.geometry(hair);skin=bpy.data.objects[b['actualSkin']];W,T=a.geometry(skin);newUV=h.arr(mesh.uv_layers[b['newDirectionUV']].data,'uv',len(mesh.loops),2);assert np.array_equal(newUV,sourceUV[:,[1,0]]) and mesh.uv_layers.active.name=='UVMap'
 mat=hair.material_slots[0].material;assert mat.name==b['actualMaterial'];nodes=mat.node_tree.nodes;bs=next(n for n in nodes if n.bl_idname=='ShaderNodeBsdfPrincipled');tangent=next(n for n in nodes if n.bl_idname=='ShaderNodeTangent');bump=next(n for n in nodes if n.bl_idname=='ShaderNodeBump');image=nodes['AFN173_ACTUAL_ORIGINAL_HAIR_PIGMENT_AND_COVERAGE'];assert image.image.name=='Image_0' and bs.inputs['Base Color'].links[0].from_node==image and bs.inputs['Alpha'].links[0].from_node==image and bs.inputs['Emission Strength'].default_value==0 and tangent.uv_map==b['newDirectionUV'] and bs.inputs['Tangent'].links[0].from_node==tangent and bs.inputs['Normal'].links[0].from_node==bump
 original=mesh.vertices[0].co.copy();mesh.vertices[0].co=original+Vector((.001,0,0));mesh.update();hair.update_tag(refresh={'DATA'});bpy.context.view_layer.update();changed,_=a.geometry(hair);edit=float(np.linalg.norm(changed-rest,axis=1).max());affected=int((np.linalg.norm(changed-rest,axis=1)>3e-6).sum());mesh.vertices[0].co=original;mesh.update();hair.update_tag(refresh={'DATA'});bpy.context.view_layer.update();restored,_=a.geometry(hair);restore=float(np.linalg.norm(restored-rest,axis=1).max());assert restore<3e-6 and affected>0
 tree=BVHTree.FromPolygons(W.tolist(),T.tolist(),all_triangles=True);edges=np.array([list(e.vertices) for e in mesh.edges]);witness=[];inspected=0
 for ei in np.linspace(0,len(edges)-1,1024,dtype=int):
  inspected+=1;u,v=map(int,edges[ei]);p,q=rest[[u,v]];delta=q-p;length=float(np.linalg.norm(delta))
  if length<1e-12:continue
  hit,no,fi,d=tree.ray_cast(Vector(p),Vector(delta/length),length)
  if hit is not None and d>1e-5 and d<length-1e-5:witness.append({'hairEdge':int(ei),'hairVertices':[u,v],'bodyTriangle':int(fi),'worldPoint':list(hit),'interiorDistanceM':float(d),'edgeLengthM':length})
  if len(witness)>=8:break
 save('actual-artist-hair-body-edge-witnesses.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceSHA256':b['sha256'],'originalArtistHairGeometryUnchanged':True,'alphaCoverageChangedFromSourceGlobal0747MultiplierToOriginalImageAlpha':True,'sampledHairMeshEdges':inspected,'rawMeshEdgeBodySurfaceWitnesses':witness,'notExactAlphaWeightedRenderedOccupancyOrGlobalFiniteContactCount':True,'globalSignedMinimumM':None,'finiteSelfContinuousNaturalHairRuntimeUnaccepted':True})
 deps=[]
 for lib in bpy.data.libraries:
  p=Path(bpy.path.abspath(lib.filepath)).resolve();assert p.is_file();deps.append({'kind':'library','file':str(p),'sha256':a.a.sha(p)})
 for im in bpy.data.images:
  if im.source=='FILE' and not im.packed_file and im.filepath:
   p=Path(bpy.path.abspath(im.filepath,library=im.library)).resolve();assert p.is_file();deps.append({'kind':'texture','file':str(p),'sha256':a.a.sha(p)})
 unique={d['sha256'] for d in deps};required=json.loads((E.parent/'r0158-shared-native-skin/workspace-storage-provenance.json').read_text())['dependencyFiles'];assert all(d['sha256'] in unique for d in required) and a.a.sha(Path(b['output']))==b['sha256']
 save('independent-artist-fibre-surface-readback.json',{'source':b['output'],'engineAliasReopened':b['engineAlias'],'sha256':b['sha256'],'protectedSixOtherRawMeshesUVEqual':True,'originalHairRawPositionsTopologyAndOriginalUVEqual':True,'allSevenOriginalEvaluatedMeshesAnd49GazePosesEqual':True,'49OriginalPoseHashes':poses,'addedDirectionUVExactlyOriginalVThenU':True,'originalUVActive':True,'effectiveMaterialName':mat.name,'actualOriginalImage0DrivesBaseColorAndAlpha':True,'actualImage0PackedBytesSHA256':a.a.hasharray(np.frombuffer(bytes(image.image.packed_file.data),dtype='u1')),'effectiveIOR':bs.inputs['IOR'].default_value,'effectiveEmissionStrength':bs.inputs['Emission Strength'].default_value,'effectiveAnisotropy':bs.inputs['Anisotropic'].default_value,'effectiveRoughness':bs.inputs['Roughness'].default_value,'actualNativeFibreTangentUV':tangent.uv_map,'effectiveMicroBumpDistanceM':bump.inputs['Distance'].default_value,'nativeMesh1mmLocalEditMaximumWorldMovementM':edit,'nativeMeshEditAffectedVertices':affected,'nativeMeshEditRestoreM':restore,'onlyScopedSourceEditingNotFullHairMotionOperation':True,'geometryUnchangedDoesNotProveRenderedAlphaContactOrMicrofibreOccupancy':True,'dependencies':deps,'uniqueDependencyFileHashCount':len(unique),'seconds':time.time()-tick})
print('R173_INDEPENDENT_ACTUAL_SURFACE_GRAPH_UV_PROTECTION_MESH_EDIT_RESTORE_DONE',time.time()-tick,flush=True)
