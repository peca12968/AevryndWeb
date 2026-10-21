"""Restore original authored Ellie proxy coordinates into original native hair keys.

Original script is read as evidence only. No source handler/code is executed.
The studio-authored emitter, key counts, child system and settings are retained.
This is an attributed SOURCE REFERENCE, never the current Aevrynd woman.
"""
from pathlib import Path
import bpy,numpy as np,json,datetime,time,hashlib
from mathutils import Vector
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0130-artist-native-groom';S=R/'engine/assets/characters/female-next/source/r0130-source';SRC=R/'Reference/character/blender-studio-ellie-v1-cc-by4/ellie.blend';OUT=S/'artist-original-ellie-restored-native-groom.blend'
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda x:x.tolist() if isinstance(x,np.ndarray) else x.item())+'\n',encoding='utf-8')
def array(c,k,n,w=3):
 a=np.empty((n,w),dtype='f4');c.foreach_get(k,a.ravel());return a
def restore(o):
 dg=bpy.context.evaluated_depsgraph_get();ev=o.evaluated_get(dg);rows=[]
 for ps in o.particle_systems:
  proxy=bpy.data.objects[o.name+'-'+ps.name];pr=proxy.evaluated_get(dg);P=array(pr.data.vertices,'co',len(pr.data.vertices));md=next(m for m in ev.modifiers if m.type=='PARTICLE_SYSTEM' and m.particle_system.name==ps.name);ep=md.particle_system;start=0;original={k:getattr(ps.settings,k) for k in ['child_type','child_percent','rendered_child_count','root_radius','tip_radius','radius_scale','display_step','render_step','clump_factor','clump_shape','child_radius']}
  for i,p in enumerate(ps.particles):
   pe=ep.particles[i];assert len(p.hair_keys)==len(pe.hair_keys)
   for j,k in enumerate(p.hair_keys):k.co_object_set(ev,md,pe,Vector(P[start]));start+=1
  # Read back from the same actual base hair-key data through the native API.
  actual=np.array([k.co_object(ev,md,ep.particles[i])[:] for i,p in enumerate(ps.particles) for k in p.hair_keys]);error=float(np.linalg.norm(actual-P[:start],axis=1).max());assert error<2e-5,(ps.name,error)
  rows.append({'name':ps.name,'proxy':proxy.name,'parents':len(ps.particles),'keyPoints':start,'actualNativeKeyAgainstOriginalProxyMaxSourceUnits':error,'originalSettings':original,'fullProxyVertices':len(P)})
 o.data.update();o.update_tag(refresh={'OBJECT','DATA'});bpy.context.view_layer.update();return rows
def main():
 tick=time.time();assert not OUT.exists();bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1)
 def layers(l):
  l.exclude=False
  for c in l.children:layers(c)
 layers(bpy.context.view_layer.layer_collection)
 for o in s.objects:
  if o.type in ['MESH','CURVE','CURVES','LIGHT']:o.hide_render=True
 scalp=bpy.data.objects['GEO-ellie_hair_cut.scalp'];scalp.hide_render=False;scalp.hide_viewport=False;scalp.hide_set(False);scalp.show_instancer_for_render=False;scalp.show_instancer_for_viewport=False
 for md in scalp.modifiers:
  if md.type=='MASK':md.show_viewport=md.show_render=False
 bpy.context.view_layer.update();rows=restore(scalp)
 # Independent physically based reference shader; do not borrow unversioned Brown hair.
 mat=bpy.data.materials.new('AFN130_OWN_REFERENCE_DARK_BROWN_NATIVE_HAIR');mat.use_nodes=True;n=mat.node_tree.nodes;n.clear();p=n.new('ShaderNodeBsdfHairPrincipled');p.parametrization='MELANIN';p.inputs['Melanin'].default_value=.8;p.inputs['Melanin Redness'].default_value=.12;p.inputs['Roughness'].default_value=.35;p.inputs['Radial Roughness'].default_value=.45;out=n.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(p.outputs[0],out.inputs['Surface']);scalp.data.materials.clear();scalp.data.materials.append(mat)
 for ps in scalp.particle_systems:ps.settings.material=1
 head=bpy.data.objects['GEO-ellie_head'];head.hide_render=False;head.hide_set(False);clay=bpy.data.materials.new('AFN130_STUDIO_SOURCE_REFERENCE_CLAY');clay.use_nodes=True;clay.node_tree.nodes.clear();cp=clay.node_tree.nodes.new('ShaderNodeBsdfPrincipled');cp.inputs['Base Color'].default_value=(.25,.25,.25,1);co=clay.node_tree.nodes.new('ShaderNodeOutputMaterial');clay.node_tree.links.new(cp.outputs['BSDF'],co.inputs['Surface']);head.data.materials.clear();head.data.materials.append(clay)
 for p in head.data.polygons:p.material_index=0
 for md in head.modifiers:
  if md.type=='SUBSURF':md.levels=md.render_levels=1
 bpy.context.view_layer.update();s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.use_denoising=True;s.render.threads_mode='FIXED';s.render.threads=4;s.render.resolution_x=s.render.resolution_y=640;s.render.resolution_percentage=100;s.render.image_settings.media_type='IMAGE';s.render.image_settings.file_format='PNG';s.render.film_transparent=False;s.render.hair_type='STRIP';s.render.hair_subdiv=3;s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=-.5
 s.world=bpy.data.worlds.new('AFN130_SOURCE_REFERENCE_WORLD');s.world.use_nodes=True;s.world.node_tree.nodes.clear();bg=s.world.node_tree.nodes.new('ShaderNodeBackground');bg.inputs[0].default_value=(0,0,0,1);wo=s.world.node_tree.nodes.new('ShaderNodeOutputWorld');s.world.node_tree.links.new(bg.outputs[0],wo.inputs[0])
 d=head.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;P=array(d.vertices,'co',len(d.vertices));A=np.array(head.matrix_world);W=P@A[:3,:3].T+A[:3,3];center=(W.min(0)+W.max(0))*.5;span=float(W[:,2].max()-W[:,2].min());aim=center+np.array([0,0,.05*span]);distance=span*3.0
 camdata=bpy.data.cameras.new('AFN130_SOURCE_REFERENCE_CAMERA');cam=bpy.data.objects.new(camdata.name,camdata);s.collection.objects.link(cam);s.camera=cam;camdata.lens=60
 for name,offset,power,size in [('KEY',[-1.2,-1.5,1.8],600,1.3),('FILL',[1.4,-1.1,.8],300,1.8),('RIM',[.5,1.2,1.5],500,1.0)]:
  ld=bpy.data.lights.new('AFN130_SOURCE_'+name,'AREA');ld.energy=power*span*span;ld.shape='DISK';ld.size=size*span;lo=bpy.data.objects.new(ld.name,ld);s.collection.objects.link(lo);lo.location=Vector(aim+np.array(offset)*span);lo.rotation_euler=(Vector(aim)-lo.location).to_track_quat('-Z','Y').to_euler()
 save('studio-native-restore-readback.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':str(SRC),'sourceSha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'sourceRecipeReadOnly':'ellie-original-rigged-particle-hair-readonly.txt','sourceScriptExecuted':False,'nativeSystems':rows,'sourceHeadWorldBounds':[W.min(0).tolist(),W.max(0).tolist()],'nativeWorldScale':list(scalp.matrix_world.to_scale()),'noNeighbourGuideOrInventedChildReconstruction':True,'referenceOnlyNotCurrentWoman':True,'secondsBeforeSave':time.time()-tick})
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);save('studio-native-reference-source.json',{'source':str(OUT),'sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),'bytes':OUT.stat().st_size,'scope':'Original restored studio source reference only. Not current woman, adoption, natural dynamics or contact/runtime qualification.'})
 for name,offset in [('face',[0,-distance,.1*span]),('profile',[-distance,0,.1*span])]:
  cam.location=Vector(aim+np.array(offset));cam.rotation_euler=(Vector(aim)-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(E/('reference-restored-ellie-native-'+name+'.png'));bpy.ops.render.render(write_still=True)
 print('R130_RESTORED_ORIGINAL_STUDIO_NATIVE_GROOM_REFERENCE_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
