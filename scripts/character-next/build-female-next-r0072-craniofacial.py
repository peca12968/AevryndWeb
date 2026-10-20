"""One source-authored cheek/jaw form candidate on the complete r69 woman.

Data-only CC0 sculpt deltas, with existing eye repair, female morph, rig,
skin/materials, light and editable groom retained. No parameter sweep.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,time,sys,importlib.util
def module(n,p):
    sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(p));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
m=module('build72rig','build-female-next-r0069-complete-controls.py')
q=module('build72render','build-female-next-r0071-hair-scattering.py')
R=m.R;S=m.S;E=R/'Evidence/character-female-next/r0072-craniofacial-form';D=R/'Reference/character/charmorph-vitruvian-cc0/r0072-facial-form'
SRC=S/'aevrynd-female-next-r0069-a-complete-controls-study.blend';OUT=S/'aevrynd-female-next-r0072-a-authored-cheek-jaw-study.blend';SOURCE_SHA='f358d3c5a4d00ee6ad94d324612b33bdcf5aa4dde0bb19382d72bc7afabbb667'
COEFFICIENTS={'Cheeks_BoneDefinition':.5,'Jaw_Definition':.35}
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def open_source(p):
    bpy.ops.wm.open_mainfile(filepath=str(p));bpy.context.scene.frame_set(1);m.shade.settings();m.shade.g.E=E
def pilot(view):
    s=bpy.context.scene;m.shade.settings();m.k.b.camera(view);s.camera.data.lens=85;s.render.resolution_x=s.render.resolution_y=640;s.cycles.samples=16
    ctl={'camera':np.array(s.camera.matrix_world).tolist(),'lights':q.lights(),'samples':16,'resolution':640,'seed':s.cycles.seed,'exposure':s.view_settings.exposure,'look':s.view_settings.look,'frame':s.frame_current,'engine':s.render.engine,'hairPrimitive':s.render.hair_type}
    old=E.parent/'r0071-hair-scattering';p=old/('baseline-pilot-controls.json' if view=='face' else 'baseline-body-pilot-controls.json');assert ctl==json.loads(p.read_text())
    s.render.filepath=str(E/('a-pilot-'+view+'.png'));bpy.ops.render.render(write_still=True);save('a-pilot-'+view+'-controls.json',{'candidate':ctl,'reusedExactR69BaselineControls':str(p),'reusedImage':str(old/('baseline-pilot-'+view+'.png')),'noBaselineRerenderOrNewBaselineGainClaim':True})
def main():
    tick=time.time()
    if '--views' in sys.argv:
        assert sha(OUT)==json.loads((E/'a-build-summary.json').read_text())['outputSha256'];open_source(OUT);save('a-full-view-controls.json',m.shade.render('a-form',('face','body-face','oblique','profile','back','alternate-oblique')));return
    assert not OUT.exists() and sha(SRC)==SOURCE_SHA;open_source(SRC);stage=q.lights();native=np.load(R/'Reference/character/charmorph-vitruvian-cc0/Default.npy',allow_pickle=False);N=len(native);morphs={};total=np.zeros_like(native)
    for name,value in COEFFICIENTS.items():
        path=D/'morphs/L2'/(name+'.npz');z=np.load(path,allow_pickle=False);delta=np.zeros_like(native);delta[z['idx']]=z['delta'];assert np.isfinite(delta).all();morphs[name]={'value':value,'path':str(path),'sha256':sha(path),'delta':delta};total+=value*delta
    changes=[];ids_seen=[]
    for name in m.native_names():
        o=bpy.data.objects[name];ids=np.empty(len(o.data.vertices),'i4');o.data.attributes['AFN60_NativeVertexID'].data.foreach_get('value',ids);ids_seen.extend(ids.tolist());base=np.array([p.co[:] for p in o.data.shape_keys.key_blocks[0].data]);assert np.max(np.abs(base-native[ids]))<1e-7
        if not np.any(total[ids]):continue
        for morph,row in morphs.items():
            delta=row['delta'][ids]
            if not np.any(delta):continue
            key=o.shape_key_add(name='AFN72_CC0_'+morph,from_mix=False);key.relative_key=o.data.shape_keys.key_blocks[0];key.data.foreach_set('co',(base+delta).astype('f4').ravel());key.slider_min=-1.;key.slider_max=1.;key.value=row['value']
            changes.append({'object':name,'key':key.name,'value':key.value,'affectedNativeVertices':int((np.linalg.norm(delta,axis=1)>1e-10).sum()),'maximumWeightedWorldDeltaM':float(np.linalg.norm(delta@np.array(o.matrix_world)[:3,:3].T*key.value,axis=1).max())})
    assert sorted(ids_seen)==list(range(N)) and q.lights()==stage
    s=bpy.context.scene;s['AFN72_scope']='One data-only CC0 authored cheek/jaw form study, .5/.35. Existing female/eye repair/blink/rig and source skin/hair materials retained. New appearance/contact/runtime acceptance unproven.'
    m.k.b.camera('face');s.camera.data.lens=85;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    np.savez_compressed(E/'a-native-morph-delta.npz',totalDelta=total,**{n:v['delta'] for n,v in morphs.items()})
    save('a-build-summary.json',{'source':str(SRC),'sourceSha256':sha(SRC),'output':str(OUT),'outputSha256':sha(OUT),'outputBytes':OUT.stat().st_size,'coefficients':COEFFICIENTS,'sourceData':{n:{k:v for k,v in row.items() if k!='delta'} for n,row in morphs.items()},'changes':changes,'materialLightExposureRigWeightTuning':False,'sourceCanonicalVertices':N,'maximumCombinedNativeDeltaM':float(np.linalg.norm(total,axis=1).max()),'preservedExistingRepairAndFemaleMorph':True,'fullAnatomyOrNaturalMotionOrContactOrRuntimeAccepted':False,'secondsBeforePilot':time.time()-tick})
    pilot('face');pilot('body-face');print('R72_COMPLETE_FORM_PILOTS_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
