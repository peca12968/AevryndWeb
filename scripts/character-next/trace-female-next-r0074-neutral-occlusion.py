"""Trace the neutral dental crossing to actual r69 surfaces and check Head attachment."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util
from mathutils.bvhtree import BVHTree
from mathutils import Vector,Quaternion
sp=importlib.util.spec_from_file_location('screen74',Path(__file__).with_name('screen-female-next-r0074-oral-contact.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
E=m.E;R=m.R
def world(o):
    d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;p=np.array([v.co[:] for v in d.vertices]);a=np.array(o.matrix_world);return d,p@a[:3,:3].T+a[:3,3]
def main():
    src=R/'engine/assets/characters/female-next/source/aevrynd-female-next-r0069-a-complete-controls-study.blend';bpy.ops.wm.open_mainfile(filepath=str(src));bpy.context.scene.frame_set(1);o=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING'];d,p=world(o);ids=np.array([x.value for x in d.attributes['AFN60_NativeFaceID'].data]);charts=json.loads((E/'source-oral-uv-islands.json').read_text());sets={k:set(f for row in charts[3:] if (row['jawAffected']==0)==(k=='upper') for f in row['faces']) for k in ('upper','lower')};d.calc_loop_triangles();data={};corners={}
    for name,faceids in sets.items():
        triangles=np.array([v.vertices[:] for v in d.loop_triangles if int(ids[v.polygon_index]) in faceids]);data[name]=(p,triangles);corners[name]=np.array([p[v] for f in d.polygons if int(ids[f.index]) in faceids for v in f.vertices])
    trees={n:BVHTree.FromPolygons(p.tolist(),t.tolist(),all_triangles=True) for n,(p,t) in data.items()};hit=None
    for a,b in trees['upper'].overlap(trees['lower']):
        witness=m.proper_cross(data['upper'][0][data['upper'][1][a]],data['lower'][0][data['lower'][1][b]])
        if witness is not None:hit={'worldPointM':witness,'sourceTriangleUpper':int(a),'sourceTriangleLower':int(b)};break
    assert hit is not None,'The claimed inherited source crossing was not reproduced.'
    ref=json.loads((E/'c-build-summary.json').read_text());bpy.ops.wm.open_mainfile(filepath=ref['output']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();errors={};objects={n:bpy.data.objects['AFN74_'+n.upper()+'_TEETH_RIGID'] for n in ('upper','lower')}
    for name,o in objects.items():
        d,p=world(o);actual=np.array([p[v] for f in d.polygons for v in f.vertices]);assert actual.shape==corners[name].shape;err=float(np.linalg.norm(actual-corners[name],axis=1).max());assert err<1e-6;errors[name]=err
    s.frame_set(13);bpy.context.view_layer.update();rig=bpy.data.objects['AFN69_BODY_CONTROLS'];h0=rig.matrix_world@rig.pose.bones['Head'].matrix;before={n:world(o)[1].copy() for n,o in objects.items()};pb=rig.pose.bones['Head'];pb.rotation_mode='QUATERNION';axis=pb.bone.matrix_local.to_3x3().transposed()@Vector((0,0,1));pb.rotation_quaternion=Quaternion(axis,np.radians(20));bpy.context.view_layer.update();H=np.array((rig.matrix_world@pb.matrix)@h0.inverted());follow={}
    for name,o in objects.items():
        expected=before[name]@H[:3,:3].T+H[:3,3];err=float(np.linalg.norm(world(o)[1]-expected,axis=1).max());assert err<1e-6;follow[name]=err
    s.frame_set(1);rig.pose.bones['Head'].rotation_quaternion=(1,0,0,0);bpy.context.view_layer.update();meshes=[];curves=[]
    for o in s.objects:
        if o.hide_render:continue
        if o.type=='MESH':
            d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;d.calc_loop_triangles();meshes.append({'object':o.name,'vertices':len(d.vertices),'triangles':len(d.loop_triangles)})
        elif o.type=='CURVES':
            d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;curves.append({'object':o.name,'curves':len(d.curves),'points':len(d.position_data)})
    stats={'source':ref['output'],'sha256':ref['outputSha256'],'actualVisibleEvaluatedMeshComponents':meshes,'actualVisibleMeshVertices':sum(x['vertices'] for x in meshes),'actualVisibleTriangles':sum(x['triangles'] for x in meshes),'actualVisibleCurves':curves,'bones':52,'dentalArchMeshes':2,'nativeSoftSourceVertices':35606,'cpuGpuRuntimeMemoryLODNotTested':True};(E/'model-statistics.json').write_text(json.dumps(stats,indent=2),encoding='utf8')
    result={'status':'PASS_SOURCE_NEUTRAL_CROSSING_REPRODUCED_AND_BOTH_ARCH_HEAD_ATTACHMENTS','sourceR69ActualProperCrossing':hit,'candidateNeutralDentalSurfaceMaximumErrorsFromActualR69M':errors,'bothArchHead20DegreesAtFullOpeningMaximumWorldErrorsM':follow,'interpretation':'Neutral upper/lower tooth crossing exists in r69 and is retained, not repaired, by this prototype. It cannot be waived for final acceptance.','noContinuousMotionOrFullContactCertificate':True}
    (E/'c-source-occlusion-and-head-attachment.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result),flush=True)
if __name__=='__main__':main()
