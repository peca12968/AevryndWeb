"""Inspect the saved brow shader/coverage, with reversible material diagnostics."""
import bpy,json,hashlib,importlib.util,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0018-brow-readability';E.mkdir(parents=True,exist_ok=True)
SRC=S/'aevrynd-female-next-r0017-c-volume-locks-study.blend'
spec=importlib.util.spec_from_file_location('base',Path(__file__).with_name('build-female-next-r0016-feathered-tips.py'));base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,data): (E/name).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def main():
    proof=json.loads((R/'Evidence/character-female-next/r0017-volume-locks/c-exact-crown-transition/saved-build-verification.json').read_text());assert proof['outputSha256']==sha(SRC)
    save('iteration-contract.json',{'previousGoalTurnClassification':'progress: bounded r0017 free-lock geometry retained after five static pose and controlled multi-view evidence; crown and hair remain research quality.','source':str(SRC),'sourceSha256':sha(SRC),'stage':'B_COMPLETE_HEAD_IN_PROGRESS','primaryDefect':'Brows are barely readable and look pale despite the intended dark-brown fibre pigment; face still reads as a mannequin.','hypothesis':'Inspect actual saved material output, attribute values and raster footprint before choosing a correction. A matte-constant diagnostic distinguishes pigment/shading from geometry coverage without changing skin or exposure.','minimalDiagnostic':['Saved material graph, mesh slots, visibility and projected fibre footprint.','Original versus constant dark-brown diffuse material on exact same brow mesh, plus a separate labelled emission mask.'],'rejectIf':['Any skin/hair/eye/light/exposure change.','Only eyebrow close-up improves while the complete face regresses.','A flat painted strip or uniform black block replaces fibre detail.'],'resources':{'threads':4,'diagnosticConditions':3,'meshGrowth':0,'renderViews':['face','brows']},'collisionPolicy':'Material-only diagnostic has no geometric collision change. Exact saved-state checks are required before inheriting static evidence; no redundant complete-hair collision rerun.'})
    bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;base.v14.solid.stage.set_pose(bpy.data.objects['AFN_R0005_Rig'],'neutral');s.render.threads_mode='FIXED';s.render.threads=4
    brows=[bpy.data.objects[n] for n in ('AFN11_L_BrowFibres','AFN11_R_BrowFibres')];material=bpy.data.materials['AFN11_BrowKeratin'];nodes=material.node_tree.nodes;links=material.node_tree.links
    def val(i):
        v=getattr(i,'default_value',None);return list(v) if v is not None and not isinstance(v,str) and hasattr(v,'__iter__') else v
    data={'sourceSha256':sha(SRC),'material':material.name,'nodes':[{'name':n.name,'type':n.bl_idname,'inputs':[(i.name,val(i),i.is_linked) for i in n.inputs]} for n in nodes],'links':[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in links],'brows':[]}
    for o in brows:
        attr=o.data.attributes['AFN11_BrowPigment'];values=np.array([v.value for v in attr.data]);data['brows'].append({'object':o.name,'vertices':len(o.data.vertices),'faces':len(o.data.polygons),'materialSlots':[m.name for m in o.data.materials],'materialIndices':sorted(set(p.material_index for p in o.data.polygons)),'hideRender':o.hide_render,'collections':[(c.name,c.hide_render) for c in o.users_collection],'bounds':[[min(v.co[a] for v in o.data.vertices),max(v.co[a] for v in o.data.vertices)] for a in range(3)],'pigmentMinMax':[float(values.min()),float(values.max())],'pigmentDomain':attr.domain,'pigmentType':attr.data_type})
    for row,n in zip(data['nodes'],nodes):
        if hasattr(n,'color_ramp'):row['rampElements']=[{'position':e.position,'color':list(e.color)} for e in n.color_ramp.elements]
        if hasattr(n,'attribute_name'):row['attributeName']=n.attribute_name;row['attributeType']=n.attribute_type
    save('saved-brow-inspection.json',data)
    if '--inspection-only' in sys.argv:
        print('R0018_SAVED_GRAPH_INSPECTED',flush=True);return
    mode='constant-diffuse' if '--constant' in sys.argv else 'emission-mask' if '--mask' in sys.argv else 'baseline'
    if mode!='baseline':
        out=next(n for n in nodes if n.bl_idname=='ShaderNodeOutputMaterial')
        if mode=='constant-diffuse':
            shader=nodes.new('ShaderNodeBsdfDiffuse');shader.inputs['Color'].default_value=(.022,.011,.005,1.);shader.inputs['Roughness'].default_value=.70
        else:
            shader=nodes.new('ShaderNodeEmission');shader.inputs['Color'].default_value=(1.,0.,0.,1.);shader.inputs['Strength'].default_value=1.
        links.new(shader.outputs[0],out.inputs['Surface'])
    rows=[];head=1.5624730926266572*.91
    for view,loc,target,lens,res in [('face',(0.,-.90,head+.015),(0.,-.02,head),100,(1100,1100)),('brows',(0.,-.43,1.474),(0.,-.115,1.474),100,(1400,650))]:
        c=s.camera;c.location=loc;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=lens;s.render.resolution_x,s.render.resolution_y=res;s.render.resolution_percentage=100;s.render.filepath=str(E/f'{mode}-{view}.png');bpy.ops.render.render(write_still=True)
        screen=[]
        for o in brows:
            pts=np.array([tuple(world_to_camera_view(s,c,o.matrix_world@v.co))[:2] for v in o.data.vertices]);screen.append({'object':o.name,'pixelBounds':[float(pts[:,0].min()*res[0]),float((1-pts[:,1].max())*res[1]),float(pts[:,0].max()*res[0]),float((1-pts[:,1].min())*res[1])]})
        rows.append({'path':s.render.filepath,'view':view,'projectedBrowBounds':screen,'resolution':res,'lens':lens,'exposure':s.view_settings.exposure,'engine':s.render.engine})
    save(mode+'-diagnostic.json',{'mode':mode,'sourceSha256':sha(SRC),'geometryUnchanged':True,'temporaryMaterialOnly':mode!='baseline','savedSourceModified':False,'renders':rows})
    print('R0018_DIAGNOSTIC_DONE '+mode,flush=True)
if __name__=='__main__':main()
