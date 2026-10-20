"""Bounded native-index/affected-region check of actual CC0 sculpt data."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util
from mathutils import Vector
from mathutils.kdtree import KDTree
sp=importlib.util.spec_from_file_location('form72rig',Path(__file__).with_name('build-female-next-r0069-complete-controls.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
R=m.R;E=R/'Evidence/character-female-next/r0072-craniofacial-form';D=R/'Reference/character/charmorph-vitruvian-cc0';SRC=m.S/'aevrynd-female-next-r0069-a-complete-controls-study.blend'
def main():
    assert m.sha(SRC)=='f358d3c5a4d00ee6ad94d324612b33bdcf5aa4dde0bb19382d72bc7afabbb667';bpy.ops.wm.open_mainfile(filepath=str(SRC));bpy.context.scene.frame_set(1)
    P=np.load(D/'Default.npy',allow_pickle=False);V=np.zeros_like(P);ids_seen=[];objects={};mapping={}
    for name in m.native_names():
        o=bpy.data.objects[name];ids=np.empty(len(o.data.vertices),'i4');o.data.attributes['AFN60_NativeVertexID'].data.foreach_get('value',ids);base=np.array([p.co[:] for p in o.data.shape_keys.key_blocks[0].data]);error=float(np.linalg.norm(base-P[ids],axis=1).max());assert error<1e-7
        q=base.copy()
        for key in o.data.shape_keys.key_blocks[1:]:q+=(np.array([p.co[:] for p in key.data])-base)*key.value
        A=np.array(o.matrix_world);V[ids]=q@A[:3,:3].T+A[:3,3];mapping[name]=ids;ids_seen.extend(ids.tolist());objects[name]={'vertices':len(ids),'canonicalBasisMaximumErrorM':error}
    assert sorted(ids_seen)==list(range(37436));tree=KDTree(len(V))
    for i,p in enumerate(V):tree.insert(Vector(p),i)
    tree.balance();rows=[]
    for file in ('Cheeks_BoneDefinition','Face_Zygomatic_Bone','Jaw_Definition','Face_Maxilla'):
        z=np.load(D/'r0072-facial-form/morphs/L2'/(file+'.npz'),allow_pickle=False);delta=np.zeros_like(P);delta[z['idx']]=z['delta'];active=np.linalg.norm(delta,axis=1)>1e-10;row={'morph':file,'path':str(D/'r0072-facial-form/morphs/L2'/(file+'.npz')),'affectedNativeVertices':int(active.sum()),'maximumNativeDeltaM':float(np.linalg.norm(delta,axis=1).max()),'affectedWorldBoundsM':[V[active].min(0).tolist(),V[active].max(0).tolist()],'components':{},'facialHelpers':{}}
        for name,ids in mapping.items():
            x=np.linalg.norm(delta[ids],axis=1);row['components'][name]={'affectedVertices':int((x>1e-10).sum()),'maximumNativeDeltaM':float(x.max())}
        body=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING'];ids=mapping[body.name];roles={}
        for face in body.data.polygons:
            if any(active[ids[i]] for i in face.vertices):
                n=body.data.materials[face.material_index].name;roles[n]=roles.get(n,0)+1
        row['affectedIncidentBodyFaceMaterials']=roles
        for name in ('AFN59_LASHES_NATIVE_POINT_POSES','AFN59_BROWS_NATIVE_POINT_POSES'):
            o=bpy.data.objects[name];arr=np.array([p.co[:] for p in o.data.shape_keys.key_blocks[0].data]);A=np.array(o.matrix_world);world=arr@A[:3,:3].T+A[:3,3];nearest=np.array([tree.find(Vector(p))[1] for p in world]);x=np.linalg.norm(delta[nearest],axis=1);row['facialHelpers'][name]={'nearestNativeNonzeroDeltaPoints':int((x>1e-10).sum()),'maximumNativeDeltaM':float(x.max())}
        rows.append(row)
    (E/'native-morph-preflight.json').write_text(json.dumps({'source':str(SRC),'sourceSha256':m.sha(SRC),'nativeVertexCount':37436,'allNativeIDsUniqueCovered':True,'objects':objects,'morphs':rows,'noAppearanceOrContactAcceptance':True},indent=2),encoding='utf8')
    for row in rows:print(json.dumps(row),flush=True)
if __name__=='__main__':main()
