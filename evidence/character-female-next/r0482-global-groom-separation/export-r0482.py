"""Export the standalone r482 Blender source to portable collision and binding streams."""
from argparse import ArgumentParser
from hashlib import file_digest, sha256
from pathlib import Path
import json
import sys
import bpy
import numpy as np


def digest(path):
    with path.open('rb') as stream:
        return file_digest(stream,'sha256').hexdigest()


def attribute(data,name,dtype,count,channel='value'):
    values=np.empty(count,dtype=dtype)
    data.attributes[name].data.foreach_get(channel,values.ravel())
    return values


def main():
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('--source',required=True,type=Path)
    parser.add_argument('--out',required=True,type=Path)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    source=args.source.resolve(strict=True)
    args.out.mkdir(parents=True,exist_ok=False)
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
    mesh=bpy.data.objects['R482 archived complete neutral skin'].data
    skin=np.empty((len(mesh.vertices),3),dtype='f4');mesh.vertices.foreach_get('co',skin.ravel())
    triangles=np.array([polygon.vertices[:] for polygon in mesh.polygons],dtype='i4')
    np.savez_compressed(args.out/'skin.npz',position=skin,triangles=triangles)
    provenance={'source':{'name':source.name,'sha256':digest(source)},'modes':{},'skinSha256':digest(args.out/'skin.npz')}
    for mode in ('base','A','B'):
        obj=bpy.data.objects[f'R482 complete groom | {mode}']; data=obj.data
        curves=len(data.curves);points=len(data.points)
        if points!=curves*80:
            raise ValueError('The r482 export requires 80 points on every curve.')
        q=np.empty((curves,80,3),dtype='f4');data.position_data.foreach_get('vector',q.ravel())
        radius=attribute(data,'radius','f4',(curves,80))
        ids=attribute(data,'AFN409_CURVE_ID','i4',curves)
        point_ids=attribute(data,'AFN409_POINT_ID','i4',(curves,80))
        face=attribute(data,'AFN409_SKIN_TRIANGLE_ID','i4',curves)
        bary=attribute(data,'AFN409_SKIN_BARYCENTRIC','f4',(curves,3),'vector')
        local=attribute(data,'AEVRYND_ROOT_OFFSET_LOCAL','f4',(curves,3),'vector')
        if len(np.unique(ids))!=curves or len(np.unique(point_ids))!=points:
            raise ValueError('Persistent strand and point identities must be unique.')
        tri=skin[triangles[face]].astype('f8')
        u=tri[:,1]-tri[:,0];u/=np.linalg.norm(u,axis=1,keepdims=True)
        n=np.cross(u,tri[:,2]-tri[:,0]);n/=np.linalg.norm(n,axis=1,keepdims=True);v=np.cross(n,u)
        root=np.sum(tri*bary[:,:,None],axis=1)+u*local[:,0,None]+v*local[:,1,None]+n*local[:,2,None]
        error=float(np.linalg.norm(root-q[:,0],axis=1).max()*1000.)
        if error>=.0006:
            raise ValueError(f'Scalp binding reconstruction error is {error} mm.')
        folder=args.out/mode;folder.mkdir()
        for name,array in (('rest.f32',q),('radius.f32',radius),('curve-ids.i32',ids),('point-ids.i32',point_ids)):
            array.tofile(folder/name)
        np.savez_compressed(folder/'root-binding.npz',skinTriangle=face,barycentric=bary,localOffset=local)
        capture=dict(source=provenance['source'],variant=mode,dimensions=list(q.shape),
            poses=[dict(label='rest',name='rest.f32',sha256=digest(folder/'rest.f32'))],rigidStopCoordinatesExactlyEqualToRest=False)
        (folder/'capture-source.json').write_text(json.dumps(capture,indent=2),encoding='utf8')
        provenance['modes'][mode]=dict(curves=curves,points=points,geometrySha256=digest(folder/'rest.f32'),
            radiusSha256=digest(folder/'radius.f32'),curveIDsSha256=digest(folder/'curve-ids.i32'),
            pointIDsSha256=digest(folder/'point-ids.i32'),rootBindingSha256=digest(folder/'root-binding.npz'),maxRootErrorMm=error)
    (args.out/'export-receipt.json').write_text(json.dumps(provenance,indent=2),encoding='utf8')
    print(json.dumps(provenance,indent=2),flush=True)


if __name__=='__main__':
    main()