"""Actual native coarse eyelid topology and existing artist expression references."""
from pathlib import Path
import bpy,numpy as np,json
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0107-native-coarse-lid-cage';P=R/'Reference/character/blender-human-base-meshes-v1.4.1/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend'
with bpy.data.libraries.load(str(P),link=False) as (a,b):b.objects=['GEO-head_animation_realistic']
ob=b.objects[0];bpy.context.scene.collection.objects.link(ob);bpy.context.view_layer.update();d=ob.data;raw=np.empty(len(d.vertices)*3,'f4');d.vertices.foreach_get('co',raw);uv=np.empty(len(d.loops)*2,'f4');d.uv_layers['UVMap'].data.foreach_get('uv',uv);ids=np.empty(len(d.loops),'i4');d.loops.foreach_get('vertex_index',ids);starts=np.empty(len(d.polygons),'i4');counts=starts.copy();d.polygons.foreach_get('loop_start',starts);d.polygons.foreach_get('loop_total',counts);np.savez_compressed(E/'native-coarse-source.npz',local=raw.reshape(-1,3),uv=uv.reshape(-1,2),loopVertexIDs=ids,faceStarts=starts,faceCounts=counts)
report={'nativeHead':{'vertices':len(d.vertices),'faces':len(d.polygons),'UV':list(d.uv_layers.keys()),'modifiers':[(m.name,m.type,getattr(m,'levels',None),getattr(m,'total_levels',None)) for m in ob.modifiers]},'existingReferences':{}}
for label,folder,name in [('Ellie','blender-studio-ellie-v1-cc-by4','ellie.blend'),('Rain','blender-studio-rain-v3-cc-by4/Rain v3.3','rain_v3.2.blend')]:
 p=R/'Reference/character'/folder/name
 with bpy.data.libraries.load(str(p),link=False) as (a,b):report['existingReferences'][label]={'source':str(p),'objects':a.objects,'meshes':a.meshes,'shapeKeys':getattr(a,'shape_keys',[])}
(E/'actual-coarse-and-local-references.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');print('R107_NATIVE_COARSE_INSPECTED',report['nativeHead'],flush=True)
