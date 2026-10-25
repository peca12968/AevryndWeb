"""Read actual source birth fields and generator lineage once, not root proxies."""
from pathlib import Path
import bpy,numpy as np,json,datetime,hashlib,importlib.util
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0198-native-birth-owned-scalp';ART=Path('C:/Users/USER/AppData/Local/Temp/Aevrynd-hair-editor-reference/hair.blend');assert hashlib.file_digest(ART.open('rb'),'sha256').hexdigest()=='93aedaef061dc14618a0fcfad33c3df816fa755e8093381cbdfd0fd4c34527f5';sp=importlib.util.spec_from_file_location('r198base',C/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h;bpy.ops.wm.open_mainfile(filepath=str(ART));s=bpy.context.scene;hair=bpy.data.objects['straight_hair_to_shoulder'];body=hair.data.surface;bpy.context.view_layer.update();ev=hair.evaluated_get(bpy.context.evaluated_depsgraph_get());d=ev.data;arrays={};attrs=[]
for prefix,data in [('raw',hair.data),('evaluated',d)]:
 for at in data.attributes:
  row={'name':at.name,'type':at.data_type,'domain':at.domain,'count':len(at.data)}
  if any(x in at.name.lower() for x in ['uv','surface','birth','root','guide','id']):
   if at.data_type in ['FLOAT_VECTOR','FLOAT2']:
    k=3 if at.data_type=='FLOAT_VECTOR' else 2;v=h.arr(at.data,'vector',len(at.data),k);arrays[prefix+'__'+at.name]=v;row.update(min=v.min(0).tolist(),max=v.max(0).tolist(),first3=v[:3].tolist())
   elif at.data_type in ['INT','FLOAT','BOOLEAN']:
    v=h.arr(at.data,'value',len(at.data),dtype='i4' if at.data_type in ['INT','BOOLEAN'] else 'f4');arrays[prefix+'__'+at.name]=v;row.update(min=float(v.min()),max=float(v.max()),unique=int(len(np.unique(v))))
  attrs.append({'stage':prefix,**row})
groups=[];seen=set()
def group(g):
 if g.name in seen:return
 seen.add(g.name);nodes=[]
 for n in g.nodes:
  row={'name':n.name,'type':n.bl_idname}
  if n.bl_idname in ['GeometryNodeInputNamedAttribute','GeometryNodeStoreNamedAttribute']:row['attributeName']=n.inputs['Name'].default_value
  if n.bl_idname=='GeometryNodeObjectInfo':row['object']=n.inputs['Object'].default_value.name if n.inputs['Object'].default_value else None
  if n.bl_idname=='GeometryNodeGroup' and n.node_tree:row['group']=n.node_tree.name;group(n.node_tree)
  if n.bl_idname in ['GeometryNodeInterpolateCurves','GeometryNodeSampleUVSurface','GeometryNodeDistributePointsOnFaces','GeometryNodeSetPosition'] or any(x in n.bl_idname for x in ['CaptureAttribute','SampleIndex']):row['sockets']=[{'name':i.name,'identifier':i.identifier,'linked':i.is_linked} for i in n.inputs]
  nodes.append(row)
 groups.append({'name':g.name,'nodes':nodes,'links':[{'from':[l.from_node.name,l.from_socket.name],'to':[l.to_node.name,l.to_socket.name]} for l in g.links]})
for md in hair.modifiers:
 if md.type=='NODES' and md.node_group:group(md.node_group)
V,T=a.geometry(body);mesh=body.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;mesh.calc_loop_triangles();loops=np.array([t.loops[:] for t in mesh.loop_triangles],'i4');arrays['sourceBodyWorld']=V.astype('f4');arrays['sourceBodyTriangles']=T
for uv in mesh.uv_layers:arrays['bodyUV__'+uv.name]=h.arr(uv.data,'uv',len(uv.data),2)[loops]
np.savez_compressed(E/'native-birth-fields.npz',**arrays)
q={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':str(ART),'sourceSHA256':'93aedaef061dc14618a0fcfad33c3df816fa755e8093381cbdfd0fd4c34527f5','frame':s.frame_current,'hair':hair.name,'surface':body.name,'rawSurfaceUVMap':hair.data.surface_uv_map,'evaluatedSurfaceUVMap':d.surface_uv_map,'rawCurves':len(hair.data.curves),'evaluatedCurves':len(d.curves),'evaluatedPoints':len(d.position_data),'attributes':attrs,'nodeGroups':groups,'bodyUVMaps':[u.name for u in mesh.uv_layers],'sourceUnmodified':True,'noCurrentModelOrCandidateAuthored':True};(E/'native-birth-inspection.json').write_bytes((json.dumps(q,indent=2)+'\n').encode());print('R198_ACTUAL_NATIVE_BIRTH_FIELDS_READ',json.dumps({k:q[k] for k in ['UTC','frame','rawSurfaceUVMap','evaluatedSurfaceUVMap','rawCurves','evaluatedCurves','evaluatedPoints','attributes','bodyUVMaps']}),flush=True)
