from pathlib import Path
from hashlib import file_digest, sha256
import json
import numpy as np
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
R482=ROOT.parent/'r0482-global-groom-separation'
SOURCE=R482/'female-next-r0482-global-groom-UNACCEPTED.blend'
DEST=ROOT/'female-next-r0483-native-shape-work-UNACCEPTED.blend'
UV_NAME='R483 Scalp Attachment Atlas'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    with path.open('rb') as stream:
        return file_digest(stream,'sha256').hexdigest()


def smooth(value):
    value=np.clip(value,0.,1.)
    return value*value*(3.-2.*value)


def normalized(value):
    return value/np.maximum(np.linalg.norm(value,axis=-1,keepdims=True),1.e-12)


def strand_shape(base,ids,tag):
    roots=base[:,0]
    x,y,z=roots.T
    back=smooth((y+.030)/.052)*smooth((z-1.445)/.045)
    layer=np.clip((z-1.466)/.101,0.,1.)
    random=((ids.astype('u8')*np.uint64(1664525)+np.uint64(1013904223))&np.uint64(0xffffffff)).astype('f8')/4294967296.
    if tag=='A':
        height=1.425+.032*layer**1.45+.0032*np.sin(x/.018+.35)
    else:
        height=1.426+.025*layer**1.3+.0055*np.clip(x/.06,-1.,1.)
    height+=.0018*(random-.5)
    eligible=back*(roots[:,2]>height+.013)
    crossed=(base[:,:,2]<=height[:,None])&(np.arange(80)[None,:]>=10)
    first=np.where(crossed.any(1),crossed.argmax(1),79)
    first=np.maximum(first,1)
    row=np.arange(len(base)); previous=first-1
    a,b=base[row,previous,2],base[row,first,2]
    fraction=np.clip((a-height)/np.maximum(a-b,1.e-9),0.,1.)
    terminal=previous+fraction
    terminal=np.where(crossed.any(1),terminal,79.)
    terminal=79.+eligible*(terminal-79.)
    u=terminal[:,None]*(np.arange(80,dtype='f4')/79.)[None,:]
    index=np.minimum(u.astype('i4'),78)
    blend=(u-index).astype('f4')
    q=base[row[:,None],index]*(1.-blend[:,:,None])+base[row[:,None],index+1]*blend[:,:,None]
    # A smooth terminal Hermite segment turns cut ends toward gravity.
    start=67
    tail=q[:,start:].copy()
    length=np.linalg.norm(np.diff(tail,axis=1),axis=2).sum(1)
    v0=normalized(q[:,start+2]-q[:,start-2])*length[:,None]
    direction=np.stack((.08*np.sign(x),-.10*eligible,-np.ones_like(x)),axis=1)
    v1=normalized(direction)*length[:,None]
    t=np.linspace(0.,1.,80-start,dtype='f4')[None,:,None]
    h00=2.*t**3-3.*t**2+1.;h10=t**3-2.*t**2+t
    h01=-2.*t**3+3.*t**2;h11=t**3-t**2
    hermite=h00*tail[:,0,None,:]+h10*v0[:,None,:]+h01*tail[:,-1,None,:]+h11*v1[:,None,:]
    changed=eligible*((79.-terminal)>.15)
    q[:,start:]=tail+changed[:,None,None]*(hermite-tail)
    crown=np.zeros(len(base),dtype='f4')
    if tag=='B':
        crown=smooth((z-1.505)/.045)*smooth((.062-np.abs(x))/.022)*smooth((y+.055)/.040)
        phase=np.linspace(0.,1.,80,dtype='f4')[None,:]
        flow=(.007*np.sin(np.pi*phase)**2+.012*smooth((phase-.27)/.73))*crown[:,None]
        q[:,:,0]+=flow
        q[:,:,1]+=.0018*np.sin(np.pi*phase)*crown[:,None]
    q=q.astype('f4')
    q[(eligible==0.)&(crown==0.)]=base[(eligible==0.)&(crown==0.)]
    q[:,0]=base[:,0]
    before=np.linalg.norm(np.diff(base,axis=1),axis=2).sum(1)
    after=np.linalg.norm(np.diff(q,axis=1),axis=2).sum(1)
    active=np.any(q!=base,axis=2)
    return q,dict(changedStrands=int(active.any(1).sum()),maxMovementMm=float(np.linalg.norm(q-base,axis=2).max()*1000.),
        arcLengthRatioP05P50P95=np.quantile(after/before,[.05,.5,.95]).tolist(),
        tipHeightMmP05P50P95=(np.quantile(q[eligible>.8,-1,2],[.05,.5,.95])*1000.).tolist())


def attachment_atlas(body,objects):
    mesh=body.data
    assert all(len(polygon.vertices)==3 for polygon in mesh.polygons)
    count=len(mesh.polygons);side=int(np.ceil(np.sqrt(count)))
    face=np.arange(count,dtype='i4')
    origin=np.column_stack((face%side,face//side)).astype('f4')
    corners=(origin[:,None,:]+np.array(((.10,.10),(.90,.10),(.10,.90)),dtype='f4')[None,:,:])/side
    uv=mesh.uv_layers.new(name=UV_NAME)
    uv.data.foreach_set('uv',corners.ravel())
    rows={}
    for tag,obj in objects.items():
        data=obj.data;n=len(data.curves)
        faces=np.empty(n,dtype='i4');data.attributes['AFN409_SKIN_TRIANGLE_ID'].data.foreach_get('value',faces)
        weights=np.empty((n,3),dtype='f4');data.attributes['AFN409_SKIN_BARYCENTRIC'].data.foreach_get('vector',weights.ravel())
        values=np.sum(corners[faces]*weights[:,:,None],axis=1).astype('f4')
        attr=data.attributes.get('surface_uv_coordinate') or data.attributes.new('surface_uv_coordinate','FLOAT2','CURVE')
        attr.data.foreach_set('vector',values.ravel())
        data.surface=body;data.surface_uv_map=UV_NAME
        rows[tag]=sha256(values.tobytes()).hexdigest()
    return rows


def main():
    proof=read(R482/'final-source-receipt.json')
    assert sha(SOURCE)==proof['source']['sha256'] and not DEST.exists()
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE),load_ui=False,use_scripts=False)
    scene=bpy.context.scene
    original=bpy.data.objects['R482 complete groom | B'].data
    p=np.empty((len(original.points),3),dtype='f4');original.position_data.foreach_get('vector',p.ravel());base=p.reshape(-1,80,3)
    ids=np.empty(len(original.curves),dtype='i4');original.attributes['AFN409_CURVE_ID'].data.foreach_get('value',ids)
    assert sha256(base.tobytes()).hexdigest()==proof['branches']['B']['positionHash']
    objects={};metrics={};stamps={};old_data=[]
    for tag in ('base','A','B'):
        obj=bpy.data.objects[f'R482 complete groom | {tag}'];old_data.append(obj.data)
        obj.data=original.copy();obj.name=f'R483 complete groom | {tag}';obj.data.name=f'R483 native curves | {tag}'
        q=base.copy()
        if tag!='base':q,metrics[tag]=strand_shape(base,ids,tag)
        obj.data.position_data.foreach_set('vector',q.ravel())
        assert np.array_equal(q[:,0],base[:,0]) and np.isfinite(q).all()
        obj.data.update_tag();obj.update_tag();obj.color=(.20,.065,.022,1.)
        obj.hide_render=tag!='A';obj.hide_set(tag!='A');objects[tag]=obj;stamps[tag]=sha256(q.tobytes()).hexdigest()
        np.savez_compressed(ROOT/f'shape-{tag}.npz',position=q,curveIDs=ids)
    for data in old_data:
        if data.users==0:bpy.data.hair_curves.remove(data)
    body=bpy.data.objects['R482 archived complete neutral skin'];body.name='R483 complete neutral skin';body.color=(.62,.47,.38,1.)
    uv=attachment_atlas(body,objects)
    bpy.ops.object.select_all(action='DESELECT')
    objects['A'].select_set(True);bpy.context.view_layer.objects.active=objects['A']
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                area.spaces.active.region_3d.view_perspective='CAMERA'
                area.spaces.active.shading.type='SOLID';area.spaces.active.shading.color_type='OBJECT'
    scene['R483_WorkingStatus']='Unaccepted macro hairstyle studies; original root coordinates and all identity/binding fields retained.'
    text=bpy.data.texts.new('Aevrynd_R483_Working_Note')
    text.write('R483 graduated rear layers and diagonal crown-flow studies. All strands and radii retained. Native surface UV atlas is generated from the actual triangle ordering and stored barycentric attachment. Root positions and the r482 local root-offset binding are preserved.\n')
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST),compress=True,copy=True)
    (ROOT/'shape-receipt.json').write_bytes(json.dumps(dict(source=dict(path=str(DEST),sha256=sha(DEST),bytes=DEST.stat().st_size),
        parent=proof['source'],neutralPositionHash=stamps,variants=metrics,attachmentUVHashes=uv,rootCount=len(ids),rootCoordinatesExact=True,
        scope='Major free-length reconstruction on the current complete groom. A is graduated rear layering, B adds diagonal crown flow. Native Curve Sculpt operation and collision gates remain pending.'),indent=2).encode('utf8'))
    print('R483_SHAPES',metrics,flush=True)


if __name__=='__main__':
    main()
