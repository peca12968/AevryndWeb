"""Inspect one original native Back1 artist groom before adaptation or adoption."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
R=Path('D:/Download/Aevrynd');E=Path('C:/Users/USER/AevryndCharacterEvidence/r0122');E.mkdir(parents=True,exist_ok=True);S=R/'engine/assets/characters/female-next/source';D=R/'Reference/character/charmorph-vitruvian-cc0'
sp=importlib.util.spec_from_file_location('r122ref',Path(__file__).with_name('build-female-next-r0116-native-eye-character.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b;q=a.q;b.u.v.E=E
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda x:x.tolist() if isinstance(x,np.ndarray) else x.item())+'\n',encoding='utf-8')
tick=time.time();bpy.ops.wm.open_mainfile(filepath=str(S/'r0117-source/aevrynd-female-next-r0117-a-native-fibre-brows.blend'));skin=bpy.data.objects['AFN113_COMPLETE_WOMAN_COHERENT_HEAD'];A=skin.matrix_world.copy()
for o in list(bpy.context.scene.objects):
 if o.type in ['MESH','CURVE','CURVES']:o.hide_render=True
with bpy.data.libraries.load(str(D/'hair.blend'),link=False) as (aa,bb):bb.objects=['hair-src']
o=bb.objects[0];bpy.context.scene.collection.objects.link(o);o.hide_render=False;o.hide_viewport=False;o.hide_set(False);o.matrix_world=A;o.show_instancer_for_render=False;o.show_instancer_for_viewport=False
inventory={p.name:{k:getattr(p.settings,k) for k in ['count','child_type','rendered_child_count','display_step','render_step','root_radius','tip_radius','radius_scale']} for p in o.particle_systems};save('source-style-inventory.json',inventory)
for md in o.modifiers:
 if md.type=='PARTICLE_SYSTEM':md.show_viewport=md.show_render=md.particle_system.name=='Back1'
ps=o.particle_systems['Back1'];ps.settings=ps.settings.copy();settings=ps.settings;original={k:getattr(settings,k) for k in ['child_type','child_percent','rendered_child_count','child_radius','child_roundness','clump_factor','clump_shape','use_clump_curve','roughness_1','roughness_2','root_radius','tip_radius','radius_scale','display_step','render_step','use_close_tip','shape']};settings.child_percent=settings.rendered_child_count;o.data.materials.clear();o.data.materials.append(bpy.data.materials['Brown hair']);settings.material=1
mesh=o.data.copy();body=bpy.data.objects.new('AFN122_ORIGINAL_CANONICAL_SOURCE_BODY_REFERENCE',mesh);bpy.context.scene.collection.objects.link(body);body.matrix_world=A;mesh.materials.clear();mat=bpy.data.materials.new('AFN122_SOURCE_REFERENCE_CLAY');mat.use_nodes=True;nodes=mat.node_tree.nodes;nodes.clear();p=nodes.new('ShaderNodeBsdfPrincipled');p.inputs['Base Color'].default_value=(.3,.3,.3,1);p.inputs['Roughness'].default_value=.6;out=nodes.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(p.outputs['BSDF'],out.inputs['Surface']);mesh.materials.append(mat)
for poly in mesh.polygons:poly.material_index=0;poly.use_smooth=True
sub=body.modifiers.new('SOURCE_REFERENCE_SUBDIVISION','SUBSURF');sub.levels=sub.render_levels=2;bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
save('source-reference.json',{'source':str(D/'hair.blend'),'sha256':hashlib.sha256((D/'hair.blend').read_bytes()).hexdigest(),'style':'Back1','originalSettings':original,'matrix':np.array(A),'scope':'Original complete canonical source body and original particle hairstyle, same existing hair material/stage. Reference only, not new target woman or accepted gain. No addon or source scripts executed.','sourceRights':'Pinned config CC0; detailed original authors/source preserved. Brown material inherited separately with its own original obligations.','secondsBeforeViews':time.time()-tick})
views=[]
for v in ['face','profile','back','body-face']:
 views.append(b.u.v.image('source-original-Back1',v));save('source-reference-view-controls.json',views)
print('R122_ORIGINAL_BACK1_REFERENCE_PREVIEW_DONE',time.time()-tick,flush=True)
