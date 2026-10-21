from pathlib import Path
import bpy,json
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0130-artist-native-groom';bpy.ops.wm.open_mainfile(filepath=str(R/'Reference/character/blender-studio-ellie-v1-cc-by4/ellie.blend'))
t=bpy.data.texts.get('rigged_particle_hair.py');assert t;(E/'ellie-original-rigged-particle-hair-readonly.txt').write_text(t.as_string(),encoding='utf-8')
o=bpy.data.objects['GEO-ellie_hair_cut.scalp'];bpy.context.scene.frame_set(1);bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());rows=[]
for p in ev.particle_systems:
 rows.append({'name':p.name,'parents':len(p.particles),'children':len(p.child_particles),'settings':{k:getattr(p.settings,k) for k in ['child_type','child_percent','rendered_child_count','root_radius','tip_radius','radius_scale','display_step','render_step','clump_factor']},'keyProperties':[(k.identifier,k.is_readonly) for k in p.particles[0].hair_keys[0].bl_rna.properties] if len(p.particles) else [],'keyFunctions':[k.identifier for k in p.particles[0].hair_keys[0].bl_rna.functions] if len(p.particles) else []})
(E/'ellie-native-source-api-readback.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8');print('R130_ELLIE_SOURCE_RECIPE_READ_NOT_EXECUTED',flush=True)
