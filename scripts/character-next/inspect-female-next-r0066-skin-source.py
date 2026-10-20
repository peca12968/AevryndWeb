"""Read-only comparison of working and source-authored skin semantics."""
from pathlib import Path
import bpy, numpy as np, json, importlib.util, hashlib, time
R=Path(r'D:\Download\Aevrynd'); S=R/'engine/assets/characters/female-next/source'; E=R/'Evidence/character-female-next/r0066-skin-response'; E.mkdir(parents=True,exist_ok=True)
SRC=S/'aevrynd-female-next-r0065-a-inner-eye-diffuse-study.blend'
SOURCE_SHA='4d0e3f67735ae68c5c1fa3c933f7cabb03cb547928e778f7067a8e699620b708'
def module(n,p):
    spec=importlib.util.spec_from_file_location(n,Path(__file__).with_name(p)); m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
d=module('skin66diag','inspect-female-next-r0065-eye-shading.py')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,v):(E/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def images():
    rows=[]
    for im in bpy.data.images:
        if not any(v in im.name for v in ('Light_Skin_Color','Skin_Roughness','Skin_Height')):continue
        row={'name':im.name,'path':im.filepath,'colorspace':im.colorspace_settings.name,'size':list(im.size),'source':im.source}
        if '1001' in im.name:
            a=np.empty(len(im.pixels),dtype='f4');im.pixels.foreach_get(a);a=a.reshape(-1,4)
            row['rgbaQuantiles']=np.quantile(a,[0,.01,.1,.5,.9,.99,1],axis=0).tolist();row['nonfinite']=int((~np.isfinite(a)).sum())
        rows.append(row)
    return rows
def main():
    tick=time.time();assert sha(SRC)==SOURCE_SHA;bpy.ops.wm.open_mainfile(filepath=str(SRC))
    current={'path':str(SRC),'sha256':sha(SRC),'skinGraph':d.tree(bpy.data.materials['AFN57_CANONICAL_SKIN'].node_tree),'skinImages':images(),'sceneScale':bpy.context.scene.unit_settings.scale_length}
    native=R/'Reference/character/charmorph-vitruvian-cc0/char.blend';bpy.ops.wm.open_mainfile(filepath=str(native))
    original={'path':str(native),'sha256':sha(native),'materials':{},'groups':{},'images':[{'name':i.name,'path':i.filepath,'colorspace':i.colorspace_settings.name,'size':list(i.size),'source':i.source} for i in bpy.data.images],'objectScales':{o.name:list(o.scale) for o in bpy.data.objects if o.type=='MESH'}}
    for m in bpy.data.materials:
        if m.use_nodes:original['materials'][m.name]=d.tree(m.node_tree)
    for group in bpy.data.node_groups:
        if any(x in group.name.lower() for x in ('skin','bump','rough','material','principled')):original['groups'][group.name]=d.tree(group)
    save('source-material-diagnosis.json',{'working':current,'original':original,'seconds':time.time()-tick,'sourceFilesModified':False});print('R66_SKIN_SOURCE_DIAGNOSIS',list(original['materials']),time.time()-tick,flush=True)
if __name__=='__main__':main()
