"""Reopen, operate and render the exact native hairstyle variants."""
from pathlib import Path
from runpy import run_path
from time import perf_counter
import bpy
import numpy as np

ROOT=Path(__file__).resolve().parent
author=run_path(str(ROOT/'author-r0508.py'))
prior=run_path(str(ROOT.parent/'r0505-ear-nape-bridge'/'preview-r0505.py'))
read_json,write_json,digest,positions,attribute,array_hash,r500,set_positions,MODES,PREFIX=(
    author[k] for k in ('read_json','write_json','digest','positions','attribute','array_hash','r500','set_positions','MODES','PREFIX'))
VIEWS=(
    ('front','portrait-front',0.,1.,0.),
    ('oblique','portrait-oblique',35.,1.,0.),
    ('crown','portrait-oblique',26.,1.,0.),
    ('profile','portrait-profile',-82.,1.,0.),
    ('opposite','portrait-profile',82.,1.,0.),
    ('rear-oblique','rear-oblique',None,1.,0.),
    ('full','full-body',None,1.,0.),
    ('turn','portrait-oblique',10.,37.,.75),
    ('blink','portrait-oblique',-27.,1.,.75),
)


def fields(obj):
    return {a.name:array_hash(attribute(obj.data,a.name)) for a in obj.data.attributes
            if a.name!='position' and not a.name.startswith(PREFIX)}


def show(scene,obj):
    for item in scene.objects:
        if item.type=='CURVES':
            item.hide_set(item!=obj)
            item.hide_render=item!=obj
    bpy.context.view_layer.update()


def evaluate(obj):
    bpy.context.view_layer.update()
    return positions(obj.evaluated_get(bpy.context.evaluated_depsgraph_get()))


def opened():
    proof=read_json(ROOT/'construction-receipt.json')
    source=Path(proof['source']['path'])
    bank_path=Path(proof['guideBank']['path'])
    assert digest(source)==proof['source']['sha256'] and digest(bank_path)==proof['guideBank']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
    scene=bpy.context.scene
    control,body,gaze,rig=(bpy.data.objects[proof[key]] for key in ('controlObject','body','gaze','rig'))
    objects={'control':control,**{mode:bpy.data.objects[proof['variants'][mode]['object']] for mode in MODES}}
    carrier=objects[proof['defaultVisible']]
    assert not carrier.hide_get() and not carrier.hide_render and bpy.context.view_layer.objects.active==carrier
    assert not bpy.data.libraries
    assert not [item.filepath for item in bpy.data.images if item.source=='FILE' and not item.packed_file]
    r500['activate'](scene,gaze,'separated',0.,1.)
    return proof,scene,objects,body,gaze,rig


def verify(proof,scene,objects,body,gaze,rig):
    control=objects['control']
    base=positions(control)
    assert array_hash(base)==proof['controlPositionHash'] and array_hash(base[:,0])==proof['rootHash']
    fixed=fields(control)
    assert fixed['AFN409_CURVE_ID']==proof['idsHash'] and fixed['radius']==proof['radiusHash']
    body_author=r500['author']
    assert array_hash(body_author['xyz'](body.data.shape_keys.reference_key.data))==proof['sourceBasisHash']
    assert array_hash(body_author['xyz'](body.data.shape_keys.key_blocks[r500['previous']['KEY_NAMES']['orbital']].data))==proof['sourceCheekHash']
    ids=attribute(control.data,'AFN409_CURVE_ID')
    bridge=attribute(control.data,'AEVRYND_R505_BRIDGE_WEIGHT')>0.
    rear=attribute(control.data,'AEVRYND_R507_LAYER')>=0
    head=rig.matrix_world@rig.pose.bones['Head'].matrix
    original=control.matrix_world.copy()
    guide_bank_path=Path(proof['guideBank']['path'])
    with np.load(guide_bank_path) as guide_bank:
        guide_centres={mode:guide_bank[mode].astype('f4') for mode in MODES}
        expected_layer=guide_bank['layer'].astype('i4')
        expected_lock=guide_bank['route']
        expected_side=guide_bank['side']
        assert np.array_equal(guide_bank['curveIDs'],ids)
    data={}
    replay={}
    for mode,obj in objects.items():
        assert obj.parent==rig and obj.parent_type=='BONE' and obj.parent_bone=='Head' and not obj.modifiers
        assert np.allclose(np.asarray(obj.matrix_world),np.asarray(original),atol=3e-7,rtol=0)
        assert fields(obj)==fixed
        assert tuple(obj.data.materials)==tuple(control.data.materials) and obj.data.surface==control.data.surface
        show(scene,obj)
        bank=evaluate(obj)
        assert np.array_equal(bank[:,:6],base[:,:6]) and np.array_equal(bank[rear|bridge],base[rear|bridge])
        assert np.isfinite(bank).all()
        h=array_hash(bank)
        if mode=='control':
            assert h==proof['controlPositionHash']
        else:
            item=proof['variants'][mode]
            assert h==item['positionHash']
            attrs=[attribute(obj.data,PREFIX+key) for key in ('LAYER','ROUTE','SIDE','INFLUENCE')]
            assert np.array_equal(attrs[0],expected_layer) and np.array_equal(attrs[1],expected_lock)
            assert np.array_equal(attrs[2],expected_side)
            for values,key in zip(attrs,('layerHash','routeHash','sideHash','influenceHash')):
                assert array_hash(values)==item[key]
            guide=bpy.data.objects[item['guide']]
            assert guide.parent==rig and guide.parent_bone=='Head'
            paths=[]
            for spline in guide.data.splines:
                coords=np.empty((len(spline.points),4),'f4')
                spline.points.foreach_get('co',coords.ravel())
                paths.append(coords[:,:3])
            assert np.array_equal(paths,guide_centres[mode])
        data[mode]=bank
        replay[mode]=dict(positionHash=h,rootHash=array_hash(bank[:,0]),samePinnedControls=6,
            protectedBridgeCurves=int(bridge.sum()),protectedRearCurves=int(rear.sum()),changedCurves=int(np.any(bank!=base,axis=(1,2)).sum()))
    active=proof['defaultVisible']
    carrier=objects[active]
    show(scene,carrier)
    changed=expected_layer>=0
    selection=np.flatnonzero(changed & (expected_layer==0) & (expected_lock==1) & (expected_side<0))[::11][:24]
    before=data[active]
    edited=before.copy()
    edited[selection,26:50,1]+=.004*np.sin(np.linspace(0,np.pi,24))
    set_positions(carrier,edited)
    after=array_hash(evaluate(carrier))
    assert after==array_hash(edited) and after!=replay[active]['positionHash']
    set_positions(carrier,before)
    restored=array_hash(evaluate(carrier))
    assert restored==replay[active]['positionHash']
    r500['activate'](scene,gaze,'separated',.75,37.)
    predicted=(rig.matrix_world@rig.pose.bones['Head'].matrix)@head.inverted()@original
    error=float(np.max(np.abs(np.asarray(carrier.matrix_world)-np.asarray(predicted))))
    assert error<3e-6
    r500['activate'](scene,gaze,'separated',0.,1.)
    assert np.max(np.abs(np.asarray(carrier.matrix_world)-np.asarray(original)))<3e-7
    meshes=[obj for obj in scene.objects if obj.type=='MESH']
    for obj in meshes:
        obj.data.calc_loop_triangles()
    stats=dict(vertices=sum(len(obj.data.vertices) for obj in meshes),
        triangles=sum(len(obj.data.loop_triangles) for obj in meshes),
        bones=sum(len(obj.data.bones) for obj in scene.objects if obj.type=='ARMATURE'),
        morphs=sum(len(obj.data.shape_keys.key_blocks)-1 for obj in meshes if obj.data.shape_keys),
        materials=len(bpy.data.materials),images=len(bpy.data.images),curves=len(base),points=int(len(base)*80))
    write_json(ROOT/'reopen-verification.json',dict(source=proof['source'],replay=replay,fixedFields=fixed,stats=stats,
        liveNativeEdit=dict(object=carrier.name,curveIds=ids[selection].tolist(),maximumEditMetres=.004,
            editedHash=after,restoredHash=restored,sourceWritten=False),
        headTurn=dict(frame=37,boneParentMatrixErrorMetres=error),packagedImages=True,noLinkedLibraries=True))
    return data


def configure(scene,name,view,angle):
    prior['view_settings'](scene,view,angle)
    if name=='crown':
        prior['top_camera'](scene)
    size=720 if name in ('front','crown','profile') else 648
    w,h=scene.render.resolution_x,scene.render.resolution_y
    scene.render.resolution_x=round(w*size/max(w,h))
    scene.render.resolution_y=round(h*size/max(w,h))
    scene.render.resolution_percentage=100
    scene.cycles.samples=21 if name in ('front','crown','profile') else 18


def render_source():
    cache=ROOT/'render-cache'
    cache_proof=cache/'receipt.json'
    reopen=ROOT/'reopen-verification.json'
    proof=read_json(ROOT/'construction-receipt.json')
    original=Path(proof['source']['path'])
    assert digest(original)==proof['source']['sha256']
    active=proof['defaultVisible']
    if cache_proof.exists():
        saved=read_json(cache_proof)
        package,arrays=cache/'carrier.blend',cache/'positions.npz'
        assert saved['source']==proof['source']
        assert digest(package)==saved['packageSha256'] and digest(arrays)==saved['arraySha256']
        bpy.ops.wm.open_mainfile(filepath=str(package),load_ui=False,use_scripts=False)
        scene=bpy.context.scene
        carrier=bpy.data.objects[proof['variants'][active]['object']]
        gaze=bpy.data.objects[proof['gaze']]
        with np.load(arrays) as packed:
            data={label:packed[label] for label in ('control',*MODES)}
        independent=read_json(reopen)
        assert independent['source']==proof['source']
        assert array_hash(evaluate(carrier))==independent['replay'][active]['positionHash']
        assert sum(obj.type=='CURVES' for obj in scene.objects)==1
        assert not bpy.data.libraries
        return proof,scene,carrier,gaze,data
    proof,scene,objects,body,gaze,rig=opened()
    carrier=objects[active]
    if reopen.exists():
        # The previous worker completed the independent native edit before the
        # render interruptions. Check the exact same input again without
        # rebuilding every temporary depsgraph during process recovery.
        independent=read_json(reopen)
        assert independent['source']==proof['source']
        data={label:positions(obj) for label,obj in objects.items()}
    else:
        data=verify(proof,scene,objects,body,gaze,rig)
        independent=read_json(reopen)
    for label,bank in data.items():
        assert array_hash(bank)==independent['replay'][label]['positionHash']
    for obj in list(scene.objects):
        if obj.type=='CURVES' and obj!=carrier:
            assert obj.hide_render
            geo=obj.data
            bpy.data.objects.remove(obj,do_unlink=True)
            if not geo.users:
                bpy.data.hair_curves.remove(geo)
    if reopen.exists():
        cache.mkdir(exist_ok=True)
        package,arrays=cache/'carrier.blend',cache/'positions.npz'
        bpy.context.preferences.filepaths.save_version=0
        bpy.ops.wm.save_as_mainfile(filepath=str(package),compress=True,copy=True)
        np.savez(arrays,**data)
        write_json(cache_proof,dict(source=proof['source'],packageSha256=digest(package),arraySha256=digest(arrays),
            carrier=carrier.name,stage='Transient single-carrier resume package with all scene dependencies used in the captures.'))
        print('R508_RENDER_CACHE',str(package),flush=True)
    return proof,scene,carrier,gaze,data


def main():
    proof,scene,carrier,gaze,data=render_source()
    active=proof['defaultVisible']
    hashes={mode:array_hash(bank) for mode,bank in data.items()}
    config=read_json(ROOT.parent/'r0477-hair-shader-isolation'/'material-probe.json')['view']
    scene.view_settings.view_transform=config['transform']
    scene.view_settings.look=config['look']
    scene.view_settings.exposure=config['exposure']
    for key,value in config['cycles'].items():
        setattr(scene.cycles,key,value)
    scene.render.use_persistent_data=False
    progress=ROOT/'preview-progress.json'
    shots=read_json(progress) if progress.exists() else {}
    recovered=len(shots)
    for key,row in shots.items():
        assert row['sourceSha256']==proof['source']['sha256']
        assert row['positionHash']==hashes[key.split(':',1)[0]]
        assert digest(Path(row['path']))==row['sha256']
    for name,view,angle,frame,blink in VIEWS:
        r500['activate'](scene,gaze,'separated',blink,frame)
        configure(scene,name,view,angle)
        for mode,bank in data.items():
            key=f'{mode}:{name}'
            if key in shots:
                continue
            set_positions(carrier,bank)
            position_hash=array_hash(evaluate(carrier))
            assert position_hash==hashes[mode]
            output=ROOT/f'{mode}-{name}.png'
            if output.exists():
                output.rename(output.with_name(f'{output.stem}-interrupted.png'))
            scene.render.filepath=str(output)
            start=perf_counter()
            bpy.ops.render.render(write_still=True)
            shots[key]=dict(path=str(output),sha256=digest(output),seconds=perf_counter()-start,
                sourceSha256=proof['source']['sha256'],positionHash=position_hash,frame=frame,blink=blink,
                hairMatrix=[list(row) for row in carrier.matrix_world],camera=[list(row) for row in scene.camera.matrix_world],
                lens=scene.camera.data.lens,exposure=scene.view_settings.exposure,samples=scene.cycles.samples,
                seed=scene.cycles.seed,resolution=[scene.render.resolution_x,scene.render.resolution_y],carrier=carrier.name)
            write_json(progress,shots)
            print('R508_PREVIEW',mode,name,round(shots[key]['seconds'],2),flush=True)
    set_positions(carrier,data[active])
    r500['activate'](scene,gaze,'separated',0.,1.)
    assert array_hash(evaluate(carrier))==hashes[active] and digest(Path(proof['source']['path']))==proof['source']['sha256']
    write_json(ROOT/'preview-receipt.json',dict(source=proof['source'],views=[item[0] for item in VIEWS],
        renders=shots,recoveredFrames=recovered,sameCarrierAndMaterials=True,sourceUnchanged=True))


if __name__=='__main__':
    main()

