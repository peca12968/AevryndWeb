"""Read actual native shape and shader foundation; no model edits."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0125-craniofacial-rest-shape';S=R/'engine/assets/characters/female-next/source'
sp=importlib.util.spec_from_file_location('r125inspect',Path(__file__).with_name('build-female-next-r0116-native-eye-character.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b;q=a.q
bpy.ops.wm.open_mainfile(filepath=str(S/'r0117-source/aevrynd-female-next-r0117-a-native-fibre-brows.blend'));b.deliver(0.);skin=bpy.data.objects['AFN113_COMPLETE_WOMAN_COHERENT_HEAD'];coarse=bpy.data.objects['AFN115_EDITABLE_CONNECTED_NATIVE_ADULT_SOURCE'];A=np.array(coarse.matrix_world);local=q.arr(coarse.data.vertices,'co',len(coarse.data.vertices),3);world=local@A[:3,:3].T+A[:3,3]
nodes=[]
for mat in skin.data.materials:
 if mat and mat.use_nodes:
  for node in mat.node_tree.nodes:
   row={'material':mat.name,'node':node.name,'type':node.bl_idname,'inputs':{}}
   for p in node.inputs:
    if hasattr(p,'default_value'):
     val=p.default_value
     try:val=list(val)
     except TypeError:pass
     if isinstance(val,(str,int,float,bool,list)):row['inputs'][p.name]={'value':val,'linked':p.is_linked}
   nodes.append(row)
ids=np.flatnonzero((world[:,2]>1.36)&(world[:,2]<1.53)&(world[:,1]<-.06));np.savez_compressed(E/'native-face-foundation.npz',coarseWorld=world,coarseLocal=local,matrix=A,selectedIDs=ids)
(E/'foundation-inspection.json').write_text(json.dumps({'coarseVertices':len(local),'selectedPoints':[{'id':int(i),'world':world[i].tolist()} for i in ids],'skinMaterialsAndNodes':nodes,'unitScale':bpy.context.scene.unit_settings.scale_length},indent=2)+'\n',encoding='utf-8',newline='\n');print('R125_NATIVE_FOUNDATION_INSPECTION_DONE',len(ids),flush=True)
