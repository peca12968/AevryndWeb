"""Bounded native data preflight for a complete character rig and scalp follower."""
from pathlib import Path
import bpy,numpy as np,json,hashlib
R=Path(r'D:\Download\Aevrynd');D=R/'Reference/character/charmorph-vitruvian-cc0/r0069-rig-data';E=R/'Evidence/character-female-next/r0069-complete-controls'
def arr(data,key):
    a=np.empty(len(data)*3,'f4');data.foreach_get(key,a);return a.reshape(-1,3)
def main():
    m=json.loads((R/'engine/assets/characters/female-next/female-next.asset.json').read_text());source=R/'engine/assets/characters/female-next'/m['activeAuthoringStudySource'];assert hashlib.sha256(source.read_bytes()).hexdigest()==m['activeAuthoringStudySha256'];bpy.ops.wm.open_mainfile(filepath=str(source));names=list(json.loads((E.parent/'r0060-ocular-assembly/b-build-summary.json').read_text())['visibleComponents'].values());rows=[];V=np.zeros((37436,3));hits=np.zeros(37436,'i4')
    for name in names:
        o=bpy.data.objects[name];a=o.data.attributes['AFN60_NativeVertexID'];ids=np.empty(len(o.data.vertices),'i4');a.data.foreach_get('value',ids);P=arr(o.data.vertices,'co');A=np.array(o.matrix_world);P=P@A[:3,:3].T+A[:3,3];assert ids.min()>=0 and ids.max()<37436
        keys=o.data.shape_keys;assert keys.use_relative
        local=arr(keys.key_blocks[0].data,'co').astype('f8')
        for key in list(keys.key_blocks)[1:]:
            assert not key.vertex_group
            if key.value:local+=(arr(key.data,'co')-arr(key.relative_key.data,'co'))*key.value
        P=local@A[:3,:3].T+A[:3,3]
        for idx,co in zip(ids,P):V[idx]+=co;hits[idx]+=1
        rows.append({'name':name,'vertices':len(ids),'idRange':[int(ids.min()),int(ids.max())],'matrix':A.tolist(),'modifiers':[(x.name,x.type) for x in o.modifiers]})
    assert (hits>0).all();V/=hits[:,None];np.save(E/'native-rest-world.npy',V)
    curves=[]
    for o in bpy.context.scene.objects:
        if o.type=='CURVES':curves.append({'name':o.name,'hideRender':o.hide_render,'modifiers':[{'name':md.name,'type':md.type,'objects':[(n.name,n.inputs['Object'].default_value.name if n.inputs['Object'].default_value else None) for n in md.node_group.nodes if n.bl_idname=='GeometryNodeObjectInfo']} for md in o.modifiers if md.type=='NODES']})
    with bpy.data.libraries.load(str(D/'rigs.blend'),link=False) as (src,dst):dst.objects=src.objects
    rigs=[{'name':o.name,'type':o.type,'bones':[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'tail':list(b.tail_local),'deform':b.use_deform,'connected':b.use_connect} for b in o.data.bones] if o.type=='ARMATURE' else []} for o in dst.objects]
    result={'source':str(source),'sha256':m['activeAuthoringStudySha256'],'nativeMeshes':rows,'nativeVertexCoverage':int((hits>0).sum()),'nativeIdsDuplicated':int((hits>1).sum()),'curves':curves,'rawUnlinkedRigs':rigs,'noSourceCodeExecuted':True}
    (E/'rig-preflight.json').write_text(json.dumps(result,indent=2)+'\n');print('R69_PREFLIGHT',rows,curves,[(x['name'],len(x['bones'])) for x in rigs],flush=True)
if __name__=='__main__':main()
