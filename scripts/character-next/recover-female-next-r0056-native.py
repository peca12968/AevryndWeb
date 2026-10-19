"""Inspect the terminal native job's quit snapshot, never rerun its strokes."""
from pathlib import Path
import bpy,importlib.util,numpy as np,json,time
sp=importlib.util.spec_from_file_location('recover56',Path(__file__).with_name('build-female-next-r0054-clump-volume.py'))
k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
b=k.b;f=k.f;E=b.R/'Evidence/character-female-next/r0056-target-native-comb'
SRC=b.S/'aevrynd-female-next-r0056-a-recovered-native-comb.blend';OUT=b.S/'aevrynd-female-next-r0056-a-target-native-comb.blend'
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def differences(a,z,path=''):
    if type(a)!=type(z):return [{'path':path,'beforeType':str(type(a)),'afterType':str(type(z))}]
    if isinstance(a,dict):
        out=[]
        for name in sorted(set(a)|set(z)):
            if name not in a or name not in z:out.append({'path':path+'/'+name,'presenceBefore':name in a,'presenceAfter':name in z})
            else:out.extend(differences(a[name],z[name],path+'/'+name))
        return out
    if a!=z:return [{'path':path,'before':a,'after':z}]
    return []
def main():
    bpy.ops.wm.open_mainfile(filepath=str(k.SRC));before=f.state()
    bpy.ops.wm.open_mainfile(filepath=str(SRC));after=f.state();delta=[]
    for key in ('meshes','materials','skinFields','stage'):delta.extend(differences(before[key],after[key],key))
    for name,row in before['curves'].items():delta.extend(differences(row,after['curves'][name],'curves/'+name))
    o=bpy.data.objects['AFN56_TARGET_NATIVE_MASTER_CURVES'];P,R=f.v.hair_arrays(o);data=np.load(b.R/'Evidence/character-female-next/r0053-new-primary-groom/refined-foundation-data.npz')
    assert np.array_equal(P[:,0],data['initialPaths'][:,0].astype('f4')) and np.array_equal(R,data['radii'].astype('f4'))
    L=.095+1.20*(P[:,0,2]-1.43);seed=(P[:,0,None]+data['normals'][:,None]*L[:,None,None]*np.linspace(0,1,128)[None,:,None]).astype('f4');seed[:,0]=P[:,0]
    changed=int(np.any(np.linalg.norm(P-seed,axis=2)>1e-7,axis=1).sum())
    save('a-terminal-invariant-differences.json',{'terminalSnapshot':str(SRC),'sha256':b.sha(SRC),'originalStateDifferences':delta,'changedCurves':changed,'rootsAndRadiiExact':True})
    print('R56_RECOVERY_DIFFERENCES',json.dumps(delta,ensure_ascii=False)[:3000],changed,flush=True)
    np.savez_compressed(E/'a-native-guide-data.npz',before=seed,positions=P,radii=R,normals=data['normals'],sourceCurveIndices=np.arange(64,dtype='i4'))
    # Recovery is a rejected/unchecked study regardless of whether only stage
    # metadata differs. Do not adopt or silently discard the failed invariant.
    bpy.data.objects[k.k.OLD].hide_render=True;bpy.data.objects[k.k.OLD].hide_set(True)
    if bpy.context.object and bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
    active=bpy.context.scene.tool_settings.curves_sculpt.brush
    if active:bpy.data.brushes.remove(active,do_unlink=True)
    b.camera('face');bpy.context.scene.camera.data.lens=85;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    session=json.loads((E/'native-session.json').read_text())
    save('a-build-summary.json',{'source':str(k.SRC),'sourceSha256':b.sha(k.SRC),'terminalRecovery':str(SRC),'terminalRecoverySha256':b.sha(SRC),'output':str(OUT),'outputSha256':b.sha(OUT),
        'status':'RECOVERED_AFTER_FINAL_INVARIANT_FAILURE_NOT_ADOPTED','curveCount':64,'pointsPerCurve':128,'changedCurves':changed,'rootPositionsAndRadiiExact':True,'originalStateDifferences':delta,'strokes':session['strokes'],
        'method':'Native Comb, new target-rooted normal seeds, four fixed115px local strokes per guide; no copied paths.'})
    f.E=E;f.render('a-actual-fibres',('face','oblique','profile'));k.k.k.k.a.i.ch.review.extras('a-actual-fibres',E)
    o.data.attributes['radius'].data.foreach_set('value',np.full_like(R,.0007).ravel());bpy.context.view_layer.update()
    f.render('a-path-diagnostic',('face','oblique','profile'));k.k.k.k.a.i.ch.review.extras('a-path-diagnostic',E)
    print('R56_A_RECOVERED_RENDERED',changed,flush=True)

if __name__=='__main__':main()
