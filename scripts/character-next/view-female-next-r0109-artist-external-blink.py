"""Actual full artist external head under original action controls; reference only."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,datetime,time
from mathutils import Vector
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0109-complete-native-lid-sheet';SRC=R/'Reference/character/blender-studio-ellie-v1-cc-by4/ellie.blend'
sp=importlib.util.spec_from_file_location('r109artist',Path(__file__).with_name('build-female-next-r0104-native-head-union.py'));u=importlib.util.module_from_spec(sp);sp.loader.exec_module(u);q=u.q;tick=time.time()
with bpy.data.libraries.load(str(SRC),link=False) as (a,b):b.objects=['GEO-ellie_head','RIG-Ellie','GEO-ellie_eye.L','GEO-ellie_eye.R']
for ob in list(bpy.data.objects):
 if ob.name not in bpy.context.scene.objects:bpy.context.scene.collection.objects.link(ob)
bpy.context.view_layer.update();rig=bpy.data.objects['RIG-Ellie'];head=bpy.data.objects['GEO-ellie_head'];eyes=[bpy.data.objects['GEO-ellie_eye.'+s] for s in ['L','R']];centres=[]
for ob in eyes:
 d,V,T=u.b.geom(ob);centres.append((V.min(0)+V.max(0))/2)
C=np.mean(centres,0);native=json.loads((E.parent/'r0100-native-eyelid-assembly/native-eye-topology.json').read_text('utf8'))['eyes'];targets=np.array([native[s]['posteriorSphereFitCentreWorld'] for s in ['L','R']]);D=targets.mean(0);scale=np.linalg.norm(targets[0]-targets[1])/np.linalg.norm(centres[0]-centres[1]);arrays={};records=[]
head.driver_remove('modifiers["Subdivision"].levels');head.modifiers['Subdivision'].levels=2
for label,value in [('neutral',0.),('half',.5),('closed',1.)]:
 for side in ['L','R']:
  for part in ['Upper','Lower']:rig.pose.bones['ACT-Eyelid_'+part+'.'+side].location.y=(-0.04 if part=='Upper' else .02)*value
 rig.update_tag();bpy.context.view_layer.update();d,V,T=u.b.geom(head);V=V.copy();T=T.copy();arrays[label+'World']=(V-C)*scale+D;arrays[label+'Triangles']=T;arrays[label+'PolygonCounts']=q.arr(d.polygons,'loop_total',len(d.polygons),dtype='i4');arrays[label+'LoopVertexIndices']=q.arr(d.loops,'vertex_index',len(d.loops),dtype='i4')
 records.append({'state':label,'originalACTEyelidUpperLowerLocalY':{part:rig.pose.bones['ACT-Eyelid_'+part+'.L'].location.y for part in ['Upper','Lower']},'evaluatedActualHeadVertices':len(V),'triangles':len(T),'actionProps':{k:repr(v) for k,v in rig.pose.bones['action_props'].items() if 'Eyelid' in k}})
for side,ob in zip(['L','R'],eyes):
 d,V,T=u.b.geom(ob);arrays['eye'+side+'World']=(V-C)*scale+D;arrays['eye'+side+'Triangles']=T.copy()
for ob in bpy.data.objects:ob.hide_render=True
def clay(name,verts,tris,color):
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts.tolist(),[],tris.tolist());mesh.update();ob=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(ob);mat=bpy.data.materials.new(name);mat.diffuse_color=(*color,1);mat.use_nodes=True;mat.node_tree.nodes.clear();bs=mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled');out=mat.node_tree.nodes.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(bs.outputs['BSDF'],out.inputs['Surface']);bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=.65;mesh.materials.append(mat)
 for p in mesh.polygons:p.use_smooth=True
 return ob
shown=clay('REFERENCE_ACTUAL_ELLIE_EXTERNAL_HEAD',arrays['neutralWorld'],arrays['neutralTriangles'],(.32,.28,.25))
for side in ['L','R']:clay('REFERENCE_EYE_'+side,arrays['eye'+side+'World'],arrays['eye'+side+'Triangles'],(.12,.14,.15))
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True;scene.cycles.seed=61061;scene.render.threads_mode='FIXED';scene.render.threads=4;scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100;scene.world.color=(.05,.05,.05);bpy.ops.object.camera_add(location=(0,-.9,1.43685055));camera=bpy.context.object;camera.rotation_euler=(Vector((0,0,1.452))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=85;scene.camera=camera
for name,loc,power,size in [('key',(-.4,-.5,1.9),220,1.),('fill',(.6,-.3,1.6),110,1.)]:
 data=bpy.data.lights.new('REF_'+name,'AREA');data.energy=power;data.shape='DISK';data.size=size;ob=bpy.data.objects.new(data.name,data);scene.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector((0,0,1.46))-ob.location).to_track_quat('-Z','Y').to_euler()
for label in ['neutral','closed']:
 shown.data.vertices.foreach_set('co',arrays[label+'World'].astype('f4').ravel());shown.data.update();shown.update_tag();bpy.context.view_layer.update();scene.render.filepath=str(E/('reference-actual-artist-'+label+'.png'));bpy.ops.render.render(write_still=True)
np.savez_compressed(E/'actual-artist-external-blink.npz',**arrays);(E/'actual-artist-external-blink.json').write_text(json.dumps({'source':str(SRC),'sourceObject':'GEO-ellie_head','referenceNotCandidate':True,'rights':'Blender Studio Ellie v1 CC-BY4.0; actual evaluated external geometry/action pose displayed and saved only as attributed reference. No character geometry/delta transferred. Complete source and notice already archived.','controlsDerivedFromSourceDrivers':'Original Upper var/-.08+.5 and Lower var/.04+.5 action drivers: Upper-.04, Lower+.02 select endpoint1 within source limits; inspect actual external surface to verify closure.','records':records,'uniformIPDScale':scale,'stagedMaximumExternalHeadMoveM':float(np.linalg.norm(arrays['closedWorld']-arrays['neutralWorld'],axis=1).max()),'seconds':time.time()-tick},indent=2)+'\n',encoding='utf8',newline='\n');print('R109_ACTUAL_ARTIST_EXTERNAL_BLINK_REFERENCE_DONE',time.time()-tick,flush=True)
