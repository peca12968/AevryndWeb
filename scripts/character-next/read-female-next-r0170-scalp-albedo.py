"""Read original current-head albedo anchors for anatomical scalp construction."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util
from mathutils import Vector
from mathutils.bvhtree import BVHTree
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');R=Path('D:/Download/Aevrynd');E=C/'evidence/character-female-next/r0170-root-constrained-carrier';sp=importlib.util.spec_from_file_location('r170albedo',C/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;before=json.loads((E/'before.json').read_text());bpy.ops.wm.open_mainfile(filepath=before['source']);skin=bpy.data.objects[a.FIXED[0]];W,T=a.geometry(skin);tree=BVHTree.FromPolygons(W.tolist(),T.tolist(),all_triangles=True);d=skin.data;d.calc_loop_triangles();uv=d.uv_layers['AngelicaOriginalUV'];mat=skin.material_slots[8].material;nodes=mat.node_tree.nodes;bs=next(n for n in nodes if n.bl_idname=='ShaderNodeBsdfPrincipled');links=[{'from':x.from_node.name,'fromType':x.from_node.bl_idname,'fromSocket':x.from_socket.name,'to':x.to_node.name,'toSocket':x.to_socket.name} for x in mat.node_tree.links];images=[n.image for n in nodes if n.bl_idname=='ShaderNodeTexImage' and n.image];points={'capTop':[0,0,1.571],'capBack':[0,.047,1.50],'forehead':[0,-.12,1.52],'cheek':[-.05,-.10,1.44],'ear':[-.075,-.02,1.44]};anchors={}
for label,p in points.items():
 hit,no,fi,dist=tree.find_nearest(Vector(p));bc=m.bary(hit,W[T[fi]]);U=bc@np.array([uv.data[k].uv[:] for k in d.loop_triangles[fi].loops]);anchors[label]={'world':list(hit),'triangle':int(fi),'UV':U.tolist(),'material':d.polygons[d.loop_triangles[fi].polygon_index].material_index,'pixels':{}}
for im in images:
 w,hh=im.size;px=np.empty(len(im.pixels),'f4');im.pixels.foreach_get(px);px=px.reshape(hh,w,4)
 for label,r in anchors.items():u,v=r['UV'];r['pixels'][im.name]=px[min(hh-1,max(0,int(v*hh))),min(w-1,max(0,int(u*w))),:3].tolist()
result={'originalHeadMaterial':mat.name,'links':links,'anchors':anchors,'sourceAppearanceNotChanged':True};(E/'source-albedo-scalp-anchor-read.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print('R170_CURRENT_ALBEDO_ANCHORS_READ',json.dumps(result),flush=True)
