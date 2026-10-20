"""Reopen A/B/C exact archived sources and real source/own textures."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time
s=importlib.util.spec_from_file_location('history64',Path(__file__).with_name('verify-female-next-r0064-cards.py'));v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
E=v.E;R=v.base.R;M=R/'sites-engine-journey/assets-source/aevrynd-character/female-next'
def main():
    tick=time.time();bundle=v.read(E/'history-bundle.json')
    for f in bundle['files']:
        p=R/'sites-engine-journey'/f['file'];assert p.stat().st_size==f['bytes'] and v.base.sha(p)==f['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(v.base.SRC));names=list(v.read(E.parent/'r0060-ocular-assembly/b-build-summary.json')['visibleComponents'].values());before={n:v.v.mesh_signature(bpy.data.objects[n]) for n in names};results=[]
    for prefix in ('a','b','c'):
        ref=v.read(E/(prefix+'-build-summary.json'));p=M/Path(ref['output']).name;assert v.base.sha(p)==ref['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(p));assert before=={n:v.v.mesh_signature(bpy.data.objects[n]) for n in names};cards=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('AFN64_') and o.name.endswith('_CARD')];guides=[o for o in bpy.data.objects if o.type=='CURVE' and o.name.startswith('AFN64_') and o.name.endswith('_EDIT_GUIDE')];assert len(cards)==len(guides)==32;images=[]
        for im in bpy.data.images:
            if im.source=='FILE':
                target=Path(bpy.path.abspath(im.filepath));assert im.filepath.startswith('//') and target.exists();im.reload();images.append({'relative':im.filepath,'sha256':v.base.sha(target),'packed':bool(im.packed_file)})
        assert len(images)==(17 if prefix=='c' else 15);assert not bpy.data.libraries and not bpy.app.handlers.frame_change_pre and not bpy.app.handlers.frame_change_post
        if prefix=='c':
            for x in ref['textures']:
                target=Path(bpy.path.abspath(x['relative']));assert target.exists() and v.base.sha(target)==x['sha256']
        results.append({'source':str(p),'sha256':v.base.sha(p),'nativeGuides':32,'actualCards':32,'originalAnatomicalMeshesUVKeysMaterialsExact':True,'relativeTexturesLoaded':images,'acceptedCharacterOrDynamics':False})
    result={'status':'PASS_EXACT_THREE_SOURCE_HISTORY_REOPEN_NOT_CHARACTER_ACCEPTANCE','filesVerified':len(bundle['files']),'sources':results,'seconds':time.time()-tick};(E/'history-readback.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('R64_HISTORY_READBACK_PASS',len(results),time.time()-tick)
if __name__=='__main__':main()
