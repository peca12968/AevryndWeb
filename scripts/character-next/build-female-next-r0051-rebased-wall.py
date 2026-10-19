"""B: rebase damaged posterior sculpt on proven clean same-cage subdivision.

Use native Multires Reshape, retaining editable sculpt, not a corrective-node
stack. Exact ordered quad correspondence is required before copying any point.
"""
from pathlib import Path
import bpy,importlib.util,numpy as np,time,json
sp=importlib.util.spec_from_file_location('probe51',Path(__file__).with_name('probe-female-next-r0051-rebase.py'))
p=importlib.util.module_from_spec(sp);sp.loader.exec_module(p)
k=p.k;a=k.a;b=k.b;f=k.f;E=k.E
OUT=b.S/'aevrynd-female-next-r0051-b-rebased-eye-wall.blend'
MASK='AFN51_TemporaryPosteriorRebaseMask'

def coords(o):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
    P=np.empty(len(m.vertices)*3,dtype='f4');m.vertices.foreach_get('co',P)
    mask=None
    if MASK in m.attributes:
        mask=np.empty(len(m.vertices),dtype='f4');m.attributes[MASK].data.foreach_get('value',mask)
    ev.to_mesh_clear();return P.reshape(-1,3),mask

def main():
    tick=time.time();proof=json.loads((E/'b-rebase-feasibility.json').read_text())
    assert proof['sameFullPolygonLoopTopology'] and proof['undisplacedSelf']['actualSelfPairs']==0
    assert all(r['actualSurfaceIntersectionPairs']==0 for r in proof['undisplacedFixedOptics'].values())
    assert b.sha(k.OUT)==proof['sha256'];bpy.ops.wm.open_mainfile(filepath=str(k.OUT))
    body=bpy.data.objects[b.BODY];before=f.state();originalTopology=p.topology(body)
    mult=next(m for m in body.modifiers if m.type=='MULTIRES');P,_=coords(body)
    reg=json.loads((E/'a-build-summary.json').read_text())['regions']
    nativeMask=np.zeros(len(body.data.vertices),dtype='f4')
    for row in reg.values():nativeMask[row['vertices']]=1.
    attr=body.data.attributes.new(MASK,'FLOAT','POINT');attr.data.foreach_set('value',nativeMask)
    mult.show_viewport=mult.show_render=False
    sub=body.modifiers.new('AFN51_SameCageReference','SUBSURF');sub.levels=sub.render_levels=3
    sub.subdivision_type='CATMULL_CLARK';bpy.context.view_layer.update();Q,W=coords(body)
    assert all(np.array_equal(x,y) for x,y in zip(originalTopology,p.topology(body)))
    W=np.clip(W,0,1);W=W*W*(3-2*W)
    target=P.astype('f8')*(1-W[:,None])+Q.astype('f8')*W[:,None]
    # Temporary same-topology source for native editable Multires Reshape.
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    targetMesh=bpy.data.meshes.new_from_object(ev,preserve_all_data_layers=True,depsgraph=bpy.context.evaluated_depsgraph_get())
    targetMesh.vertices.foreach_set('co',target.astype('f4').ravel());targetMesh.update()
    temp=bpy.data.objects.new('AFN51_TEMP_RESHAPE_TARGET',targetMesh);bpy.context.scene.collection.objects.link(temp)
    temp.matrix_world=body.matrix_world.copy()
    body.modifiers.remove(sub);mult.show_viewport=mult.show_render=True
    body.data.attributes.remove(body.data.attributes[MASK])
    for o in bpy.context.view_layer.objects:o.select_set(False)
    body.hide_set(False);body.select_set(True);temp.select_set(True);bpy.context.view_layer.objects.active=body
    result=bpy.ops.object.multires_reshape(modifier=mult.name);assert result=={'FINISHED'}
    bpy.data.objects.remove(temp,do_unlink=True);bpy.data.meshes.remove(targetMesh);bpy.context.view_layer.update()
    R,_=coords(body);err=np.linalg.norm(R.astype('f8')-target,axis=1)
    untouched=W==0;rounding=np.linalg.norm(R[untouched].astype('f8')-P[untouched].astype('f8'),axis=1)
    after=f.state();assert all(after[key]==before[key] for key in ('materials','skinFields','curves','stage'))
    assert all(after['meshes'][n]==row for n,row in before['meshes'].items() if n!=b.BODY)
    assert all(np.array_equal(x,y) for x,y in zip(originalTopology,p.topology(body)))
    bpy.context.scene['AFN51_status']='NATIVE_MULTIRES_REBASED_POSTERIOR_WALL_STATIC_CANDIDATE'
    b.camera('face');bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    k.save('b-build-summary.json',{'source':str(k.SRC),'sourceSha256':b.sha(k.SRC),
        'intermediateSource':str(k.OUT),'intermediateSourceSha256':b.sha(k.OUT),
        'output':str(OUT),'outputSha256':b.sha(OUT),
        'method':'Native Multires reshape from clean same-native-cage subdivision in posterior disk, with interpolated fixed native mask; original sculpt retained outside patch. No extra permanent modifier/controller or external data dependency.',
        'sameOrderedFullPolygonTopology':True,'posteriorInfluencedVertices':int((W>0).sum()),
        'fullWeightVertices':int((W==1).sum()),'zeroWeightVertices':int(untouched.sum()),
        'targetReadbackMaximumLocalErrorM':float(err.max()),
        'zeroWeightMaximumLocalReshapeRoundingM':float(rounding.max()),
        'zeroWeightBitExactVertices':int((rounding==0).sum()),
        'nativeMaterialSkinFieldsCurvesStageOtherMeshesExact':True,
        'sourceReference':'https://docs.blender.org/manual/en/4.4/modeling/modifiers/generate/multiresolution.html',
        'scope':'Actual installed5.2.2 operator result/readback decides compatibility; documentation describes reshape with matching topology and indices. No motion or contact acceptance.',
        'seconds':time.time()-tick})
    f.E=E;f.render('b-after',('face','oblique','profile'));a.i.i.E=E;a.i.i.closeup('b-after');a.i.ch.review.extras('b-after',E)
    print('R51_B_REBASE_READY',float(err.max()),float(rounding.max()),int((rounding==0).sum()),len(rounding),time.time()-tick,flush=True)

if __name__=='__main__':main()
