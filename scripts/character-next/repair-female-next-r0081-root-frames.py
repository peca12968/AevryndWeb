"""Same curly candidate: use broad actual-skin frame support, retain root anchors.
Fine subdivided triangles amplify float-normal error at free tips. This repair
changes the support frame, not hairstyle, pigment, radius or motion tolerance.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
from mathutils import Vector
from mathutils.kdtree import KDTree
R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0081-editable-curly-groom';OUT=S/'aevrynd-female-next-r0081-b-stable-frame-curly-study.blend'
sp=importlib.util.spec_from_file_location('repair81',Path(__file__).with_name('build-female-next-r0081-editable-curly.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);q=m.q
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):(E/n).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def main():
 tick=time.time();a=q.read(E/'a-build-summary.json');assert not OUT.exists() and sha(Path(a['output']))==a['outputSha256'];bpy.ops.wm.open_mainfile(filepath=a['output']);bpy.context.scene.frame_set(1);bpy.context.view_layer.update();o=bpy.data.objects[a['editableGuideObject']];before=q.hair(o);table=bpy.data.objects[a['liveRootBindingTable']].data;N=len(table.vertices);anchor=q.arr(table.attributes['AFN69_RestAnchor'].data,'vector',N,3);t=q.arr(table.attributes['AFN69_RestTangent'].data,'vector',N,3);b=q.arr(table.attributes['AFN69_RestBinormal'].data,'vector',N,3);body=m.rig.k.mesh(bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING']);kd=KDTree(len(body['V']))
 for i,p in enumerate(body['V']):kd.insert(Vector(p),i)
 kd.balance();F=np.array([[kd.find(Vector(target))[1] for target in (p-.01*tt,p+.01*tt,p+.01*bb)] for p,tt,bb in zip(anchor,t,b)],'i4');tri=body['V'][F];area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1);assert area.min()>1e-6
 for j in range(3):at=table.attributes.new('AFN81_FrameVertex'+str(j),'INT','POINT');at.data.foreach_set('value',F[:,j])
 wrapper=o.modifiers['AFN81_ACTUAL_RENDER_ROOT_TABLE'].node_group;nodes=wrapper.nodes;links=wrapper.links;out=next(n for n in nodes if n.bl_idname=='NodeGroupOutput');geo=out.inputs['Geometry'].links[0].from_socket;info=next(n for n in nodes if n.bl_idname=='GeometryNodeObjectInfo');index=next(n for n in nodes if n.bl_idname=='GeometryNodeInputIndex')
 for j in range(3):
  name='AFN81_FrameVertex'+str(j);attr=nodes.new('GeometryNodeInputNamedAttribute');attr.data_type='INT';attr.inputs['Name'].default_value=name;sample=nodes.new('GeometryNodeSampleIndex');sample.data_type='INT';sample.domain='POINT';sample.clamp=False;links.new(info.outputs['Geometry'],sample.inputs['Geometry']);links.new(attr.outputs['Attribute'],sample.inputs['Value']);links.new(index.outputs['Index'],sample.inputs['Index']);store=nodes.new('GeometryNodeStoreNamedAttribute');store.data_type='INT';store.domain='CURVE';store.inputs['Name'].default_value=name;links.new(geo,store.inputs['Geometry']);links.new(sample.outputs['Value'],store.inputs['Value']);geo=store.outputs['Geometry']
 links.new(geo,out.inputs['Geometry']);ng=o.modifiers['AFN81_LIVE_RENDER_SCALP_FRAME'].node_group;nodes=ng.nodes;links=ng.links;samples=[n for n in nodes if n.bl_idname=='GeometryNodeSampleIndex'];replacements={}
 for sample in samples:
  oldName=sample.inputs['Index'].links[0].from_node.inputs['Name'].default_value;assert oldName.startswith('AFN69_BodyVertex');j=int(oldName[-1]);n=nodes.new('GeometryNodeSampleIndex');n.data_type='FLOAT_VECTOR';n.domain='POINT';n.clamp=False;links.new(sample.inputs['Geometry'].links[0].from_socket,n.inputs['Geometry']);links.new(sample.inputs['Value'].links[0].from_socket,n.inputs['Value']);attr=nodes.new('GeometryNodeInputNamedAttribute');attr.data_type='INT';attr.inputs['Name'].default_value='AFN81_FrameVertex'+str(j);links.new(attr.outputs['Attribute'],n.inputs['Index']);replacements[sample.name]=n.outputs['Value']
 changed=0
 for node in list(nodes):
  if node.bl_idname!='ShaderNodeVectorMath' or node.operation!='SUBTRACT':continue
  inputs=node.inputs[:2]
  if all(socket.is_linked and socket.links[0].from_node.name in replacements for socket in inputs):
   sockets=[replacements[socket.links[0].from_node.name] for socket in inputs]
   for socket,value in zip(inputs,sockets):links.new(value,socket)
   changed+=1
 assert changed==4;ng.name='AFN81_STABLE_ACTUAL_SKIN_PATCH_FRAMES';ng.update_tag();wrapper.update_tag();bpy.context.view_layer.update();after=q.hair(o);error=float(np.linalg.norm(after-before,axis=1).max());assert error<2e-6;o['AFN81_scope']='Same303-guide curly style, material/radii/cap/actual anchors retained. Live rigid frame uses actual skin points spanning about20mm rather than unstable subdivided triangle edges. Root anchor remains original actual-body triangle/barycentric. Fixed density/seed/cap requires rebind after structural edits. Not natural hair motion or complete contact/runtime acceptance.';bpy.context.scene['AFN81_scope']=o['AFN81_scope'];bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);result=dict(a);result.update(source=a['output'],sourceSha256=a['outputSha256'],completeBaselineSource=a['source'],completeBaselineSha256=a['sourceSha256'],output=str(OUT),outputSha256=sha(OUT),outputBytes=OUT.stat().st_size,sameCandidateImplementationRepair=True,stableFrameSupportOffsetsM=[[-.01,0],[.01,0],[0,.01]],minimumDoubleFrameTriangleAreaM2=float(area.min()),rootAnchorIDsAndBarycentricsUnedited=True,neutralGeometryMaximumChangeM=error,secondsBeforePilot=time.time()-tick);save('b-build-summary.json',result);np.savez_compressed(E/'b-stable-frame-lineage.npz',actualBodyFrameVertexIDs=F,minimumDoubleAreaM2=area.min(),neutralWorld=after);rows=[]
 for view in ('face','body-face'):rows.append(m.render('b-curly',view));save('b-pilot-controls.json',rows)
 print('R81_STABLE_FRAME_IMPLEMENTATION_REPAIR',error,float(area.min()),time.time()-tick,flush=True)
if __name__=='__main__':main()
