from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,datetime
p=json.loads(Path('F:/AevryndStorage/character-development-paths.json').read_text('utf-8'));A=Path(p['directCharacterArchiveAccess']);E=A/'evidence/character-female-next/r0214-native-display-hair-modal-motion';t=json.loads((E/'before.json').read_text());assert hashlib.file_digest(Path(t['source']).open('rb'),'sha256').hexdigest()==t['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=t['source']);spec=importlib.util.spec_from_file_location('r214base',A/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);a=m.a;h=m.h;ob=bpy.data.objects[a.FIXED[1]];V,T=a.geometry(ob);raw=h.arr(ob.data.vertices,'co',len(ob.data.vertices),3);materials=[]
for slot in ob.material_slots:
 mat=slot.material;nodes=[]
 for node in mat.node_tree.nodes:
  if node.type in ['BSDF_PRINCIPLED','BSDF_HAIR_PRINCIPLED','TEX_IMAGE','OUTPUT_MATERIAL']:
   info={'name':node.name,'type':node.type}
   if node.type=='BSDF_PRINCIPLED':info.update(alpha=node.inputs['Alpha'].default_value,alphaLinks=[l.from_node.name for l in node.inputs['Alpha'].links],baseColorLinks=[l.from_node.name for l in node.inputs['Base Color'].links])
   if node.type=='TEX_IMAGE':info.update(image=node.image.name if node.image else None,file=node.image.filepath if node.image else None)
   nodes.append(info)
 materials.append({'material':mat.name,'link':slot.link,'nodes':nodes})
parent=np.arange(len(V))
def find(i):
 while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
 return i
for tri in T:
 r=find(int(tri[0]))
 for v in tri[1:]:parent[find(int(v))]=r
labels=np.array([find(i) for i in range(len(V))]);_,counts=np.unique(labels,return_counts=True);q={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actualHair':ob.name,'rawVertices':len(raw),'evaluatedVertices':len(V),'actualTriangles':len(T),'rawMeshUVSignature':a.rawsig(ob),'actualWorldBounds':[V.min(0).tolist(),V.max(0).tolist()],'modifiers':[{'name':x.name,'type':x.type} for x in ob.modifiers],'meshIslands':len(counts),'islandVertexCountQuantiles':np.quantile(counts,[0,.5,.9,1]).tolist(),'meshIslandsNotFollicleOrFlowIdentity':True,'materials':materials,'meshMatrixWorld':np.array(ob.matrix_world).tolist(),'rawToEvaluatedWorldMaximumErrorM':float(np.linalg.norm(raw@np.array(ob.matrix_world)[:3,:3].T+np.array(ob.matrix_world.translation)-V,axis=1).max())};(E/'actual-display-mesh-and-material-inspection.json').write_bytes((json.dumps(q,indent=2)+'\n').encode());print('R214_ACTUAL_WORKING_DISPLAY_MESH_MATERIALS_INSPECTED',json.dumps(q),flush=True)
