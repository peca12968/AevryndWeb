"""Actual intended long style: groom_base + native original four systems."""
from pathlib import Path
import bpy,numpy as np,json,time,hashlib,importlib.util
from mathutils import Vector
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0137-complete-studio-groom';SRC=R/'Reference/character/blender-studio-ellie-v1-cc-by4/ellie.blend'
def mod(n,f):sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
tool=mod('r137originaltools','extract-female-next-r0137-complete-studio-groom.py');restore=mod('r137nativerestore','restore-female-next-r0130-native-studio-groom.py')
def save(n,x):tool.save(n,x)
def main():
 tick=time.time();previewOnly=(E/'original-long-source.npz').exists();bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);rig=bpy.data.objects['RIG-Ellie'];props=rig.pose.bones['Properties_Character_Ellie'];props['Hairstyle']=0;props['Particle Hair']=1;props['Quality']=2;rig.update_tag()
 for c in bpy.data.collections:c.hide_viewport=False
 def show(l):
  l.exclude=False;l.hide_viewport=False
  for c in l.children:show(c)
 show(bpy.context.view_layer.layer_collection);bpy.context.view_layer.update();core=bpy.data.objects['GEO-ellie_hair.groom_base'];head=bpy.data.objects['GEO-ellie_head'];scalp=bpy.data.objects['GEO-ellie_hair.scalp'];assert not core.hide_render and not scalp.hide_render
 for md in scalp.modifiers:
  if md.type=='MASK':md.show_viewport=md.show_render=False
 scalp.hide_viewport=False;scalp.hide_set(False);bpy.context.view_layer.update();native=restore.restore(scalp);dg=bpy.context.evaluated_depsgraph_get();ev=scalp.evaluated_get(dg);systems=[];points=[];counts=[];guideKeys=[];guideCounts=[];sourceRadius=[];proxyRecords=[]
 for ps in ev.particle_systems:
  md=next(m for m in ev.modifiers if m.type=='PARTICLE_SYSTEM' and m.particle_system.name==ps.name);proxy=bpy.data.objects[scalp.name+'-'+ps.name];P=tool.arr(proxy.evaluated_get(dg).data.vertices,'co',len(proxy.evaluated_get(dg).data.vertices));gc=np.array([len(p.hair_keys) for p in ps.particles],'i4');guideKeys.append(P[:gc.sum()]);guideCounts.extend(gc.tolist());N=2**(ps.settings.display_step+1)+1;raw=np.array([[ps.co_hair(ev,particle_no=i,step=k)[:] for k in range(N)] for i in range(len(ps.particles)+len(ps.child_particles))],'f4');n=np.any(raw!=0,axis=2).sum(1);valid=np.arange(N)[None,:]<n[:,None];assert np.all(n>=2) and np.all(raw[~valid]==0);points.append(raw[valid]);counts.extend(n.tolist());sourceRadius.extend([ps.settings.radius_scale*ps.settings.root_radius]*len(n));systems.append({'name':ps.name,'parents':len(ps.particles),'children':len(ps.child_particles),'countsRange':[int(n.min()),int(n.max())],'nativeRootRadius':ps.settings.root_radius,'nativeTipRadius':ps.settings.tip_radius,'nativeRadiusScale':ps.settings.radius_scale,'rawNativeSettingsNotPhysicalRadiusCalibration':True});proxyRecords.append({'name':proxy.name,'points':len(P)})
 W,F=tool.geom(core);H,HT=tool.geom(head);guides=np.concatenate(guideKeys);counts=np.array(counts,'i4');G=np.array(guideCounts,'i4');P=np.concatenate(points)
 if previewOnly:
  original=np.load(E/'original-long-source.npz');assert np.array_equal(original['coreWorld'],W) and np.array_equal(original['fibreLocal'],P) and np.array_equal(original['fibreCounts'],counts)
 else:np.savez_compressed(E/'original-long-source.npz',coreWorld=W,coreTriangles=F,headWorld=H,headTriangles=HT,fibreLocal=P,fibreCounts=counts,guideKeys=guides,guideCounts=G,systemGuideCounts=np.array([r['parents'] for r in systems],'i4'))
 # Verify actual native displayed main core edit and restoration, not hidden rig.
 old=tool.arr(core.data.vertices,'co',len(core.data.vertices));j=int(np.argmax(old[:,2]));core.data.vertices[j].co.x+=.001;core.data.update();core.update_tag();bpy.context.view_layer.update();edited,_=tool.geom(core);delta=float(np.linalg.norm(edited-W,axis=1).max());core.data.vertices.foreach_set('co',old.ravel());core.data.update();core.update_tag();bpy.context.view_layer.update();back,_=tool.geom(core);assert delta>1e-6 and np.max(abs(back-W))<2e-6
 if not previewOnly:save('original-long-source-qualification.json',{'UTC':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),'originalSource':str(SRC),'originalSourceSha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'originalStyleControls':{'Hairstyle':0,'Particle Hair':1,'Quality':2},'nativeDriverContract':str(E/'original-native-style-contract.json'),'intendedCompanions':[core.name,scalp.name],'coreVertices':len(W),'coreTriangles':len(F),'coreBounds':[W.min(0),W.max(0)],'headBounds':[H.min(0),H.max(0)],'systems':systems,'actualSourceKeyRestoreAndReadback':native,'sourceProxyRecords':proxyRecords,'actualNativeCoreVertexOperation':{'vertex':j,'requestedLocalM':.001,'actualDisplayedCoreMaxM':delta,'restoredMaxM':float(np.max(abs(back-W)))},'allSourceNativeSystemsParentsChildrenAndValidKnotsRetained':True,'sourceCurves':len(counts),'sourcePoints':len(P),'nativeOriginalRenderWidthsNotReplacedForReference':True,'noEmbeddedSourceScriptExecuted':True,'shortMeshIsAlternativeNotIntendedCompanionCorrection':True,'secondsBeforePreview':time.time()-tick})
 # Render actual original native systems at original settings, plus intended core.
 for o in s.objects:
  if o.type in ['MESH','CURVE','CURVES','LIGHT']:o.hide_render=True
 core.hide_render=False;scalp.hide_render=False;head.hide_render=False;scalp.show_instancer_for_render=False
 def material(name,color=None):
  m=bpy.data.materials.new(name);m.use_nodes=True;m.node_tree.nodes.clear();n=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled' if color else 'ShaderNodeBsdfHairPrincipled')
  if color:n.inputs['Base Color'].default_value=color;n.inputs['Roughness'].default_value=.35
  else:n.parametrization='MELANIN';n.inputs['Melanin'].default_value=.7;n.inputs['Melanin Redness'].default_value=.4;n.inputs['Roughness'].default_value=.3;n.inputs['Radial Roughness'].default_value=.3
  o=m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(n.outputs[0],o.inputs['Surface']);return m
 for ob,mat in [(core,material('AFN137_OWN_ORIGINAL_CORE',(.025,.012,.007,1))),(head,material('AFN137_OWN_CLAY',(.25,.25,.25,1))),(scalp,material('AFN137_OWN_NATIVE_HAIR'))]:
  ob.data.materials.clear();ob.data.materials.append(mat)
  for poly in ob.data.polygons:poly.material_index=0
 for ps in scalp.particle_systems:ps.settings.material=1
 s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.use_denoising=True;s.render.threads_mode='FIXED';s.render.threads=4;s.render.resolution_x=s.render.resolution_y=640;s.render.resolution_percentage=100;s.render.image_settings.media_type='IMAGE';s.render.image_settings.file_format='PNG';s.render.hair_type='CYLINDER';s.render.hair_subdiv=3;s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=-.5;world=bpy.data.worlds.new('AFN137_SOURCE_WORLD');world.use_nodes=True;world.node_tree.nodes.clear();bg=world.node_tree.nodes.new('ShaderNodeBackground');bg.inputs['Color'].default_value=(0,0,0,1);wo=world.node_tree.nodes.new('ShaderNodeOutputWorld');world.node_tree.links.new(bg.outputs[0],wo.inputs['Surface']);s.world=world;center=(H.min(0)+H.max(0))*.5;span=np.ptp(H[:,2]);aim=center+np.array([0,0,.05*span]);distance=span*3.;cd=bpy.data.cameras.new('AFN137_SOURCE_CAMERA');cam=bpy.data.objects.new(cd.name,cd);s.collection.objects.link(cam);s.camera=cam;cd.lens=60
 for name,off,power,size in [('KEY',[-1.2,-1.5,1.8],600,1.3),('FILL',[1.4,-1.1,.8],300,1.8),('RIM',[.5,1.2,1.5],500,1.0)]:
  ld=bpy.data.lights.new('AFN137_SOURCE_'+name,'AREA');ld.energy=power*span*span;ld.shape='DISK';ld.size=size*span;lo=bpy.data.objects.new(ld.name,ld);s.collection.objects.link(lo);lo.location=Vector(aim+np.array(off)*span);lo.rotation_euler=(Vector(aim)-lo.location).to_track_quat('-Z','Y').to_euler()
 for name,off in [('face',[0,-distance,.1*span]),('profile',[-distance,0,.1*span])]:cam.location=Vector(aim+np.array(off));cam.rotation_euler=(Vector(aim)-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(E/('reference-ORIGINAL-LONG-native-'+name+'.png'));bpy.ops.render.render(write_still=True)
 print('R137_ACTUAL_COMPLETE_ORIGINAL_LONG_STYLE_READY',time.time()-tick,flush=True)
if __name__=='__main__':main()
