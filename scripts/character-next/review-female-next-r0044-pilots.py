"""Inspectable rejected native key shapes, actual renders, precise failure map.
No expanded production or animation claim. Complete working source untouched.
"""
import bpy,importlib.util,json,time,hashlib,sys
from pathlib import Path
import numpy as np
from mathutils import Vector
sp=importlib.util.spec_from_file_location('review44c',Path(__file__).with_name('build-female-next-r0044-arap-lids.py'));c=importlib.util.module_from_spec(sp);sp.loader.exec_module(c)
a=c.a;b=a.b;i=a.i;E=a.E;S=a.S;SRC=a.SRC
OUT=S/'aevrynd-female-next-r0044-c-rejected-native-lid-shapes.blend'
def save(n,x):a.save(n,x)
def actual_pairs(P,T):
    bt=i.i.tree(P,T);pairs=bt.overlap(bt);bad=[]
    for x,y in pairs:
        if x<y and set(T[x]).isdisjoint(T[y]):
            p=c.exact.intersections(P[T[x]],P[T[y]])
            if p:bad.append({'triangles':[int(x),int(y)],'vertices':[T[x].tolist(),T[y].tolist()],'intersectionWorldM':[np.array(q).tolist() for q in p]})
    return bad
def main():
    tick=time.time();assert b.sha(SRC)=='d62c180a5af61f6f8d800926b101738c89a8fbe7785fe1054fd655fd018824da';A=np.load(E/'rejected-native-shapes.npz');C=np.load(E/'c-native-shapes.npz');proof={}
    restPairs=actual_pairs(C['restWorld'],C['triangles']);baseline={tuple(p['triangles']) for p in restPairs}
    for name,data in [('A',A),('C',C)]:
        proof[name]={}
        for pose in ('pose0.5','pose1.0'):
            if pose not in data:continue
            bad=actual_pairs(data[pose],data['triangles']);moved=np.linalg.norm(data[pose]-data['restWorld'],axis=1)>1e-9;affected=np.any(moved[data['triangles']],axis=1);changed=[p for p in bad if any(affected[t] for t in p['triangles'])];new=[p for p in bad if tuple(p['triangles']) not in baseline];proof[name][pose]={'actualNonAdjacentSurfacePairs':len(changed),'changedRegionPairs':changed,'fullNativePairs':len(bad),'newFullNativePairs':len(new),'newPairs':new}
    save('independent-native-self-refinement.json',{'scope':'Actual native triangle meshes in exact saved numerical key poses, float64 plane/triangle clipping after BVH broad phase. Changed-region failures separated from pre-existing unrelated native body pairs. Not swept/contact proof for interpolation or full sculpt.','originalNativeUnrelatedSelfPairCount':len(restPairs),'originalNativePairs':restPairs,'results':proof})
    if '--verification-only' in sys.argv:print('R44_SELF_REFINED',json.dumps({n:{p:x['actualNonAdjacentSurfacePairs'] for p,x in ps.items()} for n,ps in proof.items()}),flush=True);return
    bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;body=bpy.data.objects[b.BODY];original=fingerprint=a.f.state();raw=np.array([tuple(v.co) for v in body.data.vertices]);m=np.array(body.matrix_world);nativeWorld=raw@m[:3,:3].T+m[:3,3];assert np.linalg.norm(nativeWorld-C['restWorld'],axis=1).max()<1e-10
    mult=body.modifiers[0];mult.levels=mult.render_levels=mult.sculpt_levels=0;body.shape_key_add(name='Basis')
    for key,name in [('pose0.5','AFN44_C_Half_NATIVE_ONLY'),('pose1.0','AFN44_C_Closed_REJECTED_SELF_CONTACT')]:
        k=body.shape_key_add(name=name);local=(C[key]-m[:3,3])@np.linalg.inv(m[:3,:3]).T;k.data.foreach_set('co',local.astype('f4').ravel());k.value=0.
    failedVertices=sorted({v for p in proof['C']['pose1.0']['changedRegionPairs'] for face in p['vertices'] for v in face})
    group=body.vertex_groups.new(name='AFN44_C_ClosedSelfFailures_SELECTION_ONLY');group.add(failedVertices,1.,'REPLACE')
    body['AFN44_status']='REJECTED_CLOSED_SELF_CONTACT_DIAGNOSTIC_ONLY';body['AFN44_warning']='Native level0 shapes only. Closed shape has actual self intersections; existing lashes/wet tissues/scalp are original neutral attachments, NOT rebuilt for this trial. No full-resolution, animation or runtime qualification.'
    body['AFN44_how_to_inspect']='Object Data > Shape Keys: Half or Closed, one at a time. Multires must stay0 for matching evidence. Restore original r42B file for production.'
    text=bpy.data.texts.new('AFN44_README_REJECTED');text.write('REJECTED TECHNICAL PILOT. Not an accepted character.\nOriginal complete working source remains r42B.\nNative only; original sculpt preserved but disabled for these measurements.\nC closed actual self pairs='+str(proof['C']['pose1.0']['actualNonAdjacentSurfacePairs'])+'\nExisting attached tissues/lashes are neutral and were NOT rebuilt.\nNo blink animation or continuous contact acceptance.\n')
    b.camera('face');s.camera.data.lens=85;s['AFN44_status']='THREE_NATIVE_PILOTS_REJECTED_NO_PRODUCTION_CANDIDATE';s.render.threads_mode='FIXED';s.render.threads=4;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    # Actual closed head views expose the failed geometry and frozen neutral
    # attachments; do not hide them or call these matched appearance A/B.
    closed=body.data.shape_keys.key_blocks['AFN44_C_Closed_REJECTED_SELF_CONTACT'];closed.value=1.;bpy.context.view_layer.update();a.f.E=E;a.f.render('c-rejected-native',('face','oblique'));i.i.E=E;i.i.closeup('c-rejected-native');closed.value=0.
    bpy.ops.wm.open_mainfile(filepath=str(OUT));body=bpy.data.objects[b.BODY];mult=body.modifiers[0];assert mult.levels==mult.render_levels==0;kp=body.data.shape_keys.key_blocks['AFN44_C_Closed_REJECTED_SELF_CONTACT'];kp.value=1.;bpy.context.view_layer.update();P,T=b.evaluated(body,True);assert np.array_equal(T,C['triangles']);maxError=float(np.linalg.norm(P-C['pose1.0'],axis=1).max());assert maxError<2e-7;kp.value=0.;bpy.context.view_layer.update();P0,_=b.evaluated(body,True);assert np.array_equal(P0,C['restWorld']);mult.levels=mult.render_levels=mult.sculpt_levels=3;bpy.context.view_layer.update();assert a.f.state()==original
    group=body.vertex_groups.get('AFN44_C_ClosedSelfFailures_SELECTION_ONLY');assert group is not None
    save('rejected-source-reopen-verification.json',{'source':str(OUT),'sourceSha256':b.sha(OUT),'sourceBytes':OUT.stat().st_size,'opened':True,'nativeClosedShapeReadbackErrorM':maxError,'originalNativeRestExact':True,'originalCompleteStateExactWhenMultiresRestored':True,'nativeControlTopologyUVAndAllUnrelatedSourceStateRetained':True,'failureSelectionOnlyGroup':group.name,'failedNativeVertices':failedVertices,'defaultSourceState':'Neutral with diagnostic Multires0, explicit rejected keys; original Multires detail data retained for return, not validated over rejected shapes.','status':'PASS_INSPECTABLE_REJECTED_STUDY_ONLY','limitations':['Closed actual self crossings remain','Existing neutral tissue/lash attachments are not moved','No production complete candidate, matched appearance gain, motion/continuous contact or engine acceptance'],'seconds':time.time()-tick});print('R44_REVIEW_REJECTED_SAVED',str(OUT),time.time()-tick,flush=True)
if __name__=='__main__':main()
