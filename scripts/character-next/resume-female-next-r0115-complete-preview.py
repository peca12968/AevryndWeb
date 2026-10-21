"""Resume the already authored full candidate; repair storage/relative images only."""
from pathlib import Path
import bpy,json,hashlib,time,datetime,importlib.util,os
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0115-native-continuous-neck'
TMP=Path('C:/Users/USER/AppData/Local/Temp/aevrynd-female-next-r0115-a-continuous-native-woman.blend')
OUT=S/'r0115-source/aevrynd-female-next-r0115-a-continuous-native-woman.blend'
sp=importlib.util.spec_from_file_location('r115resume',Path(__file__).with_name('build-female-next-r0113-native-neck-character.py'));b=importlib.util.module_from_spec(sp);sp.loader.exec_module(b);b.u.v.E=E
def save(n,o):(E/n).write_text(json.dumps(o,indent=2)+'\n',encoding='utf-8',newline='\n')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    tick=time.time();assert TMP.is_file() and not OUT.exists();digest=sha(TMP);bpy.ops.wm.open_mainfile(filepath=str(TMP));images=[]
    for im in bpy.data.images:
        if im.source=='FILE' and not im.packed_file and im.filepath:
            old=im.filepath
            p=S/old.removeprefix('//') if old.startswith('//') else Path(old)
            assert p.is_file(),(im.name,old,str(p));rel=p.relative_to(S).as_posix();im.filepath=str(p);im.reload();images.append({'name':im.name,'canonicalTexture':str(p),'sourceSha256':sha(p),'oldRelative':old,'newRelative':'//../'+rel});im.filepath='//../'+rel
    b.deliver(0);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=False)
    assert sha(TMP)==digest
    for im in bpy.data.images:
        if im.source=='FILE' and not im.packed_file and im.filepath:assert Path(bpy.path.abspath(im.filepath)).is_file(),im.filepath
    actual=Path('C:/Users/USER/.cache/aevrynd-character-source/r0115')/OUT.name;archive=R/'sites-engine-journey/assets-source/aevrynd-character/female-next/r0115-source'/OUT.name
    assert os.path.samefile(OUT,actual) and os.path.samefile(OUT,archive)
    save('complete-source-save.json',{'canonicalSource':str(OUT),'physicalCompleteSource':str(actual),'archiveCompleteSource':str(archive),'originalFailedCapacitySavePreserved':str(TMP),'originalFailedCapacitySaveSha256':digest,'bytes':OUT.stat().st_size,'sha256':sha(OUT),'sourceAndArchiveSameCompleteFileViaTwoDirectoryJunctions':True,'relativeTextureFoldersWorkAtSourceAndArchiveDepth':True,'originalSameRoundStartAndDeadlinesNotReset':True,'storageAndImagePathRepairOnlyNoNewShapeCandidate':True,'images':images,'resumeUTC':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    summary=json.loads((E/'a-build-summary.json').read_text(encoding='utf-8'));summary['output']=str(OUT);summary['completeSourceSave']='complete-source-save.json';save('a-build-summary.json',summary)
    views=[]
    for view in ['face','body-face','profile','back']:
        views.append(b.u.v.image('a-continuous-native-woman',view));save('a-view-controls.json',views)
    for label,value in [('half',.5),('closed',1.),('restored',0.)]:
        b.deliver(value);views.append(b.u.v.image('a-continuous-native-woman-'+label,'face'));save('a-view-controls.json',views)
    print('R115_CONTINUOUS_NATIVE_COMPLETE_WOMAN_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
