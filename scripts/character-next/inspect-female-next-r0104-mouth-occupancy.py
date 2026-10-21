"""Unsaved actual render-visible mouth rays, not a collision certificate."""
from pathlib import Path
import bpy,json,importlib.util,time
from mathutils import Vector
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0104-native-artist-ocular-foundation';SRC=R/'engine/assets/characters/female-next/source/aevrynd-female-next-r0104-b3-native-head-skin-domain.blend'
tick=time.time();bpy.ops.wm.open_mainfile(filepath=str(SRC));bpy.context.scene.frame_set(1)
for ob in bpy.context.scene.objects:
 if ob.hide_render:ob.hide_set(True)
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();hits=[];counts={}
for ix in range(31):
 x=-.03+.06*ix/30
 for iz in range(31):
  z=1.36+.06*iz/30;answer=bpy.context.scene.ray_cast(dg,Vector((x,-.3,z)),Vector((0,1,0)),distance=.5)
  if answer[0]:
   loc,normal,face,ob=answer[1:5];mat=ob.data.materials[ob.data.polygons[face].material_index].name if ob.type=='MESH' and 0<=face<len(ob.data.polygons) else None;counts[ob.name]=counts.get(ob.name,0)+1
   if abs(x)<.023 and 1.378<z<1.408:hits.append({'x':x,'z':z,'worldY':loc.y,'object':ob.name,'face':face,'material':mat})
(E/'mouth-front-render-object-rays.json').write_text(json.dumps({'source':str(SRC),'renderHiddenObjectsExcludedFromTemporaryViewportRaycast':True,'objectCounts':counts,'frontMouthHits':hits,'sourceFileNotSavedOrModified':True,'scope':'Discrete front-ray object/material diagnostic, not global render occupancy, finite volume or contact proof.','seconds':time.time()-tick},indent=2)+'\n',encoding='utf-8',newline='\n');print('R104_MOUTH_FRONT_OBJECT_COUNTS',counts,flush=True)
