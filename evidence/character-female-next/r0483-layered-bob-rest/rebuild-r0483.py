"""Rebuild rejected r483 geometry from the standalone archived r482 source."""
from argparse import ArgumentParser
from pathlib import Path
from hashlib import file_digest,sha256
from runpy import run_path
import json
import sys
import bpy
import numpy as np

def digest(path):
    with path.open('rb') as f:return file_digest(f,'sha256').hexdigest()

def main():
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('--parent',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    folder=Path(__file__).resolve().parent
    receipt=json.loads((folder/'draft-receipt.json').read_text(encoding='utf8'))
    assert digest(args.parent)==receipt['parent']['sha256']
    assert not args.out.exists()
    methods=run_path(str(folder/'author-r0483.py'))
    bpy.ops.wm.open_mainfile(filepath=str(args.parent),load_ui=False,use_scripts=False)
    original=bpy.data.objects['R482 complete groom | B'].data
    base=np.empty((24831,80,3),dtype='f4');original.position_data.foreach_get('vector',base.ravel())
    ids=np.empty(24831,dtype='i4');original.attributes['AFN409_CURVE_ID'].data.foreach_get('value',ids)
    objects={};old=[];hashes={}
    for tag in ('base','A','B'):
        obj=bpy.data.objects[f'R482 complete groom | {tag}'];old.append(obj.data)
        obj.data=original.copy();obj.name=f'R483 complete groom | {tag}';obj.data.name=f'R483 native curves | {tag}'
        q=base.copy() if tag=='base' else methods['strand_shape'](base,ids,tag)[0]
        hashes[tag]=sha256(q.tobytes()).hexdigest()
        assert hashes[tag]==receipt['neutralPositionHash'][tag]
        obj.data.position_data.foreach_set('vector',q.ravel());obj.data.update_tag();obj.update_tag()
        obj.color=(.20,.065,.022,1.);obj.hide_render=tag!='A';obj.hide_set(tag!='A');objects[tag]=obj
    for data in old:
        if data.users==0:bpy.data.hair_curves.remove(data)
    body=bpy.data.objects['R482 archived complete neutral skin'];body.name='R483 complete neutral skin'
    body.color=(.62,.47,.38,1.)
    uv=methods['attachment_atlas'](body,objects)
    assert uv==receipt['attachmentUVHashes']
    bpy.ops.object.select_all(action='DESELECT');objects['A'].select_set(True)
    bpy.context.view_layer.objects.active=objects['A']
    bpy.context.scene['R483_WorkingStatus']='Rejected appearance study. Rebuilt free lengths have no collision or motion certification.'
    text=bpy.data.texts.new('Aevrynd_R483_Replay_Provenance')
    text.write('R483 replay from archived r482 source. Retain all inherited author and license notices. Graduated free lengths and diagonal crown flow were visually rejected. No native brush operation, complete-character acceptance or runtime integration is claimed.\n')
    bpy.ops.wm.save_as_mainfile(filepath=str(args.out),compress=True,copy=True)
    bpy.ops.wm.open_mainfile(filepath=str(args.out),load_ui=False,use_scripts=False)
    for tag,expected in hashes.items():
        data=bpy.data.objects[f'R483 complete groom | {tag}'].data
        q=np.empty((len(data.points),3),dtype='f4');data.position_data.foreach_get('vector',q.ravel())
        assert sha256(q.tobytes()).hexdigest()==expected
    report=dict(parent=dict(path=str(args.parent),sha256=digest(args.parent)),output=dict(path=str(args.out),sha256=digest(args.out)),
        allGeometryHashesExactlyMatch=hashes,attachmentUVHashesExactlyMatch=uv,sourceFileByteEquivalenceClaimed=False,
        scope='Geometry reproduction only. Not a new candidate or collision/motion/appearance acceptance.')
    args.out.with_suffix('.replay.json').write_bytes(json.dumps(report,indent=2).encode('utf8'))
    print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':main()
