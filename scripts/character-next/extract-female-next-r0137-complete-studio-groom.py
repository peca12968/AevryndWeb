"""Qualify original sculpted cut hair companion and original native fibre cache."""
from pathlib import Path
import bpy,numpy as np,json,time,hashlib,importlib.util
from mathutils import Vector
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0137-complete-studio-groom';OLD=E.parent/'r0130-artist-native-groom';SRC=R/'Reference/character/blender-studio-ellie-v1-cc-by4/ellie.blend'
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.tolist() if isinstance(a,np.ndarray) else a.item())+'\n',encoding='utf-8')
def arr(c,k,n,w=3,dtype='f4'):a=np.empty((n,w),dtype);c.foreach_get(k,a.ravel());return a
def geom(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());d=ev.to_mesh();d.calc_loop_triangles();P=arr(d.vertices,'co',len(d.vertices));A=np.array(ev.matrix_world);W=P@A[:3,:3].T+A[:3,3];F=arr(d.loop_triangles,'vertices',len(d.loop_triangles),3,'i4');ev.to_mesh_clear();return W,F
def main():
 tick=time.time();assert not (E/'complete-original-groom-core.npz').exists();bpy.ops.wm.open_mainfile(filepath=str(SRC));bpy.context.scene.frame_set(1)
 def show(l):
  l.exclude=False;l.hide_viewport=False
  for c in l.children:show(c)
 for coll in bpy.data.collections:coll.hide_viewport=False
 show(bpy.context.view_layer.layer_collection);o=bpy.data.objects['GEO-ellie_hair_cut'];o.hide_set(False);o.hide_viewport=False;head=bpy.data.objects['GEO-ellie_head'];head.hide_set(False);head.hide_viewport=False;bpy.context.view_layer.update();rows=[]
 for ob in [o,head,bpy.data.objects['GEO-ellie_hair.groom_base']]:
  rows.append({'name':ob.name,'hideRender':ob.hide_render,'hideViewport':ob.hide_viewport,'collections':[c.name for c in ob.users_collection],'modifiers':[{'name':m.name,'type':m.type,'showViewport':m.show_viewport,'showRender':m.show_render,'vertexGroup':m.vertex_group if m.type=='MASK' else None,'invert':m.invert_vertex_group if m.type=='MASK' else None} for m in ob.modifiers],'drivers':[(f.data_path,[{'name':v.name,'targets':[{'id':t.id.name if t.id else None,'path':t.data_path} for t in v.targets]} for v in f.driver.variables]) for f in ob.animation_data.drivers] if ob.animation_data else []})
 W,F=geom(o);H,HT=geom(head);assert len(W)>0 and len(F)>0
 # A bounded native source-control operation on the actual complete core.
 arm=next(m.object for m in o.modifiers if m.type=='ARMATURE');names=[p.name for p in arm.pose.bones if 'hair' in p.name.lower()];candidate=next(p for p in arm.pose.bones if p.name.startswith('Hair_Front') and not p.name.startswith('ORG-'));old= candidate.matrix_basis.copy();oldMode=candidate.rotation_mode;candidate.rotation_mode='XYZ';candidate.rotation_euler.x+=.05;bpy.context.view_layer.update();edit,_=geom(o);delta=float(np.linalg.norm(edit-W,axis=1).max());candidate.matrix_basis=old;candidate.rotation_mode=oldMode;bpy.context.view_layer.update();restored,_=geom(o);assert np.max(abs(restored-W))<2e-6
 # Do not promote the failed Hair_Front operation. Verify actual displayed core
 # authoring by its native source mesh vertex, then restore exactly.
 raw=arr(o.data.vertices,'co',len(o.data.vertices));A=np.array(o.matrix_world);rw=raw@A[:3,:3].T+A[:3,3];j=int(np.linalg.norm(rw-W[W[:,2].argmax()],axis=1).argmin());blocks=list(o.data.shape_keys.key_blocks) if o.data.shape_keys else [];originalKeys=[k.data[j].co.copy() for k in blocks];oldPoint=o.data.vertices[j].co.copy();o.data.vertices[j].co.x+=.001
 for k in blocks:k.data[j].co.x+=.001
 if o.data.shape_keys:o.data.shape_keys.update_tag()
 o.data.update();o.update_tag();bpy.context.view_layer.update();edit,_=geom(o);vertexDelta=float(np.linalg.norm(edit-W,axis=1).max());o.data.vertices[j].co=oldPoint
 for k,p in zip(blocks,originalKeys):k.data[j].co=p
 if o.data.shape_keys:o.data.shape_keys.update_tag()
 o.data.update();o.update_tag();bpy.context.view_layer.update();restored,_=geom(o);save('original-core-operation-diagnostic.json',{'bone':candidate.name,'boneDelta':delta,'nativeDisplayedCoreVertexCount':len(W),'nativeHairCutGroups':[g.name for g in o.vertex_groups],'shapeKeyBlocks':len(blocks),'rawVertex':j,'actualDisplayedCoreVertexDelta':vertexDelta,'restoreMaxError':float(np.max(abs(restored-W))),'originalRows':rows});assert vertexDelta>1e-6 and np.max(abs(restored-W))<2e-6
 np.savez_compressed(E/'complete-original-groom-core.npz',coreWorld=W,coreTriangles=F,sourceHeadWorld=H,sourceHeadTriangles=HT)
 save('complete-source-qualification.json',{'UTC':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),'source':str(SRC),'sourceSha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'primaryHairCore':o.name,'nativeParticleCompanion':'GEO-ellie_hair_cut.scalp, front/back/loose','fullOriginalNativeFibreCache':str(OLD/'original-native-studio-cache.npz'),'originalCompanionRoleObserved':rows,'sourceCoreVertices':len(W),'sourceCoreTriangles':len(F),'sourceCoreBounds':[W.min(0),W.max(0)],'sourceHeadBounds':[H.min(0),H.max(0)],'sourceHairBones':names,'actualNativeCoreBoneOperation':{'bone':candidate.name,'radians':.05,'actualCoreMaxSourceM':delta,'restoredMaxSourceM':float(np.max(abs(restored-W))),'boneOperationAccepted':delta>1e-6},'actualNativeCoreVertexOperation':{'vertex':j,'requestedLocalM':.001,'actualDisplayedCoreMaxSourceM':vertexDelta,'restoredMaxSourceM':float(np.max(abs(restored-W)))},'sourceNativeParticleOperationInheritedEvidence':str(OLD/'studio-native-restore-readback.json'),'embeddedSourceCodeExecuted':False,'sourceRigNotEngineRuntimeDependency':True,'sourceOnlyNotCurrentWomanOrAdoptedAppearance':True,'seconds':time.time()-tick})
 # Actual complete source reference: original intended core + every native fibre.
 for ob in bpy.context.scene.objects:
  if ob.type in ['MESH','CURVE','CURVES','LIGHT']:ob.hide_render=True
 s=bpy.context.scene;o.hide_render=False;head.hide_render=False
 def principled(name,color):
  m=bpy.data.materials.new(name);m.use_nodes=True;m.node_tree.nodes.clear();p=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled');p.inputs['Base Color'].default_value=color;p.inputs['Roughness'].default_value=.35;out=m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(p.outputs[0],out.inputs['Surface']);return m
 o.data.materials.clear();o.data.materials.append(principled('AFN137_OWN_REFERENCE_CORE_BROWN',(.025,.012,.007,1)));head.data.materials.clear();head.data.materials.append(principled('AFN137_OWN_REFERENCE_HEAD_CLAY',(.25,.25,.25,1)))
 for ob in [o,head]:
  for p in ob.data.polygons:p.material_index=0
 cache=np.load(OLD/'original-native-studio-cache.npz');P=cache['world'];counts=cache['counts'];d=bpy.data.hair_curves.new('AFN137_ORIGINAL_COMPLETE_HAIR_NATIVE_FIBRES');d.add_curves(counts.tolist());d.position_data.foreach_set('vector',P.astype('f4').ravel());rad=d.attributes.new('radius','FLOAT','POINT');rad.data.foreach_set('value',np.concatenate([.000045*(1-.95*np.linspace(0,1,int(n))**4) for n in counts]).astype('f4'));h=bpy.data.objects.new(d.name,d);s.collection.objects.link(h);mat=bpy.data.materials.new('AFN137_OWN_NATIVE_HAIR');mat.use_nodes=True;mat.node_tree.nodes.clear();ha=mat.node_tree.nodes.new('ShaderNodeBsdfHairPrincipled');ha.parametrization='MELANIN';ha.inputs['Melanin'].default_value=.7;ha.inputs['Melanin Redness'].default_value=.4;ha.inputs['Roughness'].default_value=.3;ha.inputs['Radial Roughness'].default_value=.3;out=mat.node_tree.nodes.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(ha.outputs[0],out.inputs['Surface']);d.materials.append(mat)
 s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.use_denoising=True;s.render.threads_mode='FIXED';s.render.threads=4;s.render.resolution_x=s.render.resolution_y=640;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.hair_type='CYLINDER';s.render.hair_subdiv=3;s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=-.5;world=bpy.data.worlds.new('AFN137_SOURCE_BLACK');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(0,0,0,1);s.world=world;center=(H.min(0)+H.max(0))*.5;span=np.ptp(H[:,2]);aim=center+np.array([0,0,.05*span]);distance=span*3.;cd=bpy.data.cameras.new('AFN137_SOURCE_CAMERA');cam=bpy.data.objects.new(cd.name,cd);s.collection.objects.link(cam);s.camera=cam;cd.lens=60
 for name,off,power,size in [('KEY',[-1.2,-1.5,1.8],600,1.3),('FILL',[1.4,-1.1,.8],300,1.8),('RIM',[.5,1.2,1.5],500,1.0)]:
  ld=bpy.data.lights.new('AFN137_SOURCE_'+name,'AREA');ld.energy=power*span*span;ld.shape='DISK';ld.size=size*span;lo=bpy.data.objects.new(ld.name,ld);s.collection.objects.link(lo);lo.location=Vector(aim+np.array(off)*span);lo.rotation_euler=(Vector(aim)-lo.location).to_track_quat('-Z','Y').to_euler()
 for name,off in [('face',[0,-distance,.1*span]),('profile',[-distance,0,.1*span])]:cam.location=Vector(aim+np.array(off));cam.rotation_euler=(Vector(aim)-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(E/('reference-COMPLETE-original-Ellie-'+name+'.png'));bpy.ops.render.render(write_still=True)
 print('R137_COMPLETE_ORIGINAL_HAIR_CORE_NATIVE_COMPANION_AND_SOURCE_OPERATION_VERIFIED',time.time()-tick,flush=True)
if __name__=='__main__':main()
