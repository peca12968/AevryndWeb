from pathlib import Path
from runpy import run_path
from time import perf_counter
import numpy as np
from mathutils import Matrix
import bpy

ROOT=Path(__file__).resolve().parent
l=run_path(str(ROOT/'solve-r0482.py'))
old,groom=l['old'],l['groom']
R470=l['l']['R470']; R480=l['R480']
g=run_path(str(ROOT.parent/'r0473-cross-section-transfer'/'geometry-study-r0473.py'))
DEST=ROOT/'female-next-r0482-global-groom-rest-UNACCEPTED.blend'
TAGS=('base','A','B')
VIEWS=('posterior-detail','rear-oblique','opposite-profile','face','back','full-body','crown')
MATERIAL='AFN350_OWNED_KERATIN_SHORT_CURL_CONSTRUCTION'


def read_data():
    original,r,ids,keep,_,_,body,tri=l['l']['p']['raw_data']()
    proof=old.read(ROOT/'global-receipt.json')
    p0=old.read(R480/'projection-receipt.json')
    path=R480/p0['variants']['B']['file']; assert old.file_sha(path)==p0['variants']['B']['sha256']
    binding=old.read(l['l']['R469']/'groom-probe.json')['restAttributes']
    with np.load(l['l']['R469']/binding['path'],allow_pickle=False) as f:
        face,weights=f['face'][keep],f['weights'][keep]
    with np.load(path,allow_pickle=False) as f:
        base=f['position']
    point=ids[:,None]*80+np.arange(80,dtype='i4')[None,:]
    variants={'base':dict(position=base,radius=r,curveIDs=ids,pointIDs=point,skinTriangle=face,barycentric=weights)}
    for tag,item in proof['variants'].items():
        path=ROOT/item['file']; assert old.file_sha(path)==item['sha256']
        with np.load(path,allow_pickle=False) as f:
            variants[tag]={key:f[key] for key in variants['base']}
    return proof,variants,body,tri


def main():
    assert not DEST.exists()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    proof,banks,body,tri=read_data()
    source=old.read(R480/'source-receipt.json')['source']
    with bpy.data.libraries.load(source['path'],link=False) as (available,loaded):
        assert MATERIAL in available.materials
        loaded.materials=[MATERIAL]
    hairmat,=loaded.materials
    assert hairmat.name==MATERIAL and hairmat.use_nodes
    scene=bpy.context.scene; scene.render.engine='CYCLES'; scene.cycles.samples=16
    scene.cycles.use_denoising=True; scene.cycles.seed=448
    scene.render.resolution_x=scene.render.resolution_y=640; scene.render.resolution_percentage=100
    scene.view_settings.view_transform='AgX'; scene.view_settings.look='AgX - Medium High Contrast'; scene.view_settings.exposure=-.5
    scene.world=bpy.data.worlds.new('R482 neutral comparison world'); scene.world.color=(.12,.12,.12)
    for name,xyz,power,size in (('Broad key',(.35,.35,1.95),30.,.4),('Side fill',(-.32,.15,1.61),14.,.28),('Crown edge',(.08,-.24,1.83),21.,.27)):
        g['lamp'](scene,name,xyz,power,size)
    skinmat=g['material']('R482 neutral diagnostic skin',(.46,.37,.29),.57)
    mesh=bpy.data.meshes.new('R482 archived complete neutral skin'); mesh.from_pydata(body.tolist(),[],tri.tolist()); mesh.update()
    mesh.polygons.foreach_set('use_smooth',np.ones(len(tri),dtype=bool)); mesh.materials.append(skinmat)
    skin=bpy.data.objects.new(mesh.name,mesh); scene.collection.objects.link(skin)
    camera=bpy.data.objects.new('R482 fixed comparison camera',bpy.data.cameras.new('R482 camera')); scene.collection.objects.link(camera); scene.camera=camera
    rows={}
    for tag,bank in banks.items():
        obj=g['curve_snapshot'](scene,tag,bank['position'],bank['radius'],bank['curveIDs'],np.eye(4),hairmat)
        obj.name=f'R482 complete groom | {tag}'
        obj.data.surface=skin
        for name,kind,domain,key,channel in (('AFN409_POINT_ID','INT','POINT','pointIDs','value'),
                ('AFN409_SKIN_TRIANGLE_ID','INT','CURVE','skinTriangle','value'),
                ('AFN409_SKIN_BARYCENTRIC','FLOAT_VECTOR','CURVE','barycentric','vector')):
            attr=obj.data.attributes.new(name,kind,domain); attr.data.foreach_set(channel,bank[key].ravel())
        obj.hide_render=tag!='B'; obj.hide_set(tag!='B')
        obj['construction_status']='UNACCEPTED rest study; body is the archived neutral mesh and not the full rig.'
        rows[tag]=dict(object=obj.name,positionHash=groom.arr_sha(bank['position']),radiusHash=groom.arr_sha(bank['radius']),
            curveIdHash=groom.arr_sha(bank['curveIDs']),pointIdHash=groom.arr_sha(bank['pointIDs']),
            faceHash=groom.arr_sha(bank['skinTriangle']),baryHash=groom.arr_sha(bank['barycentric']))
    skin_name=skin.name
    shot=old.read(R470/'shot-A-rear-oblique.json')['shot']; camera.matrix_world=Matrix(shot['camera']); camera.data.lens=shot['lens']
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST),compress=True,copy=True)
    bpy.ops.wm.open_mainfile(filepath=str(DEST),load_ui=False)
    scene=bpy.context.scene
    for tag,row in rows.items():
        obj=bpy.data.objects[row['object']]; data=obj.data
        q=np.empty((len(data.points),3),dtype='f4'); data.position_data.foreach_get('vector',q.ravel())
        assert groom.arr_sha(q)==row['positionHash']
        for name,dtype,count,channel,key in (('radius','f4',len(q),'value','radiusHash'),('AFN409_CURVE_ID','i4',len(data.curves),'value','curveIdHash'),
                ('AFN409_POINT_ID','i4',len(q),'value','pointIdHash'),('AFN409_SKIN_TRIANGLE_ID','i4',len(data.curves),'value','faceHash')):
            a=np.empty(count,dtype=dtype); data.attributes[name].data.foreach_get(channel,a); assert groom.arr_sha(a)==row[key]
        a=np.empty((len(data.curves),3),dtype='f4'); data.attributes['AFN409_SKIN_BARYCENTRIC'].data.foreach_get('vector',a.ravel())
        assert groom.arr_sha(a)==row['baryHash'] and data.surface.name==skin_name
        assert [m.name for m in data.materials]==[MATERIAL]
    renders={}
    for view in VIEWS:
        shot=old.read(R470/f'shot-A-{view}.json')['shot']
        scene.camera.matrix_world=Matrix(shot['camera']); scene.camera.data.lens=shot['lens']; bpy.context.view_layer.update()
        for tag,row in rows.items():
            for mode,entry in rows.items():
                obj=bpy.data.objects[entry['object']]; obj.hide_render=mode!=tag; obj.hide_set(mode!=tag)
            file=ROOT/f'{tag}-{view}.png'; assert not file.exists()
            scene.render.filepath=str(file); start=perf_counter(); bpy.ops.render.render(write_still=True)
            renders[f'{tag}:{view}']=dict(file=str(file),sha256=old.file_sha(file),camera=shot['camera'],lens=shot['lens'],
                exposure=scene.view_settings.exposure,view=view,tag=tag,seconds=perf_counter()-start)
            print('R482_RENDER',tag,view,flush=True)
    old.save(ROOT/'source-receipt.json',dict(source=dict(path=str(DEST),bytes=DEST.stat().st_size,sha256=old.file_sha(DEST)),
        globalReceiptSha256=old.file_sha(ROOT/'global-receipt.json'),branches=rows,renders=renders,
        hairMaterial=MATERIAL,bodyMaterial='R482 neutral diagnostic skin',default='B',
        scope='Standalone neutral full-groom Blender source with preserved persistent identities, explicit scalp triangle and barycentric attributes, original owned keratin shader and archived complete skin. This fixture carries no rig, expression morphs or motion acceptance.'))


if __name__=='__main__':
    main()
