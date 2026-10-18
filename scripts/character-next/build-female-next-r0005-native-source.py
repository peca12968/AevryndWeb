"""Create an adult female source from installed core CC0 assets, with native loops.

MPFB is used only as an offline Blender tool. No MPFB code is copied into Aevrynd.
The baked body is a foundation study, not a complete or promoted character.
"""
import bpy, json, hashlib, math
from pathlib import Path
from collections import Counter,defaultdict
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(r'D:\Download\Aevrynd')
BASELINE=R/'engine/assets/characters/female-next/source/aevrynd-female-next-r0001-baseline.blend'
OUTPUT=BASELINE.parent/'aevrynd-female-next-r0005-native-source.blend'
E=R/'Evidence/character-female-next/r0005-native-source';E.mkdir(parents=True,exist_ok=True)
ADDON=Path(r'C:\Users\USER\AppData\Roaming\Blender Foundation\Blender\5.2\extensions\user_default\mpfb')
# Reuse the review stage while discarding every inherited character object.
bpy.ops.wm.open_mainfile(filepath=str(BASELINE))
scene=bpy.context.scene;scene.frame_set(1)
for o in list(bpy.data.objects):
    if o.type not in {'LIGHT','CAMERA'}:bpy.data.objects.remove(o,do_unlink=True)
bpy.data.orphans_purge(do_recursive=True)
import bl_ext.user_default.mpfb as mpfb
mpfb.MPFB_CONTEXTUAL_INFORMATION={'__package__':str(mpfb.__package__),'__package_short__':str(mpfb.__package__).split('.')[-1],'__file__':str(mpfb.__file__)}
PREFS={'mpfb_shelf_label':'MPFB','mpfb_user_data':'','mpfb_second_root':'','mh_user_data':'','mh_auto_user_data':False}
mpfb.get_preference=lambda name:PREFS.get(name)
from bl_ext.user_default.mpfb.services import HumanService,TargetService
macro=TargetService.get_default_macro_info_dict()
macro.update({'gender':0.,'age':.55,'muscle':.45,'weight':.45,'height':.5,'proportions':.5,'cupsize':.4,'firmness':.45})
macro['race'].update({'african':.2,'asian':.5,'caucasian':.3})
raw=HumanService.create_human(mask_helpers=True,detailed_helpers=True,extra_vertex_groups=True,feet_on_ground=True,scale=.1,macro_detail_dict=macro)
raw.name='AFN_R0005_EditableNativeCC0'
rig=HumanService.add_builtin_rig(raw,'game_engine',import_weights=True)
rig.name='AFN_R0005_Rig';rig.data.name=rig.name
dg=bpy.context.evaluated_depsgraph_get();dg.update()
evaluated=raw.evaluated_get(dg)
mesh=bpy.data.meshes.new_from_object(evaluated,preserve_all_data_layers=True,depsgraph=dg)
mesh.name='AFN_R0005_NativeBodyMesh'
body=bpy.data.objects.new('AFN_R0005_Body',mesh);scene.collection.objects.link(body)
body.matrix_world=raw.matrix_world.copy()
for g in raw.vertex_groups:body.vertex_groups.new(name=g.name)
bone_names={bone.name for bone in rig.data.bones if bone.use_deform}
for g in reversed(list(body.vertex_groups)):
    if g.name not in bone_names:body.vertex_groups.remove(g)
missing=[];normalised=0
for vertex in mesh.vertices:
    memberships=[(g.group,g.weight) for g in vertex.groups]
    total=sum(weight for _,weight in memberships)
    if total<1e-8:missing.append(vertex.index);continue
    if abs(total-1)>1e-6:normalised+=1
    for index,weight in memberships:body.vertex_groups[index].add([vertex.index],weight/total,'REPLACE')
body.parent=rig
arm=body.modifiers.new('AFN_NativeSkinning','ARMATURE');arm.object=rig
sub=body.modifiers.new('AFN_OfflineSubdivision','SUBSURF');sub.levels=2;sub.render_levels=2
material=bpy.data.materials.new('AFN_R0005_Clay');material.use_nodes=True
shader=next(n for n in material.node_tree.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled')
shader.inputs['Base Color'].default_value=(.32,.23,.18,1.);shader.inputs['Roughness'].default_value=.55;shader.inputs['Specular IOR Level'].default_value=.22;shader.inputs['Subsurface Weight'].default_value=.035
mesh.materials.clear();mesh.materials.append(material)
for p in mesh.polygons:p.material_index=0;p.use_smooth=True
root=bpy.data.collections.new('AFN_R0005_SOURCE');scene.collection.children.link(root)
layers={}
for name in ('BODY','EYES','ORAL','HAIR','CLOTHING','RIG','COLLISION','EDITABLE_SOURCE'):
    col=bpy.data.collections.new('AFN5_'+name);root.children.link(col);layers[name]=col
for obj,layer in ((body,'BODY'),(rig,'RIG'),(raw,'EDITABLE_SOURCE')):
    for col in list(obj.users_collection):col.objects.unlink(obj)
    layers[layer].objects.link(obj);obj['aevrynd_layer']=layer;obj['aevrynd_revision']='female-next-r0005'
raw.hide_render=True;raw.hide_viewport=True
raw['aevrynd_role']='offline editable generator source, excluded from exported actor'
body['aevrynd_role']='neutral identity baked; helper geometry removed; native facial topology retained'
body['aevrynd_asset_license']='CC0-1.0 core derivative'
body['aevrynd_release_state']='FOUNDATION_ONLY_NOT_PROMOTED'
# Inspect control-cage topology before independent subdivision/rig tests.
edge_counts=Counter(tuple(sorted((p.vertices[i],p.vertices[(i+1)%len(p.vertices)]))) for p in mesh.polygons for i in range(len(p.vertices)))
adj=defaultdict(list)
for (a,b),count in edge_counts.items():
    if count==1:adj[a].append(b);adj[b].append(a)
remaining=set(adj);boundaries=[]
while remaining:
    stack=[next(iter(remaining))];component=set()
    while stack:
        i=stack.pop()
        if i in component:continue
        component.add(i);stack.extend(adj[i])
    remaining-=component
    boundaries.append({'vertices':len(component),'degreeTwo':all(len(adj[i])==2 for i in component),'boundsM':[[min(mesh.vertices[i].co[a] for i in component),max(mesh.vertices[i].co[a] for i in component)] for a in range(3)]})
mesh.calc_loop_triangles()
height=max(v.co.z for v in mesh.vertices)-min(v.co.z for v in mesh.vertices)
head=(0.,-.02,height*.91)
views={'face-front':((0.,-.82,head[2]+.015),head,100,(1100,1100)),'face-oblique':((.36,-.78,head[2]+.02),head,100,(1100,1100)),'face-profile':((.82,-.03,head[2]+.015),head,100,(1100,1100)),'full-front':((0.,-3.55,height*.5),(0.,0.,height*.5),58,(900,1200)),'full-side':((3.55,0.,height*.5),(0.,0.,height*.5),58,(900,1200)),'full-back':((0.,3.55,height*.5),(0.,0.,height*.5),58,(900,1200))}
renders=[]
for label,(loc,target,lens,size) in views.items():
    cam=scene.camera;cam.location=loc;cam.data.lens=lens;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.resolution_x,scene.render.resolution_y=size;scene.render.resolution_percentage=100;path=E/f'r0005-{label}.png';scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);renders.append(str(path))
scene['aevrynd_revision']='female-next-r0005';scene['aevrynd_release_state']='FOUNDATION_ONLY_NOT_PROMOTED';scene['aevrynd_website_promotion']='forbidden'
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
files=[ADDON/'data/3dobjs/base.obj',ADDON/'data/rigs/standard/rig.game_engine.json',ADDON/'data/rigs/standard/weights.game_engine.json']
report={'revision':'female-next-r0005','status':'NATIVE_SOURCE_FOUNDATION_REVIEW_PENDING','output':str(OUTPUT),'sourceSha256':hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),'usesInheritedCharacterGeometry':False,'reviewStageFrom':str(BASELINE),'origin':'Installed MPFB 2.0.17 core CC0 graphical assets via offline API','sourceAssets':[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files],'macroParameters':macro,'nativeEditableShapeKeys':len(raw.data.shape_keys.key_blocks),'bakedBodyShapeKeys':len(body.data.shape_keys.key_blocks) if body.data.shape_keys else 0,'controlBodyVertices':len(mesh.vertices),'controlBodyTriangles':len(mesh.loop_triangles),'controlBodyQuads':sum(len(p.vertices)==4 for p in mesh.polygons),'controlBodyPolygons':len(mesh.polygons),'heightM':height,'bones':len(rig.data.bones),'deformWeightGroups':len(body.vertex_groups),'normalisedWeightVertices':normalised,'missingDeformWeights':len(missing),'nonFiniteControlVertices':sum(any(not math.isfinite(c) for c in v.co) for v in mesh.vertices),'edgesWithMoreThanTwoFaces':sum(n>2 for n in edge_counts.values()),'boundaryLoops':boundaries,'layerObjectCounts':{k:len(c.objects) for k,c in layers.items()},'missingCharacterSystems':['eyes and corneas','teeth, tongue and oral assets','hair, brows and lashes','skin textures and PBR baking','facial animation keys','clothing and layering','physics and colliders','runtime LODs and importer verification'],'enginePromotionApproved':False,'websitePromotionApproved':False,'characterScore':None,'scoreNote':'Foundation generation is not a realism quality gain. The previous r0001 visual baseline score remains 42.','collisionStatus':'NOT_YET_QUALIFIED','enginePerformance':{'status':'NOT_RUN_FOUNDATION_ONLY','cpuMs':None,'gpuMs':None,'memoryBytes':None},'renders':renders}
(E/'female-next-r0005-native-source.report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('AFN_R0005='+json.dumps({k:report[k] for k in ('output','controlBodyVertices','controlBodyTriangles','controlBodyQuads','heightM','bones','missingDeformWeights','edgesWithMoreThanTwoFaces','boundaryLoops')}),flush=True)
