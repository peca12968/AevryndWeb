"""One current-woman optical boundary construction, engineering approximation.
Not an import-bug correction, IOR-only variant or measured full eye anatomy.
"""
from pathlib import Path
import bpy,numpy as np,json,datetime,time,hashlib,importlib.util,math
from mathutils import Matrix
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0194-complete-head-foundation';OUT=C/'assets-source/aevrynd-character/female-next/r0194-source/aevrynd-female-next-r0194-a-optical-eye-boundary.blend'
sp=importlib.util.spec_from_file_location('r194base',C/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h
def save(n,x):(E/n).write_bytes((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
def sha(p):return hashlib.file_digest(open(p,'rb'),'sha256').hexdigest()
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def main():
 tick=time.time();t=json.loads((E/'before.json').read_text());assert not OUT.exists() and sha(t['source'])==t['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=t['source']);s=bpy.context.scene;s.frame_set(1);s.camera.data.type='PERSP';bpy.data.objects['AFN126_ORIGINAL_Hair_Hair_0'].material_slots[0].link='DATA'
 for n,hide in [('AFN184_ACTUAL_NATIVE_DEFORMED_LASHES',True),('AFN126_ORIGINAL_Eyelashes_Eyelashes_0',False)]:bpy.data.objects[n].hide_render=hide;bpy.data.objects[n].hide_set(hide)
 bpy.context.view_layer.update();inner=bpy.data.objects['AFN126_ORIGINAL_Eye_Eye_0'];outer=bpy.data.objects['AFN126_ORIGINAL_EyeScleraReflect_EyeScleraReflect_0'];protected={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING if n!=outer.name};capturePath=E/'actual-render-pre-capture-states.json';captures=json.loads(capturePath.read_text()) if capturePath.exists() else []
 def capture(scene):
  # Same deterministic integration settings in both before/after captures.
  scene.cycles.samples=48;scene.cycles.max_bounces=8;scene.cycles.transmission_bounces=8;scene.cycles.transparent_max_bounces=8
  captures.append({'UTC':stamp(),'loadedSource':bpy.data.filepath,'plannedCandidate':str(OUT),'output':scene.render.filepath,'frame':scene.frame_current,'cameraMatrixWorld':[list(x) for x in scene.camera.matrix_world],'lens':scene.camera.data.lens,'cameraType':scene.camera.data.type,'viewTransform':scene.view_settings.view_transform,'look':scene.view_settings.look,'exposure':scene.view_settings.exposure,'resolution':[scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage],'samples':scene.cycles.samples,'maxBounces':scene.cycles.max_bounces,'transmissionBounces':scene.cycles.transmission_bounces,'seed':scene.cycles.seed,'actualOuterEye':outer.name,'actualInnerEye':inner.name,'captureStateNotRenderGeometryDepsgraphProof':True});save('actual-render-pre-capture-states.json',captures)
 bpy.app.handlers.render_pre.append(capture);a.b.u.v.E=E
 for view in ['face','body-face','oblique']:
  completed=E/f'matched-baseline-original-working-eyes-{view}.png'
  if completed.exists():assert any(Path(x['output']).name==completed.name and x['loadedSource']==t['source'] for x in captures)
  else:a.b.u.v.image('baseline-original-working-eyes',view)
 s.frame_set(1);bpy.context.view_layer.update();oldWorld,oldTriangles=a.geometry(outer);raw=h.arr(outer.data.vertices,'co',len(outer.data.vertices),3);rawWorld=raw@np.array(outer.matrix_world)[:3,:3].T+np.array(outer.matrix_world.translation);assert np.linalg.norm(oldWorld-rawWorld,axis=1).max()<3e-6
 vertices=[];faces=[];uvs=[];sideRanges=[];shape=[];nlon=64;nlat=32
 for sign in [-1,1]:
  use=np.flatnonzero(oldWorld[:,0]*sign>0);v=oldWorld[use];lo=v.min(0);hi=v.max(0);centre=(lo+hi)/2;radii=(hi-lo)/2;membership={vg.name:0. for vg in outer.vertex_groups}
  for i in use:
   for g in outer.data.vertices[int(i)].groups:membership[outer.vertex_groups[g.group].name]+=g.weight
  bone=max(membership,key=membership.get);base=len(vertices)
  def point(theta,phi):
   dx=radii[0]*math.sin(theta)*math.cos(phi);dz=radii[2]*math.sin(theta)*math.sin(phi);rho=math.hypot(dx,dz);bulge=.0006*max(0.,1-(rho/.006)**2)**2 if theta<math.pi/2 else 0.;return [centre[0]+dx,centre[1]-radii[1]*math.cos(theta)-bulge,centre[2]+dz]
  vertices.append(point(0,0));uvs.append([.5,0.])
  for ring in range(1,nlat):
   for j in range(nlon):vertices.append(point(math.pi*ring/nlat,2*math.pi*j/nlon));uvs.append([j/nlon,ring/nlat])
  back=len(vertices);vertices.append(point(math.pi,0));uvs.append([.5,1.])
  for j in range(nlon):faces.append((base,base+1+j,base+1+(j+1)%nlon))
  for ring in range(nlat-2):
   row=base+1+ring*nlon;nextrow=row+nlon
   for j in range(nlon):faces.append((row+j,nextrow+j,nextrow+(j+1)%nlon,row+(j+1)%nlon))
  row=base+1+(nlat-2)*nlon
  for j in range(nlon):faces.append((row+j,back,row+(j+1)%nlon))
  sideRanges.append((bone,base,len(vertices)));shape.append({'side':sign,'measuredOriginalBounds':[lo.tolist(),hi.tolist()],'measuredCentre':centre.tolist(),'ellipsoidRadiiM':radii.tolist(),'nativeBone':bone,'localCornealBulgeMaximumM':.0006,'cornealRadialSupportM':.006})
 world=np.array(vertices);inv=np.linalg.inv(np.array(outer.matrix_world));local=world@inv[:3,:3].T+inv[:3,3];mesh=bpy.data.meshes.new('AFN194_MEASURED_EYE_OPTICAL_BOUNDARY_WITH_LOCAL_CORNEA');mesh.from_pydata(local.tolist(),[],faces);mesh.update();uv=mesh.uv_layers.new(name='AFN194_OPTICAL_BOUNDARY_UV')
 for poly in mesh.polygons:
  poly.use_smooth=True
  for li in poly.loop_indices:uv.data[li].uv=uvs[mesh.loops[li].vertex_index]
 outer.data=mesh
 for bone,start,end in sideRanges:
  group=outer.vertex_groups.get(bone) or outer.vertex_groups.new(name=bone);group.add(list(range(start,end)),1.,'REPLACE')
 glass=bpy.data.materials.new('AFN194_CLEAR_OPTICAL_BOUNDARY_IOR138_ENGINEERING');glass.use_nodes=True;ns=glass.node_tree.nodes;ns.clear();bs=ns.new('ShaderNodeBsdfGlass');bs.inputs['Color'].default_value=(1,1,1,1);bs.inputs['Roughness'].default_value=.025;bs.inputs['IOR'].default_value=1.38;out=ns.new('ShaderNodeOutputMaterial');glass.node_tree.links.new(bs.outputs[0],out.inputs['Surface']);mesh.materials.append(glass)
 originalInner=inner.material_slots[0].material;diff=originalInner.copy();diff.name='AFN194_SAME_IRIS_SCLERA_COLOUR_DIFFUSE_UNDER_OPTICAL_BOUNDARY';nodes=diff.node_tree.nodes;links=diff.node_tree.links;oldbs=next(n for n in nodes if n.bl_idname=='ShaderNodeBsdfPrincipled');output=next(n for n in nodes if n.bl_idname=='ShaderNodeOutputMaterial');df=nodes.new('ShaderNodeBsdfDiffuse');df.inputs['Roughness'].default_value=0.
 if oldbs.inputs['Base Color'].is_linked:links.new(oldbs.inputs['Base Color'].links[0].from_socket,df.inputs['Color'])
 else:df.inputs['Color'].default_value=oldbs.inputs['Base Color'].default_value
 for link in list(output.inputs['Surface'].links):links.remove(link)
 links.new(df.outputs[0],output.inputs['Surface']);inner.material_slots[0].link='OBJECT';inner.material_slots[0].material=diff;bpy.context.view_layer.update();OW,OT=a.geometry(outer);assert protected=={n:a.rawsig(bpy.data.objects[n]) for n in protected}
 save('optical-boundary-construction.json',{'UTC':stamp(),'actualOuterEye':outer.name,'actualInnerEye':inner.name,'actualOuterVertices':len(OW),'actualOuterTriangles':len(OT),'geometryConstruction':shape,'actualNativeGazeRig':outer.modifiers[0].object.name,'newOpticalMaterial':glass.name,'newInnerColourMaterial':diff.name,'sourceInnerMaterial':originalInner.name,'innerRawGeometryUVAndSourceColourTextureUnchanged':True,'newOpticalRepresentation':'One transparent dielectric outer optical boundary with local anterior convexity; same source-colour diffuse interior. Combined cornea/fluid approximation, not measured multi-medium human anatomy.','IOR':1.38,'roughness':.025,'fixedOriginalGazeControlsAndActionUnchanged':True,'originalSixOtherRawMeshUVSignatures':protected,'allSkinBodyHairLashWetMouthGeometryAndMaterialsUnchanged':True,'sourceAlpha0OuterNotCalledAnImportBug':True,'newNoShadowVisibilityBypass':True,'secondsBeforeNewCompletePreview':time.time()-tick})
 for view in ['face','body-face','oblique','profile']:s.camera.data.type='PERSP';a.b.u.v.image('a-optical-eye-boundary',view)
 bpy.app.handlers.render_pre.remove(capture);s.frame_set(1);s.camera.matrix_world=Matrix(captures[0]['cameraMatrixWorld']);s.camera.data.lens=captures[0]['lens'];s.camera.data.type=captures[0]['cameraType'];OUT.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);save('a-build-summary.json',{'UTC':stamp(),'output':str(OUT),'sha256':sha(OUT),'bytes':OUT.stat().st_size,'actualOuterEye':outer.name,'actualInnerEye':inner.name,'oneOpticalConstructionOneCandidate':True,'elapsedJobSeconds':time.time()-tick,'appearanceFunctionContactRuntimeUnaccepted':True});print('R194_ONE_COMPLETE_CURRENT_OPTICAL_EYE_BOUNDARY_SAVED',flush=True)
if __name__=='__main__':main()
