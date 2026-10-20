"""Bounded actual oral component and native jaw-expression inspection."""
from pathlib import Path
import bpy,numpy as np,json,hashlib
R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0074-oral-controls';D=R/'Reference/character/charmorph-vitruvian-cc0'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    src=S/'aevrynd-female-next-r0069-a-complete-controls-study.blend';assert sha(src)=='f358d3c5a4d00ee6ad94d324612b33bdcf5aa4dde0bb19382d72bc7afabbb667'
    bpy.ops.wm.open_mainfile(filepath=str(src));bpy.context.scene.frame_set(1)
    o=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING'];d=o.data;ids=np.empty(len(d.vertices),'i4');d.attributes['AFN60_NativeVertexID'].data.foreach_get('value',ids)
    b=np.array([v.co[:] for v in d.shape_keys.key_blocks[0].data]);v=b.copy()
    for k in d.shape_keys.key_blocks[1:]:v+=(np.array([p.co[:] for p in k.data])-b)*k.value
    a=np.array(o.matrix_world);w=v@a[:3,:3].T+a[:3,3]
    z=np.load(D/'r0074-oral-controls/Jaw_Lower.npz',allow_pickle=False);delta=np.zeros((37436,3));delta[z['idx']]=z['delta'];assert np.isfinite(delta).all()
    parent=list(range(len(v)))
    def root(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for edge in d.edges:
        u,vv=edge.vertices;u=root(u);vv=root(vv)
        if u!=vv:parent[vv]=u
    groups={}
    for i in range(len(v)):groups.setdefault(root(i),[]).append(i)
    comps=[]
    for values in groups.values():
        vv=np.array(values);mask=np.zeros(len(v),bool);mask[vv]=True;faces=[p.index for p in d.polygons if mask[p.vertices[0]]];materials={}
        for i in faces:
            p=d.polygons[i];n=d.materials[p.material_index].name;materials[n]=materials.get(n,0)+1
        dd=delta[ids[vv]]@a[:3,:3].T
        comps.append({'vertices':len(vv),'faces':len(faces),'materials':materials,'worldBoundsM':[w[vv].min(0).tolist(),w[vv].max(0).tolist()],'worldCentroidM':w[vv].mean(0).tolist(),'nativeIDs':ids[vv].tolist(),'nativeFaceIDs':[d.attributes['AFN60_NativeFaceID'].data[i].value for i in faces],'jawAffectedVertices':int((np.linalg.norm(dd,axis=1)>1e-9).sum()),'jawMaximumWorldDeltaM':float(np.linalg.norm(dd,axis=1).max()),'jawMeanWorldDeltaM':dd.mean(0).tolist()})
    comps.sort(key=lambda x:-x['vertices'])
    result={'source':str(src),'sha256':sha(src),'components':comps,'keys':[{'name':k.name,'value':k.value} for k in d.shape_keys.key_blocks],'modifiers':[{'name':x.name,'type':x.type} for x in o.modifiers],'nativeExpressionSourceSHA256':sha(D/'r0074-oral-controls/Jaw_Lower.npz'),'nativeVertexCount':37436,'noLayerOrContactAcceptance':True}
    (E/'native-oral-preflight.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    for c in comps:print(json.dumps({k:v for k,v in c.items() if k not in ('nativeIDs','nativeFaceIDs')}),flush=True)
    print('KEYS',result['keys'],'MODIFIERS',result['modifiers'],flush=True)
    with bpy.data.libraries.load(str(D/'canonical-female-data.blend'),link=False) as (src,dst):dst.objects=src.objects
    for obj in dst.objects:
        if obj and obj.type=='MESH':print('SOURCE_GROUPS',obj.name,[g.name for g in obj.vertex_groups],flush=True)
    for name in ('Jaw_Lower','Mouth_Large_Opened','Tongue_Up'):
        z=np.load(D/'r0074-oral-controls'/(name+'.npz'),allow_pickle=False);delta=np.zeros((37436,3));delta[z['idx']]=z['delta'];dd=delta[ids]@a[:3,:3].T;active=np.linalg.norm(dd,axis=1)>1e-8
        print('MORPH',name,'affected',int(active.sum()),'deltaRange',dd.min(0).tolist(),dd.max(0).tolist(),'bounds',w[active].min(0).tolist(),w[active].max(0).tolist(),flush=True)
if __name__=='__main__':main()
