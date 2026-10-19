"""Bounded check of Multires coordinate/UV coupling; no source is saved."""
import bpy,importlib.util,json
import numpy as np
from pathlib import Path
spec=importlib.util.spec_from_file_location('b32',Path(__file__).with_name('build-female-next-r0032-registered-skin.py'));k=importlib.util.module_from_spec(spec);spec.loader.exec_module(k)
b=k.b;E=k.ROOT_E/'b'
def main():
    bpy.ops.wm.open_mainfile(filepath=str(k.S/'aevrynd-female-next-r0032-b-chart-registered-skin.blend'));body=bpy.data.objects[b.BODY]
    if 'AFN32_RegisteredCC0UVW' in body.data.attributes:
        vectors=np.empty(len(body.data.vertices)*3,dtype='f4');body.data.attributes['AFN32_RegisteredCC0UVW'].data.foreach_get('vector',vectors);loopverts=np.empty(len(body.data.loops),dtype='i4');body.data.loops.foreach_get('vertex_index',loopverts);uv=vectors.reshape(-1,3)[loopverts,:2].ravel()
    else:
        uv=np.empty(len(body.data.loops)*2,dtype='f4');body.data.uv_layers['AFN32_RegisteredCC0UV'].data.foreach_get('uv',uv);vectors=None
    bpy.ops.wm.open_mainfile(filepath=str(k.SRC));body=bpy.data.objects[b.BODY];bpy.context.view_layer.update();ref,t=b.evaluated(body,True);rows=[]
    def check(label):
        bpy.context.view_layer.update();v,tt=b.evaluated(body,True);rows.append({'change':label,'maxVertexDifferenceM':float(np.linalg.norm(v-ref,axis=1).max()),'changedVertices':int(np.any(v!=ref,axis=1).sum()),'trianglesExact':bool(np.array_equal(t,tt))})
    _=list(body.data.vertex_normals);check('read native vertex normals')
    layer=body.data.uv_layers.new(name='TEST_SECOND_UV');check('add copied/default second UV')
    layer.data.foreach_set('uv',uv);body.data.uv_layers.active_index=0;check('assign registered UV, active original')
    rows[-1]['uvFlags']=[{'name':x.name,'activeRender':x.active_render,'activeClone':x.active_clone} for x in body.data.uv_layers]
    for x in body.data.uv_layers:x.active_render=x.name=='UVMap'
    body.data.update();check('restore original render-active UV and mesh update')
    body.data.uv_layers.remove(layer);check('remove extra UV')
    attr=body.data.attributes.new('TEST_ROUGHNESS','FLOAT','POINT');attr.data.foreach_set('value',np.ones(len(body.data.vertices),dtype='f4')*.5);check('float attribute only')
    if vectors is not None:
        attr=body.data.attributes.new('TEST_REGISTERED_COORDINATES','FLOAT_VECTOR','POINT');attr.data.foreach_set('vector',vectors);check('point vector coordinates without extra UV')
    body.data.materials.clear();mat=bpy.data.materials.new('TEST_PLAIN');body.data.materials.append(mat);check('swap material slots')
    (E/'subdivision-coordinate-diagnosis.json').write_text(json.dumps({'source':str(k.SRC),'changes':rows,'scope':'Unsaved isolated dependency test; no adoption/score or collision exclusion.'},indent=2)+'\n',encoding='utf8');print(json.dumps(rows),flush=True)
if __name__=='__main__':main()
