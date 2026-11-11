"""Record dependency correction, editor settings and minimum source statistics."""
from pathlib import Path
from hashlib import file_digest,sha256
import json
import bpy
import numpy as np
ROOT=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return file_digest(f,'sha256').hexdigest()
def external():
    return dict(libraries=[dict(name=i.name,path=i.filepath,users=i.users) for i in bpy.data.libraries],
        images=[dict(name=i.name,path=i.filepath,users=i.users) for i in bpy.data.images if i.source=='FILE' and not i.packed_file],
        linkedIDs=[dict(name=i.name,type=i.bl_rna.identifier,library=i.library.filepath) for i in bpy.data.user_map() if i.library])
def scalars(value):
    result={}
    for p in value.bl_rna.properties:
        if p.type in ('BOOLEAN','INT','FLOAT','STRING','ENUM') and not getattr(p,'is_array',False):
            v=getattr(value,p.identifier);result[p.identifier]=sorted(v) if isinstance(v,set) else v
    return result
def main():
    proof=read(ROOT/'sealed-source-receipt.json')
    bpy.ops.wm.open_mainfile(filepath=proof['supersededLinkedSeal']['path'],load_ui=False,use_scripts=False)
    before=external()
    bpy.ops.wm.open_mainfile(filepath=proof['source']['path'],load_ui=False,use_scripts=False)
    after=external();assert not after['libraries'] and not after['images'] and not after['linkedIDs']
    fields={};positions={}
    for tag in ('control','A','B'):
        d=bpy.data.objects[f'R485 complete hair | {tag}'].data
        p=np.empty((24831,80,3),dtype='f4');d.position_data.foreach_get('vector',p.ravel())
        positions[tag]=p;assert sha256(p.tobytes()).hexdigest()==proof['modes'][tag]['positionHash']
        rows={}
        for name,dtype,shape,channel in (('radius','f4',(24831,80),'value'),('AFN409_CURVE_ID','i4',24831,'value'),
            ('AFN409_POINT_ID','i4',(24831,80),'value'),('AFN409_SKIN_TRIANGLE_ID','i4',24831,'value'),
            ('AFN409_SKIN_BARYCENTRIC','f4',(24831,3),'vector'),('AEVRYND_ROOT_OFFSET_LOCAL','f4',(24831,3),'vector'),
            ('AEVRYND_ROOT_NORMAL_OFFSET','f4',24831,'value'),('surface_uv_coordinate','f4',(24831,2),'vector')):
            v=np.empty(shape,dtype=dtype);d.attributes[name].data.foreach_get(channel,v.ravel());rows[name]=sha256(v.tobytes()).hexdigest()
        fields[tag]=rows
    assert fields['control']==fields['A']==fields['B']
    assert all(np.array_equal(p[:,0],positions['control'][:,0]) for p in positions.values())
    for tag in ('A','B'):assert fields[tag]==read(ROOT/f'native-{tag}-receipt.json')['attributeHashes']
    unified={}
    for label,owner in (('toolSettings',bpy.context.scene.tool_settings),('curvesSculpt',bpy.context.scene.tool_settings.curves_sculpt)):
        for prop in owner.bl_rna.properties:
            if 'unified' in prop.identifier:
                value=getattr(owner,prop.identifier)
                unified[label+'.'+prop.identifier]=scalars(value) if hasattr(value,'bl_rna') else str(value)
    body=bpy.data.objects['AFN126_COMPLETE_WOMAN_BODY_AND_ARTIST_HEAD'];ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
    verts=np.empty((len(mesh.vertices),3),dtype='f4');mesh.vertices.foreach_get('co',verts.ravel());mesh.calc_loop_triangles()
    matrix=np.asarray(body.matrix_world,dtype='f8');verts=(verts@matrix[:3,:3].T+matrix[:3,3]).astype('f4')
    triangles=np.asarray([t.vertices[:] for t in mesh.loop_triangles],dtype='i4');ev.to_mesh_clear()
    previous=read(ROOT.parent/'r0480-lock-clearance-projection/render-B-face.json')['skinStamp']
    skin_hash=[sha256(verts.tobytes()).hexdigest(),sha256(triangles.tobytes()).hexdigest()]
    assert skin_hash==previous,(skin_hash,previous)
    stats=[dict(name=o.name,type=o.type,vertices=len(o.data.vertices) if o.type=='MESH' else None,
        faces=len(o.data.polygons) if o.type=='MESH' else None,bones=len(o.data.bones) if o.type=='ARMATURE' else None,
        shapeKeys=len(o.data.shape_keys.key_blocks) if o.type=='MESH' and o.data.shape_keys else 0,hiddenFromRender=o.hide_render) for o in bpy.context.scene.objects]
    record=dict(source=proof['source'],dependencyStateBeforeCorrection=before,dependencyStateAfterCorrection=after,
        unifiedNativePaintSettings=unified,unchangedAttributeHashes=fields,allRootsBitIdentical=True,
        actualNeutralSkinHashes=skin_hash,actualNeutralSkinExactlyMatchesR480=True,
        evaluatedSkinVertices=len(verts),evaluatedSkinTriangles=len(triangles),sceneStatistics=stats,
        imageCount=len(bpy.data.images),materialCount=len(bpy.data.materials),nativeGuideHierarchyCreated=False,
        minimumSignedClearanceMm=None,penetrationCount=None,hairMotionTested=False,engineCPUTimeMs=None,engineGPUTimeMs=None,
        dependencyCause='The exact residual reference is recorded above. The earlier assertion that the native brush caused it was premature; no such causal claim is needed for the portable-source result.')
    (ROOT/'source-state-receipt.json').write_bytes(json.dumps(record,indent=2).encode('utf8'))
    print(json.dumps(dict(dependencyBefore=before,dependencyAfter=after,unified=unified,skinHashes=skin_hash),indent=2),flush=True)
if __name__=='__main__':main()
