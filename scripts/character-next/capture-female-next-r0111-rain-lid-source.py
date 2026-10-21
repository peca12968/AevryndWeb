"""Capture actual Rain external head/paired ocular geometry, no old-mesh pose transfer."""
from pathlib import Path
import bpy,numpy as np,json,time,importlib.util
from mathutils import Vector
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0111-native-mobile-lid-mesh';SRC=R/'Reference/character/blender-studio-rain-v3-cc-by4/Rain v3.3/rain_v3.2.blend'
sp=importlib.util.spec_from_file_location('r111source',Path(__file__).with_name('build-female-next-r0104-native-head-union.py'));u=importlib.util.module_from_spec(sp);sp.loader.exec_module(u);q=u.q;tick=time.time()
with bpy.data.libraries.load(str(SRC),link=False) as (a,b):b.objects=['GEO-rain-head','RIG-rain','GEO-rain-eyes','GEO-rain-eye_cornea']
for ob in list(bpy.data.objects):
 if ob.name not in bpy.context.scene.objects:bpy.context.scene.collection.objects.link(ob)
rig=bpy.data.objects['RIG-rain'];objects={'head':bpy.data.objects['GEO-rain-head'],'eyes':bpy.data.objects['GEO-rain-eyes'],'cornea':bpy.data.objects['GEO-rain-eye_cornea']}
for ob in objects.values():
 md=ob.modifiers.get('Subdivision')
 if md:
  ob.driver_remove('modifiers["Subdivision"].levels');md.levels=1
bpy.context.scene.frame_set(1);bpy.context.view_layer.update();arrays={};records=[]
for label,value in [('neutral',0.),('half',.5),('closed',1.)]:
 for side in ['L','R']:
  rig.pose.bones['ACT-Eyelid_Upper.'+side].location.y=-.04*value;rig.pose.bones['ACT-Eyelid_Lower.'+side].location.y=.02*value
 rig.update_tag();bpy.context.view_layer.update()
 for name,ob in objects.items():
  d,V,T=u.b.geom(ob);arrays[name+'_'+label+'World']=V.copy();arrays[name+'_'+label+'Triangles']=T.copy();arrays[name+'_'+label+'PolygonCounts']=q.arr(d.polygons,'loop_total',len(d.polygons),dtype='i4');arrays[name+'_'+label+'LoopVertexIndices']=q.arr(d.loops,'vertex_index',len(d.loops),dtype='i4')
  if label=='neutral':
   lp=q.arr(d.loop_triangles,'loops',len(T),3,dtype='i4');pf=q.arr(d.loop_triangles,'polygon_index',len(T),dtype='i4');arrays[name+'_neutralTriMaterialIndices']=q.arr(d.polygons,'material_index',len(d.polygons),dtype='i4')[pf]
   for uv in d.uv_layers:arrays[name+'_neutralTriUV_'+uv.name]=q.arr(uv.data,'uv',len(d.loops),2)[lp]
 records.append({'state':label,'ACTUpperY':-.04*value,'ACTLowerY':.02*value,'headVertices':len(arrays['head_'+label+'World']),'headCorrectives':{k.name:k.value for k in objects['head'].data.shape_keys.key_blocks if 'Eyelid' in k.name}})
eyeV=arrays['eyes_neutralWorld'];centres=np.array([(eyeV[eyeV[:,0]*sign>0].min(0)+eyeV[eyeV[:,0]*sign>0].max(0))/2 for sign in [1,-1]]);target=json.loads((E.parent/'r0100-native-eyelid-assembly/native-eye-topology.json').read_text('utf8'))['eyes'];targets=np.array([target[s]['posteriorSphereFitCentreWorld'] for s in ['L','R']]);scale=np.linalg.norm(targets[0]-targets[1])/np.linalg.norm(centres[0]-centres[1]);C=centres.mean(0);D=targets.mean(0)
for key in arrays:
 if key.endswith('World'):arrays[key]=(arrays[key]-C)*scale+D
for ob in bpy.data.objects:ob.hide_render=True
def shown(name,V,T,color):
 m=bpy.data.meshes.new(name);m.from_pydata(V.tolist(),[],T.tolist());m.update();ob=bpy.data.objects.new(name,m);bpy.context.scene.collection.objects.link(ob);mat=bpy.data.materials.new(name);mat.use_nodes=True;mat.node_tree.nodes.clear();bs=mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled');out=mat.node_tree.nodes.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(bs.outputs['BSDF'],out.inputs['Surface']);bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=.6;m.materials.append(mat)
 for p in m.polygons:p.use_smooth=True
 return ob
head=shown('REFERENCE_RAIN_HEAD',arrays['head_neutralWorld'],arrays['head_neutralTriangles'],(.25,.2,.18));eyes=shown('REFERENCE_RAIN_EYES',arrays['eyes_neutralWorld'],arrays['eyes_neutralTriangles'],(.1,.13,.15));sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=8;sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.resolution_x=sc.render.resolution_y=640;sc.render.resolution_percentage=100;sc.world.color=(.05,.05,.05);bpy.ops.object.camera_add(location=(0,-.9,1.43685055));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,1.452))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=85;sc.camera=cam
for name,loc,power in [('key',(-.4,-.5,1.9),100),('fill',(.6,-.3,1.6),50)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.size=1.;ob=bpy.data.objects.new(name,d);bpy.context.scene.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector((0,0,1.46))-ob.location).to_track_quat('-Z','Y').to_euler()
for label in ['neutral','closed']:
 for name,ob in [('head',head),('eyes',eyes)]:ob.data.vertices.foreach_set('co',arrays[name+'_'+label+'World'].astype('f4').ravel());ob.data.update();ob.update_tag()
 bpy.context.view_layer.update();sc.render.filepath=str(E/('reference-actual-rain-'+label+'.png'));bpy.ops.render.render(write_still=True)
np.savez_compressed(E/'actual-rain-ocular-geometry.npz',**arrays);(E/'actual-rain-ocular-geometry.json').write_text(json.dumps({'source':str(SRC),'rights':'Rain Rig (CC) Blender Foundation | studio.blender.org / CC-BY4.0. Original full zip and notices retained in source-inputs/r0090-rain-rig. Actual geometry captured, not a pose field transferred to old native skin.','records':records,'materials':{n:[m.name if m else None for m in o.data.materials] for n,o in objects.items()},'uniformStageScale':scale,'sourceHeadMaximumMoveM':float(np.linalg.norm(arrays['head_closedWorld']-arrays['head_neutralWorld'],axis=1).max()),'referenceNotCompleteAevryndCharacter':True,'seconds':time.time()-tick},indent=2)+'\n',encoding='utf8');print('R111_ACTUAL_RAIN_OCULAR_CAPTURED',time.time()-tick,flush=True)
