"""Independent saved-source comparison; no contact or motion acceptance."""
from pathlib import Path
from types import SimpleNamespace
import bpy,numpy as np,json,time,sys,hashlib,importlib.util
def module(n,p):
    s=importlib.util.spec_from_file_location(n,Path(__file__).with_name(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
q=module('read71build','build-female-next-r0071-hair-scattering.py')
v=module('read71native','verify-female-next-r0061-complete-groom.py')
def digest(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def group_sig(t):
    s=q.m.k.f.v.v32.material_signature(SimpleNamespace(node_tree=t))
    for row,n in zip(s['nodes'],t.nodes):
        row.update(model=getattr(n,'model',None),parametrization=getattr(n,'parametrization',None),operation=getattr(n,'operation',None))
        if n.type=='VALTORGB':row['ramp']=[(e.position,list(e.color)) for e in n.color_ramp.elements]
    return s
def world(o):
    d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;P=q.m.base.array3(d.position_data,'vector').astype('f8');A=np.array(o.matrix_world);return P@A[:3,:3].T+A[:3,3]
def state():
    s=bpy.context.scene;s.frame_set(1);names=q.m.native_names()
    native={n:v.mesh_signature(bpy.data.objects[n]) for n in names}
    facial={n:q.m.k.v59.native_curves(bpy.data.objects[n]) for n in ('AFN57_NATIVE_BROWS','AFN57_NATIVE_LASHES')}
    hair={}
    for n in q.HAIR:
        x=q.m.k.v59.native_curves(bpy.data.objects[n]);x.pop('materials');hair[n]=x
    rig=bpy.data.objects['AFN69_BODY_CONTROLS'];bones=[(b.name,b.parent.name if b.parent else None,np.array(b.matrix_local).tolist(),b.length) for b in rig.data.bones]
    weights={}
    for n in names:
        o=bpy.data.objects[n];weights[n]=digest(np.array([(i,g.group,g.weight) for i,p in enumerate(o.data.vertices) for g in p.groups],dtype='f8'))
    view=[s.view_settings.exposure,s.view_settings.view_transform,s.view_settings.look];light=q.lights();v.raise_subdivision();poses={}
    for f in (1,13,49):
        s.frame_set(f);bpy.context.view_layer.update();row={}
        for n in names:
            m=q.m.k.mesh(bpy.data.objects[n]);assert np.isfinite(m['V']).all();row[n]={'positions':digest(m['V']),'triangles':digest(m['T']),'vertices':len(m['V']),'triangleCount':len(m['T'])}
        for n in q.HAIR:
            p=world(bpy.data.objects[n]);assert np.isfinite(p).all();row[n]={'positions':digest(p),'points':len(p)}
        poses[str(f)]=row
    return {'native':native,'facial':facial,'hairNativeGeometryRadiiMatrix':hair,'bones':bones,'weights':weights,'view':view,'lights':light,'evaluatedPoses':poses}
def main():
    tick=time.time();assert q.sha(q.SRC)==q.SOURCE_SHA;bpy.ops.wm.open_mainfile(filepath=str(q.SRC));baseline=state()
    old_group=group_sig(bpy.data.materials['Brown hair'].node_tree.nodes['Group'].node_tree)
    mats={m.name:q.m.k.f.v.v32.material_signature(m) for m in bpy.data.materials if m.use_nodes}
    rows=[]
    for tag in ('a','b'):
        ref=json.loads((q.E/(tag+'-build-summary.json')).read_text());path=Path(ref['output'])
        if '--history' in sys.argv:path=q.R/'sites-engine-journey/assets-source/aevrynd-character/female-next'/path.name
        assert q.sha(path)==ref['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(path));current=state();assert current==baseline,'Saved source changed geometry, poses, weights, stage or original facial materials'
        assert all(mats[n]==q.m.k.f.v.v32.material_signature(bpy.data.materials[n]) for n in mats)
        mat=bpy.data.materials[ref['change']['material']];tree=mat.node_tree;group=tree.nodes['Group'];routes=[l for l in tree.links if l.to_node.name=='Reroute.001'];assert len(routes)==1 and routes[0].from_socket.name=='Cycles Shader'
        gs=group_sig(group.node_tree)
        if tag=='a':assert gs==old_group
        else:
            new_nodes={r['name']:r for r in gs['nodes']};assert len(gs['nodes'])==len(old_group['nodes'])+1
            assert all(r==new_nodes[r['name']] for r in old_group['nodes'])
            oldlinks=set(tuple(x) for x in old_group['links']);newlinks=set(tuple(x) for x in gs['links'])
            assert oldlinks-newlinks=={('Curves Info','Random','Mix','B')}
            assert len(newlinks-oldlinks)==4
        for n in q.HAIR:assert bpy.data.objects[n].data.materials[0]==mat
        external=[];packed=0
        for im in bpy.data.images:
            if im.packed_file:packed+=1
            elif im.source=='FILE':
                p=Path(bpy.path.abspath(im.filepath));assert im.filepath.startswith('//') and p.exists();external.append({'relative':im.filepath,'sha256':q.sha(p)})
        assert len(external)==15 and not bpy.data.libraries and not bpy.app.handlers.frame_change_pre and not bpy.app.handlers.frame_change_post
        rows.append({'tag':tag,'source':str(path),'sha256':q.sha(path),'originalNativeAnatomyKeysUVSkinEyeMaterialsExact':True,'originalRigWeightsAndPosedActualDisplayGeometryExact':True,'checkedFrames':[1,13,49],'hairNativeCountsRadiiMatricesExact':True,'originalLightsExposureAndColorManagementExact':True,'originalMaterialAndGroupNodeParametersExact':True,'routingAndOnlyDocumentedPaletteLinksChanged':True,'externalTextures':external,'packedImages':packed,'newContactOrNaturalMotionOrRuntimeAcceptance':False})
        print('R71_SAVED_READBACK',tag,flush=True)
    q.save('history-readback.json' if '--history' in sys.argv else 'independent-readback.json',{'status':'SAVED_SOURCES_REOPENED_GEOMETRY_AND_RIG_EXACT_MATERIAL_CHANGE_ONLY','studies':rows,'baselineEvaluatedPoses':baseline['evaluatedPoses'],'scope':'Material-only source comparison. Underlying surfaces/curves and three poses equal r69. Shader opacity/visibility changes do not inherit contact or natural-motion acceptance.','seconds':time.time()-tick})
if __name__=='__main__':main()
