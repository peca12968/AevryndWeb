"""Actual original source emitter and native Eve system reference; no script execution."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0130-artist-native-groom';D=R/'Reference/character/charmorph-vitruvian-cc0';S=R/'engine/assets/characters/female-next/source'
sp=importlib.util.spec_from_file_location('r130base',Path(__file__).with_name('build-female-next-r0116-native-eye-character.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b;q=a.q;b.u.v.E=E
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda x:x.tolist() if isinstance(x,np.ndarray) else x.item())+'\n',encoding='utf-8')
def hairmat():
 mat=bpy.data.materials.new('AFN130_INDEPENDENT_BROWN_FIBRE');mat.use_nodes=True;n=mat.node_tree.nodes;n.clear();p=n.new('ShaderNodeBsdfHairPrincipled');p.parametrization='COLOR';p.inputs['Color'].default_value=(.055,.027,.014,1);p.inputs['Roughness'].default_value=.32;p.inputs['Radial Roughness'].default_value=.45;o=n.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(p.outputs[0],o.inputs['Surface']);return mat
def main():
 tick=time.time();bpy.ops.wm.open_mainfile(filepath=str(S/'r0126-source/aevrynd-female-next-r0126-b-source-section-neck.blend'));A=bpy.data.objects['AFN113_COMPLETE_WOMAN_COHERENT_HEAD'].matrix_world.copy()
 for o in bpy.context.scene.objects:
  if o.type in ['MESH','CURVE','CURVES']:o.hide_render=True
 with bpy.data.libraries.load(str(D/'hair.blend'),link=False) as (src,dst):dst.objects=['hair-src']
 o=dst.objects[0];bpy.context.scene.collection.objects.link(o);o.matrix_world=A;o.hide_render=False;o.hide_viewport=False;o.hide_set(False);o.show_instancer_for_render=False
 for md in o.modifiers:
  if md.type=='PARTICLE_SYSTEM':md.show_viewport=md.show_render=md.particle_system.name=='Eve'
 ps=o.particle_systems['Eve'];ps.settings=ps.settings.copy();ps.settings.child_percent=ps.settings.rendered_child_count;o.data.materials.clear();o.data.materials.append(hairmat());ps.settings.material=1
 mesh=o.data.copy();body=bpy.data.objects.new('AFN130_ORIGINAL_NATIVE_BODY_REFERENCE',mesh);bpy.context.scene.collection.objects.link(body);body.matrix_world=A;mesh.materials.clear();mat=bpy.data.materials.new('AFN130_REFERENCE_CLAY');mat.diffuse_color=(.3,.3,.3,1);mesh.materials.append(mat)
 for p in mesh.polygons:p.material_index=0;p.use_smooth=True
 sub=body.modifiers.new('ORIGINAL_BODY_REFERENCE_SUBDIV','SUBSURF');sub.levels=sub.render_levels=1;bpy.context.scene.frame_set(1);bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());p=ev.particle_systems['Eve'];save('eve-original-source-reference.json',{'source':str(D/'hair.blend'),'sha256':a.sha(D/'hair.blend'),'license':'CC0 per pinned source config listing hair.blend and Eve','matrix':np.array(A),'parents':len(p.particles),'children':len(p.child_particles),'sourceOwnNativeEmitterAndParticleGroom':True,'referenceOwnNewBrownShaderAndClayBody':True,'notCurrentWomanOrAdoption':True,'originalSourceNotSaved':True,'secondsBeforeViews':time.time()-tick});rows=[]
 for view in ['face','profile']:rows.append(b.u.v.image('source-original-native-Eve',view));save('eve-original-source-view-controls.json',rows)
 print('R130_ORIGINAL_NATIVE_EVE_REFERENCE_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
