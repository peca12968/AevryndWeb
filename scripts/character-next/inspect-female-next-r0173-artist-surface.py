"""Read actual artist volume, effective source shader/UV; no source save/model trial."""
from pathlib import Path
import bpy,numpy as np,json,datetime,importlib.util
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0173-artist-fibre-surface'
sp=importlib.util.spec_from_file_location('r173inspect',C/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h
before=json.loads((E/'before.json').read_text());assert a.a.sha(Path(before['source']))==before['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=before['source']);s=bpy.context.scene;s.frame_set(1);hair=bpy.data.objects[a.FIXED[1]];hair.material_slots[0].link='DATA';hair.hide_render=False;hair.hide_set(False);bpy.context.view_layer.update();W,T=a.geometry(hair);mesh=hair.data;mesh.calc_loop_triangles();UV=h.arr(mesh.uv_layers.active.data,'uv',len(mesh.loops),2);edges=np.asarray([list(e.vertices) for e in mesh.edges]);loops=h.arr(mesh.loops,'vertex_index',len(mesh.loops),dtype='i4');vertexUV=np.zeros((len(mesh.vertices),2),'f4');vertexUV[loops]=UV
graph=[]
for slot in hair.material_slots:
 mat=slot.material;nodes=[]
 for n in mat.node_tree.nodes:
  inputs=[]
  for i in n.inputs:
   if hasattr(i,'default_value'):
    try:v=list(i.default_value)
    except TypeError:v=i.default_value
    if isinstance(v,(str,float,int,list,bool)):inputs.append({'name':i.name,'value':v,'links':[(l.from_node.name,l.from_socket.name) for l in i.links]})
  nodes.append({'name':n.name,'type':n.bl_idname,'inputs':inputs,'image':{'name':n.image.name,'path':bpy.path.abspath(n.image.filepath,library=n.image.library),'size':list(n.image.size),'channels':n.image.channels,'alphaMode':n.image.alpha_mode} if hasattr(n,'image') and n.image else None})
 graph.append({'name':mat.name,'nodes':nodes,'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in mat.node_tree.links]})
np.savez_compressed(E/'actual-artist-mesh-uv-construction.npz',worldVertices=W,triangles=T,edges=edges,loopUV=UV,loopVertex=loops,vertexUV=vertexUV)
d={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':before['source'],'sourceSHA256':before['sourceSha256'],'actualHair':hair.name,'sourceMesh':mesh.name,'sourceLibrary':mesh.library.filepath if mesh.library else None,'vertices':len(mesh.vertices),'triangles':len(T),'edges':len(edges),'polygons':len(mesh.polygons),'UV':mesh.uv_layers.active.name,'bounds':[W.min(0).tolist(),W.max(0).tolist()],'uvBounds':[UV.min(0).tolist(),UV.max(0).tolist()],'materials':graph,'modifiers':[(q.name,q.type,q.show_viewport,q.show_render) for q in hair.modifiers],'unchangedSourceNotSaved':True}
(E/'actual-artist-surface-inspection.json').write_bytes((json.dumps(d,indent=2)+'\n').encode());print(json.dumps(d),flush=True);print('R173_ACTUAL_SOURCE_VOLUME_UV_MATERIAL_INSPECTION_DONE',flush=True)
