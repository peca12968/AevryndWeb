from pathlib import Path
from hashlib import file_digest,sha256
import os,json
import numpy as np
import bpy
ROOT=Path(__file__).resolve().parent
def sha(p):
    with p.open('rb') as f:return file_digest(f,'sha256').hexdigest()
def main():
    tag=os.environ.get('R485_CAPTURE_TAG','A');source=ROOT/f'female-next-r0485-native-{tag}-UNACCEPTED.blend'
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
    obj=bpy.data.objects['R485 Native complete root-to-tip hair'];data=obj.data
    p=np.empty((24831,80,3),dtype='f4');data.position_data.foreach_get('vector',p.ravel())
    before=np.load(ROOT/'before-native.npz',allow_pickle=False)['position']
    delta=np.linalg.norm(p-before,axis=2)*1000.
    arrays={};fields=(('radius','f4',(24831,80),'value'),('AFN409_CURVE_ID','i4',24831,'value'),
        ('AFN409_POINT_ID','i4',(24831,80),'value'),('AFN409_SKIN_TRIANGLE_ID','i4',24831,'value'),
        ('AFN409_SKIN_BARYCENTRIC','f4',(24831,3),'vector'),('AEVRYND_ROOT_OFFSET_LOCAL','f4',(24831,3),'vector'),
        ('AEVRYND_ROOT_NORMAL_OFFSET','f4',24831,'value'),('surface_uv_coordinate','f4',(24831,2),'vector'))
    for name,dtype,shape,channel in fields:
        a=np.empty(shape,dtype=dtype);data.attributes[name].data.foreach_get(channel,a.ravel());arrays[name]=a
    np.savez_compressed(ROOT/f'native-{tag}-capture.npz',position=p,**arrays)
    settings=bpy.context.scene.tool_settings.curves_sculpt
    props={prop.identifier:getattr(settings,prop.identifier) for prop in settings.bl_rna.properties if prop.type in ('BOOLEAN','INT','FLOAT','STRING','ENUM') and not prop.is_array}
    record=dict(source=dict(path=str(source),sha256=sha(source),bytes=source.stat().st_size),object=obj.name,
        positionHash=sha256(p.tobytes()).hexdigest(),attributeHashes={k:sha256(v.tobytes()).hexdigest() for k,v in arrays.items()},
        changedStrands=int((delta>0).any(1).sum()),changedPoints=int((delta>0).sum()),
        movementMmP0P50P95P100=np.quantile(delta[delta>0],[0,.5,.95,1]).tolist() if (delta>0).any() else [0.]*4,
        rootCoordinatesBitIdentical=bool(np.array_equal(p[:,0],before[:,0])),maxRootMovementMm=float(delta[:,0].max()),
        finitePositions=bool(np.isfinite(p).all()),nativeSettings=props,
        nativeBrush=({k:getattr(settings.brush,k,None) for k in ('name','size','strength','curves_sculpt_tool')} if settings.brush else None),
        surface=data.surface.name if data.surface else None,surfaceUV=data.surface_uv_map,contactOrMotionAccepted=False)
    unified=getattr(bpy.context.scene.tool_settings,'unified_paint_settings',None)
    if unified:
        record['unifiedPaintSettings']={prop.identifier:getattr(unified,prop.identifier) for prop in unified.bl_rna.properties if prop.type in ('BOOLEAN','INT','FLOAT','STRING','ENUM') and not prop.is_array}
    record['curveDataCollisionSettings']={prop.identifier:getattr(data,prop.identifier) for prop in data.bl_rna.properties if 'collision' in prop.identifier and prop.type in ('BOOLEAN','INT','FLOAT','STRING','ENUM') and not prop.is_array}
    (ROOT/f'native-{tag}-receipt.json').write_bytes(json.dumps(record,indent=2).encode('utf8'))
    print(json.dumps(record,indent=2),flush=True)
if __name__=='__main__':main()
