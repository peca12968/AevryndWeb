"""Reopen the saved grooms, exercise live strand controls, and capture matched views."""
from pathlib import Path
from runpy import run_path
from time import perf_counter

import bpy
import numpy as np
from mathutils import Matrix, Vector

ROOT=Path(__file__).resolve().parent
groom=run_path(str(ROOT/'author-r0505.py'))
old=groom['base']['old']
r500=groom['r500']
read_json,write_json,digest,positions,attribute,array_hash,set_positions=(
    groom[k] for k in ('read_json','write_json','digest','positions','attribute','array_hash','set_positions'))
VIEWS=(('rear','rear-oblique',None,0.),('opposite','portrait-profile',82.,0.),
       ('profile','portrait-profile',-82.,0.),('front','portrait-front',0.,0.),
       ('oblique','portrait-oblique',35.,0.),('crown','portrait-oblique',26.,0.),
       ('turn','portrait-oblique',9.,.75),('full-body','full-body',None,0.),('blink','portrait-oblique',32.,.75))


def evaluated(obj):
    bpy.context.view_layer.update()
    actual=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return positions(actual)


def fixed_fields(obj):
    return {a.name:array_hash(attribute(obj.data,a.name)) for a in obj.data.attributes
            if a.name!='position' and not a.name.startswith('AEVRYND_R505_')}


def show(scene,obj):
    for g in scene.objects:
        if g.type=='CURVES':
            g.hide_render=g!=obj
            g.hide_set(g!=obj)


def view_settings(scene,view,angle):
    r500['previous']['view_setup'](scene,view,angle)
    scene.render.use_border=scene.render.use_crop_to_border=False


def top_camera(scene):
    position=Vector((.192,-.455,1.796))
    target=Vector((0.,-.030,1.533))
    rotation=(target-position).to_track_quat('-Z','Y')
    scene.camera.matrix_world=Matrix.Translation(position)@rotation.to_matrix().to_4x4()
    scene.camera.data.lens=67.
    scene.camera.data.type='PERSP'


def main():
    proof=read_json(ROOT/'construction-receipt.json')
    source=Path(proof['source']['path'])
    assert digest(source)==proof['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
    scene=bpy.context.scene
    carrier=bpy.data.objects[proof['variants'][proof['defaultVisible']]['object']]
    assert carrier==bpy.context.view_layer.objects.active and not carrier.hide_get() and not carrier.hide_render
    control=bpy.data.objects[proof['controlObject']]
    scalp=bpy.data.objects[proof['scalp']]
    skin,gaze=(bpy.data.objects[proof[k]] for k in ('body','gaze'))
    body_author=r500['author']
    assert array_hash(body_author['xyz'](skin.data.shape_keys.reference_key.data))==proof['sourceBasisHash']
    assert array_hash(body_author['xyz'](skin.data.shape_keys.key_blocks[r500['previous']['KEY_NAMES']['orbital']].data))==proof['sourceCheekHash']
    base=positions(control)
    assert array_hash(base)==proof['controlPositionHash']
    binding=old['foundation']['binding_frame'](control,scalp,base[:,0])[2]
    fixed=fixed_fields(control)
    data={'control':base}
    attachments={}
    masks={}
    for label,info in proof['variants'].items():
        obj=bpy.data.objects[info['object']]
        assert fixed_fields(obj)==fixed
        assert tuple(obj.data.materials)==tuple(control.data.materials)
        assert obj.data.surface==control.data.surface
        assert obj.parent and obj.parent.name==proof['rig'] and obj.parent_type=='BONE' and obj.parent_bone=='Head'
        assert np.max(abs(np.asarray(obj.matrix_world)-np.asarray(control.matrix_world)))<3e-7
        show(scene,obj)
        bank=evaluated(obj)
        assert array_hash(bank)==info['positionHash'] and np.array_equal(bank[:,0],base[:,0])
        assert array_hash(attribute(obj.data,'AEVRYND_R505_BRIDGE_LAYER'))==info['familyHash']
        assert array_hash(attribute(obj.data,'AEVRYND_R505_BRIDGE_WEIGHT'))==info['weightHash']
        rear=attribute(obj.data,'AEVRYND_REAR_BLEND_GROUP')>=0
        assert np.array_equal(bank[rear],base[rear])
        start=attribute(obj.data,'AEVRYND_R505_BRIDGE_START')
        assert array_hash(start)==info['startHash']
        protected=np.arange(bank.shape[1])[None,:]<=start[:,None]
        assert np.array_equal(bank[protected],base[protected])
        assert np.isfinite(bank).all()
        data[label]=bank
        masks[label]=np.flatnonzero(np.any(bank!=base,axis=(1,2)))
        attachments[label]=dict(evalHash=array_hash(bank),rootHash=array_hash(bank[:,0]),rearCount=int(rear.sum()),
            strands=len(bank),pointsPerCurve=bank.shape[1])
    # Edit real stored control points on the visible candidate and restore.
    show(scene,carrier)
    selected=masks[proof['defaultVisible']]
    chosen=selected[:24]
    assert len(chosen)==24
    original=data[proof['defaultVisible']]
    edited=original.copy()
    edited[chosen,25:47,1]+= .0023*np.sin(np.linspace(0,np.pi,22))
    set_positions(carrier,edited)
    edited_hash=array_hash(evaluated(carrier))
    assert edited_hash==array_hash(edited) and edited_hash!=array_hash(original)
    set_positions(carrier,original)
    restore=array_hash(evaluated(carrier))
    assert restore==array_hash(original)
    ids=attribute(carrier.data,'AFN409_CURVE_ID')
    ears=read_json(ROOT/'ear-join-probe.json')['ears']
    assigned=attribute(control.data,'AEVRYND_R504_TEMPLE_GROUP')>=0
    xy,index=groom['survey']['crossing'](base,(ears[0]['top']+ears[0]['bottom'])*.5)
    cohorts=[]
    for side in (-1,1):
        for lo in (.024,.034):
            members=assigned&(index>=0)&(base[:,0,0]*side>0)&(xy[:,1]>=lo)&(xy[:,1]<lo+.010)
            cohorts.append(dict(side=side,lowerYMillimetres=lo*1000.,curves=int(members.sum()),
                medianTipHeightMm={name:float(np.median(bank[members,-1,2])*1000.) for name,bank in data.items()}))
    operation=dict(object=carrier.name,curveIDs=ids[chosen].tolist(),controlRange=[25,46],maximumEditYMetres=.0023,
                   editedHash=edited_hash,restoredHash=restore,sourceWrite=False)
    rig=bpy.data.objects[proof['rig']]
    head0=rig.matrix_world@rig.pose.bones['Head'].matrix
    rest_matrix=carrier.matrix_world.copy()
    r500['activate'](scene,gaze,'separated',.75,37.)
    target=(rig.matrix_world@rig.pose.bones['Head'].matrix)@head0.inverted()@rest_matrix
    error=float(np.max(np.abs(np.asarray(carrier.matrix_world)-np.asarray(target))))
    assert error<3e-6,error
    pose_receipt=dict(frame=37,headTransformMaxDifference=error,
        neutralMatrix=[list(row) for row in rest_matrix],
        turnedMatrix=[list(row) for row in carrier.matrix_world])
    r500['activate'](scene,gaze,'separated',0.,1.)
    assert np.max(np.abs(np.asarray(carrier.matrix_world)-np.asarray(rest_matrix)))<3e-7
    libraries=[item.filepath for item in bpy.data.libraries]
    external=[item.filepath for item in bpy.data.images if item.source=='FILE' and not item.packed_file]
    assert not libraries and not external
    meshes=[obj for obj in scene.objects if obj.type=='MESH']
    for obj in meshes:
        obj.data.calc_loop_triangles()
    stats=dict(vertices=sum(len(obj.data.vertices) for obj in meshes),
        triangles=sum(len(obj.data.loop_triangles) for obj in meshes),
        bones=sum(len(obj.data.bones) for obj in scene.objects if obj.type=='ARMATURE'),
        morphs=sum(len(obj.data.shape_keys.key_blocks)-1 for obj in meshes if obj.data.shape_keys),
        materials=len(bpy.data.materials),images=len(bpy.data.images),curvesPerGroom=len(base),pointsPerGroom=int(base.shape[0]*base.shape[1]))
    write_json(ROOT/'reopen-verification.json',dict(source=proof['source'],parent=proof['parent'],attributes=fixed,
        verifiedVariants=attachments,operation=operation,bindingMaximumErrorMetres=binding,externalImages=external,
        libraries=libraries,stats=stats,headOperation=pose_receipt,fixedTipCohorts=cohorts))
    # Keep one carrier with identical material and radius for all three renders.
    for obj in list(scene.objects):
        if obj.type=='CURVES' and obj!=carrier:
            mesh=obj.data
            bpy.data.objects.remove(obj,do_unlink=True)
            if not mesh.users:
                bpy.data.hair_curves.remove(mesh)
    config=read_json(ROOT.parent/'r0477-hair-shader-isolation/material-probe.json')['view']
    scene.view_settings.view_transform=config['transform']
    scene.view_settings.look=config['look']
    scene.view_settings.exposure=config['exposure']
    for k,v in config['cycles'].items():
        setattr(scene.cycles,k,v)
    scene.render.use_persistent_data=False
    progress=ROOT/'preview-progress.json'
    shots=read_json(progress) if progress.exists() else {}
    recovered=len(shots)
    for key,row in shots.items():
        mode=key.split(':')[0]
        assert row['sourceSha256']==proof['source']['sha256'] and row['positionHash']==array_hash(data[mode])
        assert digest(Path(row['path']))==row['sha256']
    for name,view,angle,blink in VIEWS:
        frame=37. if name=='turn' else 1.
        r500['activate'](scene,gaze,'separated',blink,frame)
        view_settings(scene,view,angle)
        if name=='crown':
            top_camera(scene)
        for mode,bank in data.items():
            key=f'{mode}:{name}'
            if key in shots:
                continue
            set_positions(carrier,bank)
            h=array_hash(evaluated(carrier))
            assert h==array_hash(bank)
            output=ROOT/f'{mode}-{name}.png'
            if output.exists():
                output.rename(output.with_name(f'{output.stem}-interrupted.png'))
            scene.render.filepath=str(output)
            now=perf_counter()
            bpy.ops.render.render(write_still=True)
            shots[key]=dict(sourceSha256=proof['source']['sha256'],path=str(output),sha256=digest(output),
                seconds=perf_counter()-now,positionHash=h,carrier=carrier.name,blink=blink,frame=frame,carrierMatrix=[list(row) for row in carrier.matrix_world],
                camera=[list(row) for row in scene.camera.matrix_world],lens=scene.camera.data.lens,
                exposure=scene.view_settings.exposure,seed=scene.cycles.seed)
            write_json(progress,shots)
            print('R505_PREVIEW',mode,name,flush=True)
    set_positions(carrier,original)
    r500['activate'](scene,gaze,'separated',0.,1.)
    assert array_hash(evaluated(carrier))==restore and digest(source)==proof['source']['sha256']
    write_json(ROOT/'preview-receipt.json',dict(source=proof['source'],views=len(VIEWS),renders=shots,
        recoveredFrames=recovered,sameCarrierAndMaterials=True,restoredSourceUnchanged=True))


if __name__=='__main__':
    main()

