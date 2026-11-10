"""Minimum independent reopen and unchanged-identity checks for rejected studies."""
from pathlib import Path
from hashlib import file_digest,sha256
import json
import bpy
import numpy as np
ROOT=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return file_digest(f,'sha256').hexdigest()
def attr(data,name,dtype,shape,channel='value'):
    v=np.empty(shape,dtype=dtype);data.attributes[name].data.foreach_get(channel,v.ravel());return v

def main():
    receipt=read(ROOT/'volume-source-receipt.json');source=Path(receipt['source']['path'])
    assert sha(source)==receipt['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
    previous=read(ROOT.parent/'r0482-global-groom-separation/final-source-receipt.json')['branches']['B']
    data=bpy.data.objects['R484 complete hair | control'].data
    base=np.empty((24831,80,3),dtype='f4');data.position_data.foreach_get('vector',base.ravel())
    mesh=bpy.data.objects['R482 archived complete neutral skin'].data
    skin=np.empty((len(mesh.vertices),3),dtype='f4');mesh.vertices.foreach_get('co',skin.ravel())
    tri=np.asarray([p.vertices[:] for p in mesh.polygons],dtype='i4')
    obj=bpy.data.objects['AFN126_COMPLETE_WOMAN_BODY_AND_ARTIST_HEAD']
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());actual=ev.to_mesh()
    actual_skin=np.empty((len(actual.vertices),3),dtype='f4');actual.vertices.foreach_get('co',actual_skin.ravel())
    world=np.asarray(obj.matrix_world,dtype='f8');actual_skin=(actual_skin@world[:3,:3].T+world[:3,3]).astype('f4')
    fixture_error=float(np.linalg.norm(actual_skin-skin,axis=1).max()*1000.) if actual_skin.shape==skin.shape else None
    ev.to_mesh_clear()
    assert fixture_error is not None and fixture_error<.0006,fixture_error
    fields=(('radius','radiusHash','f4',(24831,80),'value'),('AFN409_CURVE_ID','curveIdHash','i4',24831,'value'),
        ('AFN409_POINT_ID','pointIdHash','i4',(24831,80),'value'),('AFN409_SKIN_TRIANGLE_ID','faceHash','i4',24831,'value'),
        ('AFN409_SKIN_BARYCENTRIC','baryHash','f4',(24831,3),'vector'),
        ('AEVRYND_ROOT_NORMAL_OFFSET','offsetHash','f4',24831,'value'),('AEVRYND_ROOT_OFFSET_LOCAL','localOffsetHash','f4',(24831,3),'vector'))
    rows={}
    for tag in ('control','A','B'):
        data=bpy.data.objects[f'R484 complete hair | {tag}'].data
        assert len(data.curves)==24831 and len(data.points)==1986480
        p=np.empty((24831,80,3),dtype='f4');data.position_data.foreach_get('vector',p.ravel())
        assert np.isfinite(p).all() and np.array_equal(p[:,0],base[:,0])
        assert sha256(p.tobytes()).hexdigest()==receipt['positionHashes'][tag]
        hashes={};values={}
        for name,key,dtype,shape,channel in fields:
            value=attr(data,name,dtype,shape,channel);values[name]=value;hashes[key]=sha256(value.tobytes()).hexdigest()
            assert hashes[key]==previous[key],(tag,name)
        face=values['AFN409_SKIN_TRIANGLE_ID'];bary=values['AFN409_SKIN_BARYCENTRIC'];local=values['AEVRYND_ROOT_OFFSET_LOCAL']
        points=skin[tri[face]].astype('f8');u=points[:,1]-points[:,0];u/=np.linalg.norm(u,axis=1,keepdims=True)
        n=np.cross(u,points[:,2]-points[:,0]);n/=np.linalg.norm(n,axis=1,keepdims=True);v=np.cross(n,u)
        root=(points*bary[:,:,None]).sum(1)+u*local[:,0,None]+v*local[:,1,None]+n*local[:,2,None]
        error=float(np.linalg.norm(root-p[:,0],axis=1).max()*1000.);assert error<.0006
        rows[tag]=dict(curves=len(data.curves),points=len(data.points),rootsBitIdentical=True,maxPhysicalRootReconstructionErrorMm=error,
            positionHash=receipt['positionHashes'][tag],unchangedFieldHashes=hashes,materials=[m.name for m in data.materials])
    external=[l.filepath for l in bpy.data.libraries]+[i.filepath for i in bpy.data.images if i.source=='FILE' and not i.packed_file]
    assert not external
    assert bpy.data.objects['AFN126_ORIGINAL_Hair_Hair_0'].hide_render
    stats=[dict(name=o.name,type=o.type,vertices=len(o.data.vertices) if o.type=='MESH' else None,
        faces=len(o.data.polygons) if o.type=='MESH' else None,bones=len(o.data.bones) if o.type=='ARMATURE' else None,
        shapeKeys=len(o.data.shape_keys.key_blocks) if o.type=='MESH' and o.data.shape_keys else 0,
        modifiers=[m.type for m in o.modifiers],hiddenFromRender=o.hide_render) for o in bpy.context.scene.objects]
    report=dict(source=receipt['source'],branches=rows,fixtureVsActualNeutralSkinMaxVertexErrorMm=fixture_error,
        externalDependencies=external,sceneObjectStatistics=stats,credits=[t.name for t in bpy.data.texts],
        activeMode='B (unaccepted)',minimumSignedClearanceMm=None,penetrationCount=None,
        contactStatus='NOT_TESTED_FOR_RECONSTRUCTED_STRANDS',dynamicStatus='NOT_TESTED_HAIR_IS_A_NEUTRAL_REST_STUDY',
        engineCPUTimeMs=None,engineGPUTimeMs=None,enginePeakMemoryBytes=None,
        scope='Actual same-woman neutral body, ocular parts and source controls are present. Hair rig/motion, expressions, clothing, collision and runtime gates are not passed.')
    (ROOT/'final-reopen-verification.json').write_bytes(json.dumps(report,indent=2).encode('utf8'))
    print(json.dumps(dict(source=receipt['source'],externalDependencies=external,fixtureVsActualNeutralSkinMaxVertexErrorMm=fixture_error,
        branchCount=len(rows),curveCountPerBranch=24831),indent=2),flush=True)

if __name__=='__main__':main()
