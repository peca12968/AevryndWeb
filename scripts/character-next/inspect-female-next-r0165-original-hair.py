"""Single bounded actual source readback, no material or style variants."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,collections
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');R=Path('D:/Download/Aevrynd');E=C/'evidence/character-female-next/r0165-native-hair-construction'
sp=importlib.util.spec_from_file_location('r165source',C/'scripts/character-next/build-female-next-r0158-shared-native-skin.py');h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);a=h.a;h.E=E;b=json.loads((E/'before.json').read_text());assert a.a.sha(Path(b['source']))==b['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=b['source']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();hair=bpy.data.objects[a.FIXED[1]];skin=bpy.data.objects[a.FIXED[0]];disabled=[]
for ob in bpy.data.objects:
 if ob.type=='CURVES' or ob.name.startswith('AFN152_'):
  if not ob.hide_render:disabled.append(ob.name)
  ob.hide_render=True;ob.hide_set(True)
hair.hide_render=False;hair.hide_set(False);bpy.context.view_layer.update();V,T=a.geometry(hair);d=hair.data;parent=np.arange(len(V))
def find(v):
 while parent[v]!=v:parent[v]=parent[parent[v]];v=parent[v]
 return int(v)
for edge in d.edges:
 u,v=map(int,edge.vertices);u=find(u);v=find(v)
 if u!=v:parent[v]=u
ids=np.array([find(i) for i in range(len(V))]);_,component=np.unique(ids,return_inverse=True);sizes=np.bincount(component);uv=h.arr(d.uv_layers.active.data,'uv',len(d.loops),2);loopVertex=h.arr(d.loops,'vertex_index',len(d.loops),dtype='i4');U=np.zeros((len(V),2));weight=np.bincount(loopVertex,minlength=len(V));np.add.at(U,loopVertex,uv);U/=np.maximum(weight[:,None],1);materials=[]
for ma in d.materials:
 if ma is None:materials.append(None);continue
 row={'name':ma.name,'useNodes':ma.use_nodes,'surfaceRenderMethod':getattr(ma,'surface_render_method',None),'nodes':[]}
 if ma.use_nodes:
  for n in ma.node_tree.nodes:
   nd={'name':n.name,'type':n.bl_idname}
   if n.bl_idname=='ShaderNodeTexImage' and n.image:
    im=n.image;nd.update(image=im.name,file=im.filepath,size=list(im.size),channels=im.channels,alphaMode=im.alpha_mode)
   if n.bl_idname in ['ShaderNodeBsdfPrincipled','ShaderNodeBsdfHairPrincipled']:
    nd['inputs']={i.name:{'linked':i.is_linked,'value':str(getattr(i,'default_value',None))} for i in n.inputs if i.name in ['Base Color','Roughness','Alpha','Metallic','Anisotropic IOR Level','Transmission Weight','IOR','Melanin']}
   row['nodes'].append(nd)
  row['links']=[{'from':l.from_node.name+'.'+l.from_socket.name,'to':l.to_node.name+'.'+l.to_socket.name} for l in ma.node_tree.links]
 materials.append(row)
records=[]
for ci in np.argsort(sizes)[::-1][:16]:
 chosen=np.flatnonzero(component==ci);records.append({'component':int(ci),'vertices':len(chosen),'worldMin':V[chosen].min(0).tolist(),'worldMax':V[chosen].max(0).tolist(),'UVMin':U[chosen].min(0).tolist(),'UVMax':U[chosen].max(0).tolist()})
h.save('actual-original-hair-construction-readback.json',{'source':b['source'],'sourceSha256':b['sourceSha256'],'actualHair':hair.name,'actualSkin':skin.name,'actualHairVertices':len(V),'actualHairTriangles':len(T),'nativeConnectedComponents':len(sizes),'componentSizeHistogram':dict(collections.Counter(map(int,sizes))),'largestActualComponents':records,'materials':materials,'disabledOnlyExplicitUnacceptedGroom':disabled,'originalHairActuallyShownForBaseline':True});np.savez_compressed(E/'actual-original-hair-geometry.npz',positions=V,triangles=T,uvPerVertex=U,components=component,loopUV=uv,loopVertex=loopVertex);a.b.u.v.E=E
for view in ['face','body-face','profile','back']:a.b.u.v.image('baseline-original-hair',view)
print('R165_ACTUAL_ORIGINAL_HAIR_READBACK_AND_COMPLETE_BASELINE_DONE',len(V),len(T),len(sizes),flush=True)
