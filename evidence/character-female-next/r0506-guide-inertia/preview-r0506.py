"""Verify native Curves motion and render comparisons from the saved Blender source."""
from pathlib import Path
from runpy import run_path
from time import perf_counter
import bpy
import numpy as np

ROOT=Path(__file__).resolve().parent
author=run_path(str(ROOT/'author-r0506.py'))
prior=run_path(str(ROOT.parent/'r0505-ear-nape-bridge'/'preview-r0505.py'))
read_json,write_json,digest,positions,attribute,array_hash,r500=(
    author[k] for k in ('read_json','write_json','digest','positions','attribute','array_hash','r500'))
modes=('rigid','spring','rod')


def mode_set(hair,proof,mode):
    mod=hair.modifiers[proof['modifier']]
    getattr(mod.properties.inputs,proof['modeSocket']).value=modes.index(mode)
    hair.update_tag()
    bpy.context.view_layer.update()


def evaluated(hair):
    return positions(hair.evaluated_get(bpy.context.evaluated_depsgraph_get()))


def expected_offset(bake,rest,mode,frame):
    offset=np.zeros_like(rest)
    if mode=='rigid':
        return offset
    stations=bake['stations']
    index=np.arange(rest.shape[1])
    lo=np.clip(np.searchsorted(stations,index,side='right')-1,0,len(stations)-2)
    alpha=((index-stations[lo])/(stations[lo+1]-stations[lo])).astype('f4')
    offsets=bake[mode][frame-1]
    weights=bake['weights']
    nearest=bake['nearestGuideRows']
    for slot in range(nearest.shape[1]):
        guide=offsets[nearest[:,slot]]
        a,b=guide[:,lo],guide[:,lo+1]
        offset+=(a+(b-a)*alpha[None,:,None])*weights[:,slot,None,None]
    offset[:,:9]=0.
    return offset


def open_source():
    proof=read_json(ROOT/'construction-receipt.json')
    source=Path(proof['source']['path'])
    bake_path=Path(proof['bank']['path'])
    assert digest(source)==proof['source']['sha256'] and digest(bake_path)==proof['bank']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
    scene=bpy.context.scene
    hair,skin,gaze=(bpy.data.objects[proof[k]] for k in ('hair','body','gaze'))
    rest=positions(hair)
    assert not hair.hide_get() and not hair.hide_render
    assert array_hash(rest)==proof['controlPositionHash'] and hair.parent.name==proof['rig']
    assert hair.parent_type=='BONE' and hair.parent_bone=='Head'
    assert array_hash(attribute(hair.data,'AFN409_CURVE_ID'))==proof['idsHash']
    assert array_hash(attribute(hair.data,'radius'))==proof['radiusHash']
    body_author=r500['author']
    assert array_hash(body_author['xyz'](skin.data.shape_keys.reference_key.data))==proof['originalBodyBasisHash']
    assert array_hash(body_author['xyz'](skin.data.shape_keys.key_blocks[r500['previous']['KEY_NAMES']['orbital']].data))==proof['originalCheekHash']
    assert not bpy.data.libraries
    assert not [item for item in bpy.data.images if item.source=='FILE' and not item.packed_file]
    with np.load(bake_path) as archive:
        bake={key:archive[key] for key in archive}
    return proof,scene,hair,skin,gaze,rest,bake


def check_frame(scene,hair,gaze,proof,bake,rest,frame,mode):
    r500['activate'](scene,gaze,'separated',0.,float(frame))
    mode_set(hair,proof,mode)
    bank=evaluated(hair)
    expected=rest+expected_offset(bake,rest,mode,frame)
    error=float(np.max(np.abs(expected-bank)))
    assert error<5e-7,(mode,frame,error)
    assert np.array_equal(rest[:,:9],bank[:,:9]),(mode,frame,'pinned')
    if mode=='rigid' or frame==1:
        assert np.array_equal(rest,bank)
    assert np.allclose(np.array(hair.matrix_world),bake['matrices'][frame-1],atol=2e-7,rtol=0.)
    tips=(bank-rest)[:,-1]
    movement=np.linalg.norm(tips,axis=1)*1000.
    return dict(frame=frame,mode=mode,positionHash=array_hash(bank),rootHash=array_hash(bank[:,0]),
        nodeMaxErrorMetres=error,tipMm=np.percentile(movement,[50,95,99,100]).tolist(),
        tipMaxCurveRow=int(movement.argmax()),tipMeanLocalMm=(tips.mean(0)*1000.).tolist())


def main():
    proof,scene,hair,skin,gaze,rest,bake=open_source()
    apex=int(np.linalg.norm(bake['rod'][:,:,-1],axis=2).max(1).argmax())+1
    sample=sorted(set((1,4,7,10,12,14,17,22,29,37,apex)))
    progress_path=ROOT/'reopen-progress.json'
    partial=read_json(progress_path) if progress_path.exists() else dict(source=proof['source'],verified={})
    assert partial['source']==proof['source']
    frames=partial['verified']
    for frame in sample:
        for mode in modes:
            key=f'{mode}:{frame}'
            if key in frames:
                continue
            row=check_frame(scene,hair,gaze,proof,bake,rest,frame,mode)
            frames[key]=row
            write_json(progress_path,partial)
            print('R506_VERIFY',frame,mode,row['tipMm'],flush=True)
    before=check_frame(scene,hair,gaze,proof,bake,rest,apex,'rod')
    check_frame(scene,hair,gaze,proof,bake,rest,apex,'rigid')
    assert check_frame(scene,hair,gaze,proof,bake,rest,apex,'rod')==before
    write_json(ROOT/'reopen-verification.json',dict(source=proof['source'],verified=frames,
        rodGuideApexFrame=apex,modeToggleRestored=True,fps=proof['motionFps'],pinnedControlCount=9,
        strands=proof['follicleCount'],liveNativeGeometry=True,sourceWrite=False))
    for obj in list(scene.objects):
        if obj.type=='CURVES' and obj!=hair:
            data=obj.data
            bpy.data.objects.remove(obj,do_unlink=True)
            if not data.users:
                bpy.data.hair_curves.remove(data)
    config=read_json(ROOT.parent/'r0477-hair-shader-isolation'/'material-probe.json')['view']
    scene.view_settings.view_transform=config['transform']
    scene.view_settings.look=config['look']
    scene.view_settings.exposure=config['exposure']
    for key,value in config['cycles'].items():
        setattr(scene.cycles,key,value)
    scene.render.use_persistent_data=False
    progress=ROOT/'preview-progress.json'
    shots=read_json(progress) if progress.exists() else {}
    recovery=len(shots)
    vistas=[
        ('front','portrait-front',0.,apex,624,19),
        ('oblique','portrait-oblique',32.,apex,624,19),
        ('profile','portrait-profile',-82.,apex,624,19),
        ('rear','rear-oblique',None,apex,624,19),
        ('full','full-body',None,apex,624,19),
        ('crown','portrait-oblique',26.,apex,624,19)]
    motion_frames=sorted(set((1,3,5,7,9,11,12,14,17,22,29,37,apex)))
    vistas.extend((f'f{f:02}','portrait-oblique',8.,f,436,14) for f in motion_frames)
    for name,view,angle,frame,px,samples in vistas:
        r500['activate'](scene,gaze,'separated',0.,float(frame))
        prior['view_settings'](scene,view,angle)
        if name=='crown':
            prior['top_camera'](scene)
        w,h=scene.render.resolution_x,scene.render.resolution_y
        scene.render.resolution_x=round(w*px/max(w,h))
        scene.render.resolution_y=round(h*px/max(w,h))
        scene.render.resolution_percentage=100
        scene.cycles.samples=samples
        for mode in modes:
            key=f'{mode}:{name}'
            if key in shots:
                row=shots[key]
                assert row['sourceSha256']==proof['source']['sha256'] and digest(Path(row['path']))==row['sha256']
                continue
            mode_set(hair,proof,mode)
            position_hash=array_hash(evaluated(hair))
            if f'{mode}:{frame}' in frames:
                assert position_hash==frames[f'{mode}:{frame}']['positionHash']
            output=ROOT/f'{mode}-{name}.png'
            if output.exists():
                output.rename(output.with_name(f'{output.stem}-interrupted.png'))
            scene.render.filepath=str(output)
            now=perf_counter()
            bpy.ops.render.render(write_still=True)
            shots[key]=dict(sourceSha256=proof['source']['sha256'],path=str(output),sha256=digest(output),
                seconds=perf_counter()-now,positionHash=position_hash,mode=mode,frame=frame,
                camera=[list(row) for row in scene.camera.matrix_world],lens=scene.camera.data.lens,
                exposure=scene.view_settings.exposure,seed=scene.cycles.seed,samples=samples,
                resolution=[scene.render.resolution_x,scene.render.resolution_y])
            write_json(progress,shots)
            print('R506_PREVIEW',mode,name,round(shots[key]['seconds'],2),flush=True)
    assert digest(Path(proof['source']['path']))==proof['source']['sha256']
    write_json(ROOT/'preview-receipt.json',dict(source=proof['source'],renders=shots,motionFrames=motion_frames,
        fps=proof['motionFps'],views=[name for name,*_ in vistas[:6]],recoveredFrames=recovery,
        sameCarrierAndMaterials=True,restoredSourceUnchanged=True))


if __name__=='__main__':
    main()

