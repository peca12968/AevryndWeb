"""Reopen and verify r483 drafts without modifying or promoting them."""
from pathlib import Path
from hashlib import file_digest, sha256
import json
import bpy
import numpy as np

ROOT=Path(__file__).resolve().parent

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def digest(path):
    with path.open('rb') as stream:
        return file_digest(stream,'sha256').hexdigest()

def attr(data,name,dtype,shape,channel='value'):
    value=np.empty(shape,dtype=dtype)
    data.attributes[name].data.foreach_get(channel,value.ravel())
    return value

def main():
    receipt=read(ROOT/'draft-receipt.json')
    parent=read(ROOT.parent/'r0482-global-groom-separation'/'final-source-receipt.json')
    source=Path(receipt['source']['path'])
    assert digest(source)==receipt['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
    body=bpy.data.objects['R483 complete neutral skin'];mesh=body.data
    skin=np.empty((len(mesh.vertices),3),dtype='f4');mesh.vertices.foreach_get('co',skin.ravel())
    triangles=np.asarray([polygon.vertices[:] for polygon in mesh.polygons],dtype='i4')
    uv=np.empty((len(mesh.loops),2),dtype='f4')
    mesh.uv_layers['R483 Scalp Attachment Atlas'].data.foreach_get('uv',uv.ravel())
    uv=uv.reshape(-1,3,2)
    baseline=np.load(ROOT/'shape-base.npz',allow_pickle=False)['position']
    fields=(('radius','radiusHash','f4',(24831,80),'value'),
            ('AFN409_CURVE_ID','curveIdHash','i4',24831,'value'),
            ('AFN409_POINT_ID','pointIdHash','i4',(24831,80),'value'),
            ('AFN409_SKIN_TRIANGLE_ID','faceHash','i4',24831,'value'),
            ('AFN409_SKIN_BARYCENTRIC','baryHash','f4',(24831,3),'vector'),
            ('AEVRYND_ROOT_NORMAL_OFFSET','offsetHash','f4',24831,'value'),
            ('AEVRYND_ROOT_OFFSET_LOCAL','localOffsetHash','f4',(24831,3),'vector'))
    results={}
    for tag in ('base','A','B'):
        obj=bpy.data.objects[f'R483 complete groom | {tag}'];data=obj.data
        assert len(data.curves)==24831 and len(data.points)==24831*80
        q=np.empty((24831,80,3),dtype='f4');data.position_data.foreach_get('vector',q.ravel())
        assert np.isfinite(q).all() and np.array_equal(q[:,0],baseline[:,0])
        assert sha256(q.tobytes()).hexdigest()==receipt['neutralPositionHash'][tag]
        values={};hashes={}
        for name,key,dtype,shape,channel in fields:
            value=attr(data,name,dtype,shape,channel);values[name]=value
            hashes[key]=sha256(value.tobytes()).hexdigest()
            assert hashes[key]==parent['branches']['B'][key],name
        assert len(np.unique(values['AFN409_CURVE_ID']))==24831
        assert len(np.unique(values['AFN409_POINT_ID']))==24831*80
        face=values['AFN409_SKIN_TRIANGLE_ID'];bary=values['AFN409_SKIN_BARYCENTRIC']
        local=values['AEVRYND_ROOT_OFFSET_LOCAL'];tri=skin[triangles[face]].astype('f8')
        u=tri[:,1]-tri[:,0];u/=np.linalg.norm(u,axis=1,keepdims=True)
        n=np.cross(u,tri[:,2]-tri[:,0]);n/=np.linalg.norm(n,axis=1,keepdims=True)
        v=np.cross(n,u)
        root=(tri*bary[:,:,None]).sum(1)+u*local[:,0,None]+v*local[:,1,None]+n*local[:,2,None]
        binding_error=float(np.linalg.norm(root-q[:,0],axis=1).max()*1000.)
        assert binding_error<.0006
        assert data.surface==body and data.surface_uv_map=='R483 Scalp Attachment Atlas'
        attachment=attr(data,'surface_uv_coordinate','f4',(24831,2),'vector')
        assert data.attributes['surface_uv_coordinate'].domain=='CURVE'
        assert np.array_equal(attachment,(uv[face]*bary[:,:,None]).sum(1).astype('f4'))
        corners=uv[face].astype('f8');edge=np.stack((corners[:,1]-corners[:,0],corners[:,2]-corners[:,0]),axis=2)
        xy=np.linalg.solve(edge,(attachment-corners[:,0])[...,None])[...,0]
        uv_bary=np.column_stack((1.-xy.sum(1),xy))
        native_surface_error=float(np.linalg.norm((tri*(uv_bary-bary)[:,:,None]).sum(1),axis=1).max()*1000.)
        results[tag]=dict(points=len(data.points),curves=len(data.curves),positionHash=receipt['neutralPositionHash'][tag],
            inheritedFieldHashes=hashes,rootsBitIdentical=True,maxPhysicalRootReconstructionErrorMm=binding_error,
            attachmentUVHash=sha256(attachment.tobytes()).hexdigest(),maxUVSurfaceAnchorRoundingErrorMm=native_surface_error,
            materials=[m.name for m in data.materials])
    report=dict(source=receipt['source'],branches=results,skinVertices=len(skin),skinTriangles=len(triangles),
        armatureObjects=sum(o.type=='ARMATURE' for o in bpy.data.objects),
        externalImages=[i.filepath for i in bpy.data.images if i.source=='FILE' and not i.packed_file],
        creditTexts=[t.name for t in bpy.data.texts],
        nativeBrushOperationVerified=False,contactStatus='NOT_EVALUATED_FOR_REBUILT_FREE_LENGTHS',
        scope='Neutral unrigged hair and skin fixture. Eyes, facial controls, clothes and actual engine operation are absent.')
    (ROOT/'reopen-verification.json').write_bytes(json.dumps(report,indent=2).encode('utf8'))
    print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':
    main()
