"""Render both actual rebuilt walls with the r500 comparison settings."""
from pathlib import Path
from runpy import run_path

import bpy

ROOT=Path(__file__).resolve().parent
model=run_path(str(ROOT/'author-r0503.py'))
stage,author=(model[k] for k in ('r500','author'))
read_json,write_json,digest=(model[k] for k in ('read_json','write_json','digest'))
activate=model['activate']
baseline_preview=run_path(str(model['BASELINE']/'preview-r0500.py'))


def main():
    proof=read_json(ROOT/'construction-receipt.json')
    parent=read_json(model['BASELINE']/'construction-receipt.json')
    baseline=read_json(model['BASELINE']/'preview-receipt.json')
    native=read_json(ROOT/'reopen-contact.json')
    source=Path(proof['source']['path'])
    assert digest(source)==proof['source']['sha256']
    assert native['source']==proof['source'] and proof['parent']==parent['source']
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
    scene=bpy.context.scene
    body,gaze=(bpy.data.objects[proof[k]] for k in ('body','gaze'))
    keys=body.data.shape_keys.key_blocks
    for mode,items in proof['variants'].items():
        for spec in items:
            assert stage['array_hash'](author['xyz'](keys[spec['key']].data))==spec['coordinateHash']
    hair=bpy.data.objects[proof['hair']['object']]
    assert stage['array_hash'](author['prior']['positions'](hair))==proof['hair']['positionHash']
    assert tuple(layer.name for layer in body.data.uv_layers)==tuple(proof['topology']['uvLayers'])
    rig=next(m.object for m in body.modifiers if m.type=='ARMATURE' and 'Head' in m.object.pose.bones)
    activate(scene,gaze,'rest',0.,1.)
    head0=rig.matrix_world@rig.pose.bones['Head'].matrix
    evaluation={}
    fold_witness=run_path(str(model['BASELINE']/'contact-r0500.py'))['fold_witness']
    fixed_normals={}
    for name,_,_,phase,_ in baseline_preview['VIEWS']:
        frame=37. if name.startswith('turned-') else 1.
        token=f'{frame:g}:{phase:g}'
        if token in evaluation:
            continue
        evaluation[token]={}
        for mode in model['MODES'][1:]:
            activate(scene,gaze,mode,phase,frame)
            hash_=stage['array_hash'](author['evaluated'](body))
            evaluation[token][mode]=dict(skinHash=hash_)
            if token=='1:1':
                fixed_normals[mode]=fold_witness(scene,body)
    assert all(d.is_valid for d in body.data.shape_keys.animation_data.drivers if 'R503' in d.data_path)
    capture=baseline_preview['capture']
    capture.__globals__.update(ROOT=ROOT,MODES=model['MODES'][1:],activate=activate)
    renders,recovered=capture(scene,body,gaze,proof['source'],evaluation,head0,rig)
    baseline_renders={}
    for name,_,_,_,_ in baseline_preview['VIEWS']:
        ref=baseline['renders'][f'separated:{name}']
        assert digest(Path(ref['path']))==ref['sha256']
        baseline_renders[name]=ref
        for mode in model['MODES'][1:]:
            row=renders[f'{mode}:{name}']
            for prop in ('phase','frame','camera','lens','exposure','crop'):
                assert row[prop]==ref[prop],(mode,name,prop)
    activate(scene,gaze,'rest',0.,1.)
    assert digest(source)==proof['source']['sha256']
    write_json(ROOT/'preview-receipt.json',dict(source=proof['source'],parent=proof['parent'],
        renders=renders,baseline=baseline_renders,recovered=recovered,evaluated=evaluation,
        fixedFrontalNormalSteps=fixed_normals, restored='rest:1:0'))


if __name__=='__main__':
    main()

