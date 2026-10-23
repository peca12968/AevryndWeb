"""Single read-only inspection of actual current displayed eye construction."""
from pathlib import Path
import bpy,numpy as np,json,datetime,hashlib,importlib.util
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0194-complete-head-foundation'
sp=importlib.util.spec_from_file_location('r194inspect',C/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h
def val(x):
 if isinstance(x,(float,int,str,bool)):return x
 try:return list(x)
 except:return str(x)
def main():
 t=json.loads((E/'before.json').read_text());bpy.ops.wm.open_mainfile(filepath=t['source']);bpy.context.scene.frame_set(1);bpy.context.view_layer.update();out=[]
 for name in a.MOVING:
  ob=bpy.data.objects[name];W,T=a.geometry(ob);raw=h.arr(ob.data.vertices,'co',len(ob.data.vertices),3);rawWorld=raw@np.array(ob.matrix_world)[:3,:3].T+np.array(ob.matrix_world.translation);groups=[]
  for sign in [-1,1]:
   P=W[W[:,0]*sign>0];A=np.column_stack([2*P,np.ones(len(P))]);fit=np.linalg.lstsq(A,np.sum(P*P,axis=1),rcond=None)[0];centre=fit[:3];radius=float(np.sqrt(max(0,fit[3]+centre@centre)));error=np.abs(np.linalg.norm(P-centre,axis=1)-radius);groups.append({'side':sign,'vertices':len(P),'bbox':[P.min(0).tolist(),P.max(0).tolist()],'leastSquaresSphereCentre':centre.tolist(),'leastSquaresSphereRadiusM':radius,'sphereResidualMQuantiles':np.quantile(error,[.5,.9,1]).tolist()})
  mats=[]
  for slot in ob.material_slots:
   mat=slot.material
   if not mat:continue
   mats.append({'name':mat.name,'link':slot.link,'library':mat.library.filepath if mat.library else None,'nodes':[{'name':n.name,'type':n.bl_idname,'inputs':[{'name':s.name,'linked':s.is_linked,'default':val(s.default_value) if hasattr(s,'default_value') else None} for s in n.inputs if s.name in ['Base Color','Metallic','Roughness','IOR','Alpha','Transmission Weight','Specular IOR Level','Specular Tint','Emission Color','Emission Strength','Thin Wall']],'image':n.image.name if n.bl_idname=='ShaderNodeTexImage' and n.image else None} for n in mat.node_tree.nodes] if mat.use_nodes else [],'links':[{'from':l.from_node.name+'.'+l.from_socket.name,'to':l.to_node.name+'.'+l.to_socket.name} for l in mat.node_tree.links] if mat.use_nodes else []})
  vg={v.name:0 for v in ob.vertex_groups}
  for v in ob.data.vertices:
   for g in v.groups:
    if g.weight>1e-6:vg[ob.vertex_groups[g.group].name]+=1
  out.append({'name':name,'vertices':len(W),'triangles':len(T),'rawWorldVsEvaluatedMaxM':float(np.linalg.norm(rawWorld-W,axis=1).max()) if len(rawWorld)==len(W) else None,'shapeKeys':[k.name for k in ob.data.shape_keys.key_blocks] if ob.data.shape_keys else [],'modifiers':[{'name':d.name,'type':d.type,'object':d.object.name if d.type=='ARMATURE' and d.object else None} for d in ob.modifiers],'vertexGroupMembership':vg,'eyeSphereFits':groups,'materials':mats})
 q={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':t['source'],'sourceSHA256':hashlib.file_digest(open(t['source'],'rb'),'sha256').hexdigest(),'objects':out,'sourceNotSavedOrMutated':True,'fitsAreMeasurementsNotAnatomicalOrOpticalAcceptance':True};(E/'actual-current-eye-construction.json').write_bytes((json.dumps(q,ensure_ascii=False,indent=2)+'\n').encode());print('R194_SINGLE_ACTUAL_EYE_CONSTRUCTION_INSPECTION_DONE',json.dumps([{'name':x['name'],'vertices':x['vertices'],'rawWorldVsEvaluatedMaxM':x['rawWorldVsEvaluatedMaxM'],'eyeSphereFits':x['eyeSphereFits'],'materialNames':[y['name'] for y in x['materials']]} for x in out]),flush=True)
if __name__=='__main__':main()
