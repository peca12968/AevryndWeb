"""Reopen exact material candidates, independent invariants and full views."""
import bpy,importlib.util,json,time,hashlib,numpy as np
from pathlib import Path
sp=importlib.util.spec_from_file_location('v49skin',Path(__file__).with_name('build-female-next-r0049-skin-response.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
b=a.b;f=a.f;E=a.E;S=a.S
def authoring():
    rows=[]
    for o in bpy.context.scene.objects:
        if not o.name.startswith('AFN48_'):continue
        row={'name':o.name,'type':o.type,'hideRender':o.hide_render,'matrix':b.matrix(o.matrix_world)}
        if o.type=='MESH':row['mesh']=b.mesh_signature(o.data)
        elif o.type=='CURVE':row['splines']=[{'type':s.type,'points':[{'co':list(p.co),'left':list(p.handle_left),'right':list(p.handle_right)}for p in s.bezier_points]}for s in o.data.splines]
        rows.append(row)
    return rows
def albedo(mat):
    shader=mat.node_tree.nodes.get('Principled BSDF');start=shader.inputs['Base Color'].links[0].from_node;names=set()
    def visit(n):
        if n.name in names:return
        names.add(n.name)
        for inp in n.inputs:
            for link in inp.links:visit(link.from_node)
    visit(start);state=a.shader_state(mat);return {'nodes':[r for r in state['nodes']if r['name']in names],'links':[r for r in state['links']if r[0]in names and r[2]in names]}
def remaining(tag):
    old=json.loads((E/f'{tag}-renders.json').read_text());f.E=E;f.render(tag,('oblique','profile'));new=json.loads((E/f'{tag}-renders.json').read_text());a.save(tag+'-renders.json',old+new)
    for view in ['opposite-oblique','alternate-oblique','body-face','back']:
        if not (E/f'{tag}-{view}.png').exists():a.i.ch.review.extras(tag,E);break
def main():
    tick=time.time();bpy.ops.wm.open_mainfile(filepath=str(a.SRC));before=f.state();originalAuthoring=authoring();baselineAlbedo=albedo(bpy.data.objects[b.BODY].data.materials[0]);rows=[];remaining('before')
    # Supplemental true 3D magnification; never substitute for complete views.
    b.camera('face');bpy.context.scene.camera.data.lens=170;bpy.context.scene.render.filepath=str(E/'before-skin-detail.png');bpy.ops.render.render(write_still=True)
    for tag,path,file in [('A',a.OUT,'a-build-summary.json'),('B',S/'aevrynd-female-next-r0049-b-surface-relief.blend','b-build-summary.json'),('C',S/'aevrynd-female-next-r0049-c-body-pigment.blend','c-build-summary.json')]:
        summary=json.loads((E/file).read_text());assert b.sha(path)==summary['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(path));after=f.state();assert before['meshes']==after['meshes']and before['skinFields']==after['skinFields']and before['curves']==after['curves']and before['stage']==after['stage'];assert all(after['materials'][n]==r for n,r in before['materials'].items()if n!=b.BODY);assert authoring()==originalAuthoring;mat=bpy.data.objects[b.BODY].data.materials[0];shader=mat.node_tree.nodes.get('Principled BSDF');out=mat.node_tree.nodes.get('Material Output');assert not out.inputs['Displacement'].is_linked and shader.inputs['Alpha'].default_value==1 and not shader.inputs['Alpha'].is_linked
        changed=[];state=a.shader_state(mat);original=summary['skinBefore']['shader'];names={x['name']:x for x in original['nodes']}
        for node in state['nodes']:
            if node['name']not in names:continue
            for key,val in node['inputs'].items():
                if val!=names[node['name']]['inputs'][key]:changed.append((node['name'],key,names[node['name']]['inputs'][key],val))
        if tag=='A':assert {k[1]for k in changed}=={'Subsurface Weight','Specular IOR Level'}and len(changed)==2;assert albedo(mat)==baselineAlbedo
        if tag=='B':assert len(changed)==1 and changed[0][1]=='Specular IOR Level';assert albedo(mat)==baselineAlbedo;assert abs(shader.inputs['Subsurface Weight'].default_value-.09)<1e-6;assert mat.node_tree.nodes['AFN49B_PoreCentres'].feature=='F1'
        if tag=='C':assert changed==[];assert abs(shader.inputs['Subsurface Weight'].default_value-.09)<1e-6 and abs(shader.inputs['Specular IOR Level'].default_value-.30)<1e-6
        row={'tag':tag,'source':str(path),'sha256':b.sha(path),'bytes':path.stat().st_size,'reopened':True,'allOriginalVisibleGeometryNativeUVFieldsHairDataAndStageExact':True,'r48HiddenScalpAnd29NativeControlsExact':True,'allNonSkinMaterialsExact':True,'originalNodeInputChanges':changed,'albedoGraphExact':tag!='C','geometryDisplacement':False,'alphaOpaqueUnchanged':True,'libraries':len(bpy.data.libraries),'qualification':'Material-only static source proof, not appearance/physics/runtime acceptance'}
        if tag=='C':
            body=bpy.data.objects[b.BODY];attr=body.data.color_attributes['AFN49C_RegisteredBodyPigment'];data=np.empty(len(attr.data)*4,dtype='f4');attr.data.foreach_get('color',data);data=data.reshape(-1,4);assert np.isfinite(data).all()and np.all(data[:,3]==1);P=np.array([v.co[:]for v in body.data.vertices]);mx=np.array(body.matrix_world);P=P@mx[:3,:3].T+mx[:3,3];body.data.calc_loop_triangles();T=np.array([t.vertices[:]for t in body.data.loop_triangles]);area=np.linalg.norm(np.cross(P[T[:,1]]-P[T[:,0]],P[T[:,2]]-P[T[:,0]]),axis=1)*.5;weights=np.bincount(T.ravel(),weights=np.repeat(area/3,3),minlength=len(P));mean=(weights[:,None]*data[:,:3]).sum(0)/weights.sum();err=float(np.max(abs(mean-np.array((.32,.23,.18)))));assert err<2e-7;head=P[:,2]>=1.34;assert np.array_equal(data[head,:3],np.tile(np.array((.32,.23,.18),dtype='f4'),(int(head.sum()),1)));row['savedBodyColor']={'attribute':attr.name,'domain':attr.domain,'type':attr.data_type,'points':len(data),'sha256':hashlib.sha256(data.tobytes()).hexdigest(),'areaWeightedLinearRGB':mean.tolist(),'meanReflectanceErrorMax':err,'headFallbackExact':True,'notSubjectMeasuredOrAnatomyProof':True}
        remaining(tag.lower()+'-after')
        if tag=='B':b.camera('face');bpy.context.scene.camera.data.lens=170;bpy.context.scene.render.filepath=str(E/'b-after-skin-detail.png');bpy.ops.render.render(write_still=True)
        rows.append(row)
    a.save('reopened-material-verification.json',{'status':'PASS_EXACT_MATERIAL_ONLY_INVARIANTS_NOT_CHARACTER_ACCEPTANCE','rows':rows,'source':str(a.SRC),'sourceSha256':b.sha(a.SRC),'baseWorkingSource':str(a.WORKING),'baseWorkingSha256':b.sha(a.WORKING),'contactScope':'Exact actual displayed geometry,alpha and no-displacement invariance preserves only existing source contact evidence in its prior stated neutral/static scope. No new contact passing claim, no new continuous/self/dynamic certificate.','seconds':time.time()-tick});print('R49_ALL_MATERIALS_REOPENED',time.time()-tick,flush=True)
if __name__=='__main__':main()
