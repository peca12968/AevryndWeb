"""Actual original artist Bob reference before any target selection/transfer.
No source addon executed. Native particle render, authored count and widths.
"""
from pathlib import Path
import bpy, numpy as np, json, hashlib, importlib.util, time
R=Path('D:/Download/Aevrynd'); E=R/'Evidence/character-female-next/r0096-artist-bob-foundation'; S=R/'engine/assets/characters/female-next/source'; D=R/'Reference/character/charmorph-vitruvian-cc0'
sp=importlib.util.spec_from_file_location('r96views',Path(__file__).with_name('render-female-next-r0091-matched.py'));v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v);v.E=E;q=v.m.m.q
def save(n,x): (E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else list(a))+'\n',encoding='utf8')
def main():
 tick=time.time();src=D/'hair.blend';assert hashlib.sha256(src.read_bytes()).hexdigest()=='2abf4b59006148420e0087a98e9e9a13e02e4b0e6cca6ee73c63efbe6e8da811'
 bpy.ops.wm.open_mainfile(filepath=str(S/'aevrynd-female-next-r0094-b-source-width-growth-volume.blend'));s=bpy.context.scene;s.frame_set(1);A=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING'].matrix_world.copy()
 for ob in s.objects:
  if ob.type in ['MESH','CURVES','CURVE']:ob.hide_render=True
 with bpy.data.libraries.load(str(src),link=False) as (a,b):b.objects=['hair-src']
 o=b.objects[0];s.collection.objects.link(o);o.hide_viewport=False;o.hide_render=False;o.hide_set(False);o.matrix_world=A;o.show_instancer_for_render=False
 for md in o.modifiers:
  if md.type=='PARTICLE_SYSTEM':md.show_viewport=md.show_render=md.particle_system.name=='Bob'
 ps=o.particle_systems['Bob'];ps.settings=ps.settings.copy();settings=ps.settings;original={k:getattr(settings,k) for k in ['child_type','child_percent','rendered_child_count','child_radius','child_roundness','clump_factor','clump_shape','use_clump_curve','roughness_1','roughness_2','root_radius','tip_radius','radius_scale','display_step','render_step','use_close_tip','shape']}
 assert original['rendered_child_count']==100 and original['child_type']=='SIMPLE';settings.child_percent=settings.rendered_child_count;o.data.materials.clear();o.data.materials.append(bpy.data.materials['Brown hair']);settings.material=1
 # Explicit neutral clay original canonical body: source shape reference only.
 mesh=o.data.copy();body=bpy.data.objects.new('AFN96_ORIGINAL_CANONICAL_BODY_REFERENCE_ONLY',mesh);s.collection.objects.link(body);body.matrix_world=A;mesh.materials.clear();mat=bpy.data.materials.new('AFN96_SOURCE_REFERENCE_CLAY');mat.diffuse_color=(.38,.38,.38,1);mat.use_nodes=True;bs=mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled');out=mat.node_tree.nodes.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(bs.outputs['BSDF'],out.inputs['Surface']);bs.inputs['Base Color'].default_value=(.38,.38,.38,1);bs.inputs['Roughness'].default_value=.65;mesh.materials.append(mat)
 for p in mesh.polygons:p.use_smooth=True;p.material_index=0
 sub=body.modifiers.new('SOURCE_REFERENCE_SUBDIVISION','SUBSURF');sub.levels=sub.render_levels=2
 bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());ep=ev.particle_systems['Bob'];parent=len(ep.particles);child=len(ep.child_particles);N=2**settings.display_step+1;assert parent==248 and child==24800
 raw=np.empty((parent+child,N,3),'f4')
 for i in range(len(raw)):
  for j in range(N):raw[i,j]=ep.co_hair(ev,particle_no=i,step=j)
 valid=np.linalg.norm(raw,axis=2)>.5;counts=valid.sum(1);assert np.all(counts>=2) and np.array_equal(valid,np.arange(N)[None,:]<counts[:,None]) and np.all(raw[~valid]==0)
 pm=next(md for md in ev.modifiers if md.type=='PARTICLE_SYSTEM' and md.particle_system.name=='Bob');guides=[];gc=[]
 for particle in ep.particles:
  pts=[tuple(k.co_object(ev,pm,particle)) for k in particle.hair_keys];gc.append(len(pts));guides.extend(pts)
 G=np.array(guides,'f4');assert np.isfinite(G).all() and G[:,2].min()>.5
 np.savez_compressed(E/'native-Bob-source-and-children.npz',nativeRawAPI=raw,validCacheCounts=counts.astype('i4'),guideNative=G,guideCounts=np.array(gc,'i4'),parentCount=np.array(parent),childCount=np.array(child))
 save('native-Bob-extraction.json',{'source':str(src),'sourceSha256':hashlib.sha256(src.read_bytes()).hexdigest(),'style':'Bob','parents':parent,'renderChildren':child,'cachedPaths':len(raw),'apiSlotsEach':N,'validCachePointCountRange':[int(counts.min()),int(counts.max())],'validPoints':int(counts.sum()),'originalSettings':original,'allOriginalParentsChildrenGuidesRetained':True,'cacheScope':'Original viewport path samples; exact-zero out-of-range suffix preserved in raw data. Not exact Cycles interpolation.','referenceScope':'Original canonical body in neutral clay and original Bob native particle shape under current stage. Hair material is inherited Brown material; not a target-character improvement.','sourceAddonExecuted':False,'secondsBeforeViews':time.time()-tick})
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(E/'original-canonical-Bob-reference.blend'),compress=True)
 rows=[]
 for view in ['face','profile','back','body-face']:rows.append(v.image('source-canonical-Bob',view));save('source-reference-view-controls.json',rows)
 print('R96_ORIGINAL_BOB_REFERENCE_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
