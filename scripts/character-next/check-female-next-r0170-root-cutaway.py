"""One actual native-root/carrier/Skin domain view, not a character candidate."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,datetime
from mathutils import Vector
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');R=Path('D:/Download/Aevrynd');E=C/'evidence/character-female-next/r0170-root-constrained-carrier';sp=importlib.util.spec_from_file_location('r170anatomy',C/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;b=json.loads((E/'before.json').read_text());assert a.a.sha(Path(b['source']))==b['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=b['source']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[a.FIXED[0]];W,T=a.geometry(skin);line=np.load(E.parent/'r0169-native-carrier-groom/coherent-native-carrier-lineage.npz');hair=bpy.data.objects['AFN169_ACTUAL_COHERENT_NATIVE_ARTIST_GROOM'];carrier=bpy.data.objects['AFN169_POSE_CONSISTENT_CURRENT_SCALP_CARRIER'];P,offset=m.curveworld(hair);CV,CT=a.geometry(carrier);gid=49;root=P[offset[gid]];owner=line['sourceGuideCarrierTriangles'][gid];bc=line['sourceGuideCarrierBarycentric'][gid];tri=317573;raw=skin.data;raw.calc_loop_triangles();uv=raw.uv_layers['AngelicaOriginalUV'];failedUV=[list(uv.data[k].uv) for k in raw.loop_triangles[tri].loops]
hair.hide_render=True;bpy.data.objects[a.FIXED[1]].hide_render=True
def material(name,color):
 ma=bpy.data.materials.new(name);ma.diffuse_color=(*color,1);ma.use_nodes=True;nd=next(x for x in ma.node_tree.nodes if x.bl_idname=='ShaderNodeBsdfPrincipled');nd.inputs['Base Color'].default_value=(*color,1);nd.inputs['Roughness'].default_value=.7;return ma
red=material('AFN170_DIAGNOSTIC_ROOT_RED',(1,.02,.02));blue=material('AFN170_DIAGNOSTIC_SKIN_BLUE',(.01,.2,1))
bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=.0008,location=root);bpy.context.object.data.materials.append(red)
mesh=bpy.data.meshes.new('AFN170_DIAGNOSTIC_CURRENT_CARRIER_TRIANGLE');mesh.from_pydata(CV[owner].tolist(),[],[(0,1,2)]);ob=bpy.data.objects.new(mesh.name,mesh);s.collection.objects.link(ob);ob.data.materials.append(red);wire=ob.modifiers.new('Diagnostic edges','WIREFRAME');wire.thickness=.00035
mesh=bpy.data.meshes.new('AFN170_DIAGNOSTIC_REAL_SKIN_TRIANGLE');mesh.from_pydata((W[T[tri]]+np.array([-.00015,0,0])).tolist(),[],[(0,1,2)]);ob=bpy.data.objects.new(mesh.name,mesh);s.collection.objects.link(ob);ob.data.materials.append(blue)

trans=bpy.data.materials.new('AFN170_DIAGNOSTIC_TRANSLUCENT_SKIN');trans.use_nodes=True;ns=trans.node_tree.nodes;ns.clear();out=ns.new('ShaderNodeOutputMaterial');tr=ns.new('ShaderNodeBsdfTransparent');di=ns.new('ShaderNodeBsdfDiffuse');di.inputs['Color'].default_value=(.5,.5,.5,1);mix=ns.new('ShaderNodeMixShader');mix.inputs[0].default_value=.12;trans.node_tree.links.new(tr.outputs[0],mix.inputs[1]);trans.node_tree.links.new(di.outputs[0],mix.inputs[2]);trans.node_tree.links.new(mix.outputs[0],out.inputs[0])
materials=[]
for i,slot in enumerate(skin.material_slots):
 ma=slot.material
 if ma and ma.use_nodes:materials.append({'slot':i,'name':ma.name,'images':[{'node':n.name,'image':n.image.name,'size':list(n.image.size),'filepath':n.image.filepath} for n in ma.node_tree.nodes if n.bl_idname=='ShaderNodeTexImage' and n.image]})
 slot.link='OBJECT';slot.material=trans
a.b.u.v.m.rig.shade.settings();a.b.u.v.m.rig.k.b.camera('profile');s.camera.location.x=-abs(s.camera.location.x);s.camera.rotation_euler=(Vector((0,-.025,1.465))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=85;s.render.resolution_x=s.render.resolution_y=640;s.cycles.samples=16;s.render.filepath=str(E/'diagnostic-left-root49-transparent-cutaway.png');bpy.context.view_layer.update();bpy.ops.render.render(write_still=True)
(E/'single-controlled-cutaway-and-source-materials.json').write_bytes((json.dumps({'actualRootWorld':root.tolist(),'actualSkinTriangle':tri,'diagnosticTransparencyOnlyNoSourceSaveOrAcceptance':True,'materials':materials,'file':s.render.filepath},indent=2)+'\n').encode());print('R170_SINGLE_CUTAWAY_SOURCE_MATERIAL_READ_DONE',flush=True)
