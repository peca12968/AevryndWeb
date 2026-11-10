from pathlib import Path
from runpy import run_path
import numpy as np
import bpy

ROOT=Path(__file__).resolve().parent
a=run_path(str(ROOT/'author-r0482.py'))
old,groom=a['old'],a['groom']
DEST=ROOT/'female-next-r0482-global-groom-bound-UNACCEPTED.blend'
OFFSET='AEVRYND_ROOT_NORMAL_OFFSET'
LOCAL='AEVRYND_ROOT_OFFSET_LOCAL'


def check_shader(mat):
    names=[]; seen=set()
    def visit(tree):
        if tree.as_pointer() in seen:return
        seen.add(tree.as_pointer())
        for node in tree.nodes:
            if node.bl_idname=='ShaderNodeAttribute':names.append(node.attribute_name)
            if node.bl_idname=='ShaderNodeGroup' and node.node_tree:visit(node.node_tree)
    visit(mat.node_tree)
    assert not {'AFN409_SKIN_TRIANGLE_ID','AFN409_SKIN_BARYCENTRIC',OFFSET,LOCAL}&set(names),names
    return names


def main():
    source=old.read(ROOT/'surface-source-receipt.json'); binding=old.read(ROOT/'binding-receipt.json')
    assert old.file_sha(Path(source['source']['path']))==source['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=source['source']['path'],load_ui=False)
    shader_attributes=check_shader(bpy.data.materials[a['MATERIAL']])
    rows={}; vectors={}
    for tag,previous in source['branches'].items():
        entry=binding['controlRootBinding'] if tag=='base' else binding['variants'][tag]
        file=ROOT/entry['file'];assert old.file_sha(file)==entry['sha256']
        with np.load(file,allow_pickle=False) as f:
            face,weights,offset,local=(f[key] for key in ('skinTriangle','barycentric','rootNormalOffset','rootLocalOffset'))
        obj=bpy.data.objects[previous['object']]; data=obj.data
        data.attributes['AFN409_SKIN_TRIANGLE_ID'].data.foreach_set('value',face)
        data.attributes['AFN409_SKIN_BARYCENTRIC'].data.foreach_set('vector',weights.ravel())
        attr=data.attributes.new(OFFSET,'FLOAT','CURVE');attr.data.foreach_set('value',offset)
        attr=data.attributes.new(LOCAL,'FLOAT_VECTOR','CURVE');attr.data.foreach_set('vector',local.ravel())
        data.update_tag();obj.update_tag()
        rows[tag]=previous|dict(faceHash=groom.arr_sha(face),baryHash=groom.arr_sha(weights),offsetHash=groom.arr_sha(offset),localOffsetHash=groom.arr_sha(local))
    assert not DEST.exists()
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST),compress=True,copy=True)
    bpy.ops.wm.open_mainfile(filepath=str(DEST),load_ui=False)
    skin=bpy.data.objects['R482 archived complete neutral skin'].data
    body=np.empty((len(skin.vertices),3),dtype='f4');skin.vertices.foreach_get('co',body.ravel())
    triangles=np.array([poly.vertices[:] for poly in skin.polygons],dtype='i4')
    assert [groom.arr_sha(x) for x in (body,triangles)]==binding['skinStamp']
    max_errors={}
    for tag,row in rows.items():
        obj=bpy.data.objects[row['object']];data=obj.data
        q=np.empty((len(data.points),3),dtype='f4');data.position_data.foreach_get('vector',q.ravel());assert groom.arr_sha(q)==row['positionHash']
        roots=q.reshape(-1,80,3)[:,0];n=len(data.curves)
        faces=np.empty(n,dtype='i4');data.attributes['AFN409_SKIN_TRIANGLE_ID'].data.foreach_get('value',faces);assert groom.arr_sha(faces)==row['faceHash']
        weights=np.empty((n,3),dtype='f4');data.attributes['AFN409_SKIN_BARYCENTRIC'].data.foreach_get('vector',weights.ravel());assert groom.arr_sha(weights)==row['baryHash']
        offset=np.empty(n,dtype='f4');data.attributes[OFFSET].data.foreach_get('value',offset);assert groom.arr_sha(offset)==row['offsetHash']
        for name,dtype,count,key in (('radius','f4',len(q),'radiusHash'),('AFN409_CURVE_ID','i4',n,'curveIdHash'),('AFN409_POINT_ID','i4',len(q),'pointIdHash')):
            value=np.empty(count,dtype=dtype);data.attributes[name].data.foreach_get('value',value);assert groom.arr_sha(value)==row[key]
        tri=body[triangles[faces]].astype('f8');normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normal/=np.linalg.norm(normal,axis=1,keepdims=True)
        local=np.empty((n,3),dtype='f4');data.attributes[LOCAL].data.foreach_get('vector',local.ravel());assert groom.arr_sha(local)==row['localOffsetHash']
        u=tri[:,1]-tri[:,0];u/=np.linalg.norm(u,axis=1,keepdims=True);v=np.cross(normal,u)
        anchor=np.sum(tri*weights[:,:,None],axis=1); rebuilt=anchor+u*local[:,0,None]+v*local[:,1,None]+normal*local[:,2,None]
        err=float(np.linalg.norm(rebuilt-roots,axis=1).max()*1000.);assert err<.0006,(tag,err)
        max_errors[tag]=err
        assert data.surface.name=='R482 archived complete neutral skin'
    old.save(ROOT/'bound-source-receipt.json',dict(source=dict(path=str(DEST),bytes=DEST.stat().st_size,sha256=old.file_sha(DEST)),
        parent=source['source'],bindingReceiptSha256=old.file_sha(ROOT/'binding-receipt.json'),surfaceReceiptSha256=old.file_sha(ROOT/'surface-receipt.json'),
        branches=rows,renders=source['renders'],hairMaterial=source['hairMaterial'],bodyMaterial=source['bodyMaterial'],
        maxRootReconstructionErrorMm=max_errors,renderGeometryUnchanged=True,shaderAttributeDependencies=shader_attributes,
        previewReuse='All rendered point positions, radii, topology, materials and scene settings are preserved. Only root-binding attributes and a normal offset scalar were changed. The hair shader does not read those attributes.',
        default='B',scope=source['scope']))
    print('R482_BOUND_SOURCE',DEST,max_errors,flush=True)


if __name__=='__main__':
    main()
