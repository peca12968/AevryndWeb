"""Read only official hair reference licensing and donor-space geometry metadata."""
import bpy,json,hashlib
from pathlib import Path
import numpy as np
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0027-hair-redesign';E.mkdir(exist_ok=True);REF=R/'Reference/character/blender-hair-styles/hair_nodes-female_hair_styles.blend'
def main():
    bpy.ops.wm.open_mainfile(filepath=str(REF));texts={t.name:{'length':len(t.as_string()),'credit':'Daniel Bystedt. CC BY-SA license','exactVersionPresent':False,'fullOriginalNotesRemainInUnmodifiedPrivateReference':True} for t in bpy.data.texts if t.name=='Hair demo file info'};objects=[]
    for o in bpy.data.objects:
        if o.type not in ('MESH','CURVES'):continue
        if o.type=='MESH':P=np.array([o.matrix_world@v.co for v in o.data.vertices],np.float64)
        else:
            P=np.empty((len(o.data.points),3),np.float32);o.data.attributes['position'].data.foreach_get('vector',P.ravel());M=np.array(o.matrix_world,np.float64);P=P@M[:3,:3].T+M[:3,3]
        if not len(P):continue
        objects.append({'name':o.name,'type':o.type,'verticesOrPoints':len(P),'rawBoundsWorldM':[P.min(0).tolist(),P.max(0).tolist()],'matrixWorld':np.array(o.matrix_world).tolist(),'users':len(o.users_collection),'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers]})
    result={'reference':str(REF),'sha256':hashlib.sha256(REF.read_bytes()).hexdigest(),'embeddedLicenseInfo':texts,'objects':objects,'externalLibraries':[l.filepath for l in bpy.data.libraries],'readOnly':True};(E/'official-hair-reference-space.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps({'embeddedInfo':texts,'selectedObjects':[o for o in objects if o['name'] in ('long hair','long hair growth mesh','Head','head','head.001')]},indent=2),flush=True)
if __name__=='__main__':main()
