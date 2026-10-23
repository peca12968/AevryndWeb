"""Single actual source hair material/alpha inspection, no source mutation."""
from pathlib import Path
import bpy,numpy as np,json,datetime,hashlib
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0189-source-alpha-pipeline';t=json.loads((E/'before.json').read_text());bpy.ops.wm.open_mainfile(filepath=t['source']);s=bpy.context.scene;s.frame_set(1);o=bpy.data.objects['AFN126_ORIGINAL_Hair_Hair_0'];o.material_slots[0].link='DATA';mat=o.material_slots[0].material
def value(v):
 if isinstance(v,(int,float,str,bool)):return v
 try:return list(v)
 except:return str(v)
nodes=[];images=[]
for n in mat.node_tree.nodes:
 row={'name':n.name,'type':n.bl_idname,'inputs':[{'name':a.name,'identifier':a.identifier,'linked':a.is_linked,'default':value(a.default_value) if hasattr(a,'default_value') else None} for a in n.inputs]}
 for k in ['operation','blend_type','data_type','clamp_factor','clamp_result','distribution']:
  if hasattr(n,k):row[k]=value(getattr(n,k))
 if n.bl_idname=='ShaderNodeTexImage' and n.image:
  im=n.image;p=np.empty(len(im.pixels),'f4');im.pixels.foreach_get(p);p=p.reshape(-1,im.channels);path=bpy.path.abspath(im.filepath,library=im.library);images.append({'node':n.name,'image':im.name,'size':list(im.size),'channels':im.channels,'alphaMode':im.alpha_mode,'colorSpace':im.colorspace_settings.name,'path':path,'pathExists':Path(path).is_file(),'packed':bool(im.packed_file),'pixelRGBAQuantiles':np.quantile(p,[0,.1,.5,.9,1],axis=0).tolist(),'alphaFractionZero':float((p[:,3]<1e-6).mean()) if im.channels==4 else None,'alphaFractionBelowHalf':float((p[:,3]<.5).mean()) if im.channels==4 else None,'sourceFileSHA256':hashlib.file_digest(open(path,'rb'),'sha256').hexdigest() if Path(path).is_file() else None})
 nodes.append(row)
q={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':t['source'],'sourceSHA256':hashlib.file_digest(open(t['source'],'rb'),'sha256').hexdigest(),'actualHair':o.name,'actualMeshVertices':len(o.data.vertices),'actualUVLayers':[x.name for x in o.data.uv_layers],'actualMaterial':mat.name,'materialSlots':[{'link':x.link,'material':x.material.name if x.material else None} for x in o.material_slots],'surfaceRenderMethod':mat.surface_render_method,'nodes':nodes,'links':[{'fromNode':x.from_node.name,'fromSocket':x.from_socket.name,'fromIdentifier':x.from_socket.identifier,'toNode':x.to_node.name,'toSocket':x.to_socket.name,'toIdentifier':x.to_socket.identifier} for x in mat.node_tree.links],'actualImages':images,'viewLayerOverride':bpy.context.view_layer.material_override.name if bpy.context.view_layer.material_override else None,'sourceUnmodified':hashlib.file_digest(open(t['source'],'rb'),'sha256').hexdigest()==t['sourceSha256'],'noCandidateOrSourceSave':True,'notRenderDepsgraphOrCauseProof':True}
(E/'actual-source-alpha-material.json').write_bytes((json.dumps(q,ensure_ascii=False,indent=2)+'\n').encode());print('R189_SINGLE_ACTUAL_SOURCE_ALPHA_MATERIAL_INSPECTION_DONE',json.dumps({'UTC':q['UTC'],'material':mat.name,'images':images},ensure_ascii=False),flush=True)
