"""Actual native skin regions in depth, no inferred anatomy labels or character adoption."""
from pathlib import Path
import bpy,numpy as np,json
from mathutils import Vector
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0110-ordered-lid-topology';P=E.parent/'r0107-native-coarse-lid-cage';data=np.load(P/'native-coarse-lid-poses-pinned.npz');V=data['neutralFineWorld'];T=data['fineTriangles'];UV=np.load(E.parent/'r0105-native-head-skin-chart/actual-lip-and-native-chart.npz')['nativeUV-UVMap'];rings=json.loads((E.parent/'r0108-visible-eyelid-rim/visible-rim-causal-diagnostic.json').read_text('utf8'))['nativeQuadRows'];bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def mesh(name,V,T,colors):
 d=bpy.data.meshes.new(name);d.from_pydata(V.tolist(),[],T.tolist());d.update();o=bpy.data.objects.new(name,d);bpy.context.scene.collection.objects.link(o)
 for n,c in colors:
  m=bpy.data.materials.new(n);m.use_nodes=True;m.node_tree.nodes.clear();bs=m.node_tree.nodes.new('ShaderNodeEmission');bs.inputs['Color'].default_value=(*c,1);out=m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(bs.outputs[0],out.inputs['Surface']);d.materials.append(m)
 return o
head=mesh('ACTUAL_NATIVE_HEAD',V,T,[('UV_front_chart',(.7,.6,.4)),('Other_native_chart',(.5,.1,.6)),('Row0_1',(.8,.04,.03)),('Row1_2',(.03,.7,.12)),('Row2_external_faces',(.03,.35,.8))]);front=np.all((UV[:,:,0]>.2)&(UV[:,:,0]<.8)&(UV[:,:,1]>.5),1)
for f in head.data.polygons:f.material_index=0 if front[f.index] else 1
for side in ['L','R']:
 r0,r1,r2=[set(row) for row in rings[side]['nativeRows']]
 for f in head.data.polygons:
  ids=set(f.vertices)
  if len(ids&r0) and len(ids&r1):f.material_index=2
  elif len(ids&r1) and len(ids&r2):f.material_index=3
  elif len(ids&r2):f.material_index=4
source=np.load(E.parent/'r0104-native-artist-ocular-foundation/animation-actual-source-geometry.npz');opt=json.loads((E.parent/'r0100-native-eyelid-assembly/native-eye-topology.json').read_text('utf8'))['eyes'];C=np.mean([r['posteriorSphereFitCentreWorld'] for r in opt.values()],0);scale=np.linalg.norm(np.array(opt['L']['posteriorSphereFitCentreWorld'])-opt['R']['posteriorSphereFitCentreWorld'])/.060
for side in ['L','R']:
 p=(source['GEO-head_animation_realistic.sclera.'+side+'-world']-C)*scale+C;mesh('ACTUAL_SOURCE_OPTIC_'+side,p,source['GEO-head_animation_realistic.sclera.'+side+'-triangles'],[('Optic',(.03,.55,.7))])
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=4;sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.resolution_x=1000;sc.render.resolution_y=500;sc.render.resolution_percentage=100;sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0.;bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=.13;sc.camera=cam
for tag,loc in [('front',(0,-.5,1.463)),('oblique',(.085,-.5,1.47))]:
 cam.location=loc;cam.rotation_euler=(Vector((0,-.115,1.463))-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(E/('diagnostic-native-regions-'+tag+'.png'));bpy.ops.render.render(write_still=True)
print('R110_ACTUAL_NATIVE_REGIONS_RENDERED',flush=True)
