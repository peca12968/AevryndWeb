"""Reopen both exact archived Blender files with their relative textures."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0063-layered-crop';M=R/'sites-engine-journey/assets-source/aevrynd-character/female-next'
sp=importlib.util.spec_from_file_location('history63read',Path(__file__).with_name('verify-female-next-r0063-crop.py'));v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v);g=v.g;k=v.k
def read(p):return json.loads(p.read_text(encoding='utf8'))
def main():
    tick=time.time();bundle=read(E/'history-bundle.json')
    for f in bundle['files']:
        p=R/'sites-engine-journey'/f['file'];assert p.stat().st_size==f['bytes'] and v.m.sha(p)==f['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(v.m.SRC));names=list(read(E.parent/'r0060-ocular-assembly/b-build-summary.json')['visibleComponents'].values());base={n:v.v.mesh_signature(bpy.data.objects[n]) for n in names};stage=k.f.v.stage();results=[]
    for number,name,N,npz in [('0062','AFN62_ACTUAL_PACKED_SHAFTS',128,E.parent/'r0062-packed-bundle/a-packed-bundle-authoring.npz'),('0063',v.m.NAME,72,E/'a-crop-authoring.npz')]:
        summary=read(E.parent/('r0062-packed-bundle' if number=='0062' else 'r0063-layered-crop')/'a-build-summary.json');p=M/Path(summary['output']).name;assert v.m.sha(p)==summary['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(p));assert base=={n:v.v.mesh_signature(bpy.data.objects[n]) for n in names};now=k.f.v.stage();assert now['lights']==stage['lights']
        for key in ('transform','look','exposure','gamma','world'):assert now['config'][key]==stage['config'][key]
        o=bpy.data.objects[name];d=o.data;Q=np.empty(len(d.position_data)*3,'f4');d.position_data.foreach_get('vector',Q);rr=np.empty(len(d.position_data),'f4');d.attributes['radius'].data.foreach_get('value',rr);raw=np.load(npz);assert np.array_equal(Q,raw['positions'].ravel()) and np.array_equal(rr,raw['radii'].ravel());assert all(c.points_length==N for c in d.curves)
        images=[]
        for im in bpy.data.images:
            if im.source=='FILE':
                path=Path(bpy.path.abspath(im.filepath));assert im.filepath.startswith('//') and path.exists();im.reload();images.append({'relative':im.filepath,'sha256':v.m.sha(path)})
        assert len(images)==15 and not bpy.data.libraries and not bpy.app.handlers.frame_change_pre and not bpy.app.handlers.frame_change_post
        results.append({'source':str(p),'sha256':v.m.sha(p),'actualCurves':len(d.curves),'pointsPerCurve':N,'positionsRadiiExactlyAuthoring':True,'originalBodyOpticalMeshesKeysUVMaterialsExact':True,'relativeTexturesLoaded':images,'noExternalLibrariesOrHandlers':True,'acceptedCharacterOrMotion':False})
    result={'status':'PASS_EXACT_HISTORY_REOPEN_NOT_CHARACTER_ACCEPTANCE','fileCountVerified':len(bundle['files']),'sources':results,'seconds':time.time()-tick};(E/'history-readback.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('R63_HISTORY_REOPEN_PASS',len(results),time.time()-tick)
if __name__=='__main__':main()
