"""Reopen and inspect native POLY strand capsules; source equality is separate."""
import bpy,json,hashlib,array,importlib.util,time,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
spec=importlib.util.spec_from_file_location('route',Path(__file__).with_name('build-female-next-r0013-envelope-hair.py'));route=importlib.util.module_from_spec(spec);spec.loader.exec_module(route)
S,E,solid=route.S,route.E,route.solid

def original_state():
    meshes={}
    for o in bpy.data.objects:
        if o.type!='MESH' or o.name.startswith('AFN13_'):continue
        h=hashlib.sha256();m=o.data
        for uv in m.uv_layers:
            a=array.array('f',[0.]*(len(uv.data)*2));uv.data.foreach_get('uv',a);h.update(a.tobytes())
        w=[[(o.vertex_groups[g.group].name,g.weight) for g in v.groups] for v in m.vertices];h.update(json.dumps(w,separators=(',',':')).encode())
        meshes[o.name]={'geometry':solid.geom(o),'uvWeights':h.hexdigest(),'parent':o.parent.name if o.parent else None,'matrix':list(v for row in o.matrix_world for v in row),'materials':[x.name for x in m.materials]}
    def value(i):
        x=getattr(i,'default_value',None);return list(x) if x is not None and hasattr(x,'__iter__') and not isinstance(x,str) else x
    materials={m.name:{'nodes':[(n.name,n.bl_idname,[(i.name,value(i)) for i in n.inputs]) for n in m.node_tree.nodes],'links':[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in m.node_tree.links]} for m in bpy.data.materials if m.use_nodes and not m.name.startswith('AFN13_')}
    rig=bpy.data.objects['AFN_R0005_Rig'];s=bpy.context.scene
    return {'meshes':meshes,'materials':materials,'bones':[(b.name,list(v for row in b.matrix_local for v in row)) for b in rig.data.bones],'lights':[(o.name,list(o.location),list(o.rotation_euler),o.data.energy,o.data.size,list(o.data.color)) for o in bpy.data.objects if o.type=='LIGHT'],'view':(s.view_settings.view_transform,s.view_settings.look,s.view_settings.exposure,s.view_settings.gamma),'nodeGroups':sorted(n.name for n in bpy.data.node_groups)}

def native_paths(o):
    d=o.data;P=np.empty(len(d.position_data)*3,dtype=np.float32);d.position_data.foreach_get('vector',P);P=P.reshape(-1,3).astype(np.float64)
    M=np.array(o.matrix_world,dtype=np.float64);P=P@M[:3,:3].T+M[:3,3];rr=np.empty(len(P),dtype=np.float32);d.attributes['radius'].data.foreach_get('value',rr)
    assert all(x.value==1 for x in d.attributes['curve_type'].data)
    assert np.isfinite(P).all() and np.isfinite(rr).all() and (rr>0).all()
    offsets=[c.first_point_index for c in d.curves]+[len(P)];paths=[P[a:b] for a,b in zip(offsets[:-1],offsets[1:])];radii=[rr[a:b].astype(np.float64) for a,b in zip(offsets[:-1],offsets[1:])]
    return paths,radii

def poly_enum_proof():
    # Query the installed evaluator rather than assuming an integer enum mapping.
    d=bpy.data.hair_curves.new('AFN13_ENUM_PROBE');d.add_curves([3]);d.position_data.foreach_set('vector',[0.,0.,0.,.1,0.,.1,.2,0.,0.]);o=bpy.data.objects.new('AFN13_ENUM_PROBE',d);bpy.context.scene.collection.objects.link(o)
    group=bpy.data.node_groups.new('AFN13_ENUM_PROBE','GeometryNodeTree');group.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');group.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    a=group.nodes.new('NodeGroupInput');b=group.nodes.new('NodeGroupOutput');n=group.nodes.new('GeometryNodeCurveSplineType');n.spline_type='POLY';group.links.new(a.outputs['Geometry'],n.inputs['Curve']);group.links.new(n.outputs['Curve'],b.inputs['Geometry']);mod=o.modifiers.new('Probe','NODES');mod.node_group=group;bpy.context.view_layer.update()
    evaluated=o.evaluated_get(bpy.context.evaluated_depsgraph_get());v=evaluated.data.attributes['curve_type'].data[0].value;assert v==1,v
    bpy.data.objects.remove(o,do_unlink=True);bpy.data.hair_curves.remove(d);bpy.data.node_groups.remove(group);return {'installedSetSplineTypeNode':'POLY','evaluatedCurveTypeInteger':v}

def secondary_surfaces(paths,radii,parts):
    report={}
    for o in parts:
        V,T,tree=solid.data(o);V=np.array(V,dtype=np.float64);tri=V[np.array(T,dtype=np.int32)];lo=V.min(axis=0);hi=V.max(axis=0);bad=[];checked=0;culled=0
        for ci,(P,rr) in enumerate(zip(paths,radii)):
            # Axis separation bounds the entire piecewise-linear curve capsule.
            sep=max(float((P.min(axis=0)-hi).max()),float((lo-P.max(axis=0)).max()))
            if sep>float(rr.max())+.000001:culled+=1;continue
            ds=[tree.find_nearest(Vector(p))[3] for p in P]
            for j in range(len(P)-1):
                r=float(max(rr[j],rr[j+1]));gap,method=route.capsule.segment_test(P[j],P[j+1],ds[j],ds[j+1],r,tree,tri);checked+=1
                if gap<=0 and len(bad)<30:bad.append({'curve':ci,'segment':j,'method':method,'gapM':gap})
        report[o.name]={'bboxSeparatedCurves':culled,'checkedSegments':checked,'failureSamples':bad,'status':'PASS_SURFACE_SEPARATION' if not bad else 'FAIL_OR_UNRESOLVED','scope':'Surface separation; no closed-volume classification for open components.'}
    return report

def main():
    soft='--soft-roots' in sys.argv;label='b' if soft else 'a';prefix='b-' if soft else '';src=route.SRC;dest=S/f'aevrynd-female-next-r0013-{label}-native-envelope-hair-study.blend';build=json.loads((E/(prefix+'native-groom-build.json')).read_text());assert route.sha(dest)==build['outputSha256']
    bpy.ops.wm.open_mainfile(filepath=str(src));before=original_state();bpy.ops.wm.open_mainfile(filepath=str(dest));after=original_state();checks={k:before[k]==after[k] for k in before};assert all(checks.values()),checks
    libs=[l.filepath for l in bpy.data.libraries];assert not libs
    images=[{'name':i.name,'packed':bool(i.packed_file)} for i in bpy.data.images if i.source=='FILE'];assert all(i['packed'] for i in images)
    enum=poly_enum_proof();rig=bpy.data.objects['AFN_R0005_Rig'];body=bpy.data.objects['AFN_R0008_Body'];parts=sorted((o for o in bpy.data.objects if o.type=='CURVES' and o.name.startswith('AFN13_')),key=lambda o:o.name)
    poses=('neutral',) if '--neutral-only' in sys.argv else ('neutral','gaze-left','gaze-right','turn-left','turn-right');rows={}
    for pose in poses:
        start=time.time();solid.stage.set_pose(rig,pose);V,T,tree=solid.data(body);V=np.array(V,dtype=np.float64);tri=V[np.array(T,dtype=np.int32)];layer={};allP=[];allR=[]
        for o in parts:
            P,rr=native_paths(o);allP.extend(P);allR.extend(rr);audit=route.check_paths(P,rr,tree,tri);layer[o.name]=audit
            print('AFN13_SAVED_CHECK='+json.dumps({'pose':pose,'layer':o.name,'badSegments':audit['unqualifiedSegments'],'insideRoots':audit['rootContainmentFailures']}),flush=True)
        extra=secondary_surfaces(allP,allR,[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('AFN6_','AFN10_','AFN11_'))])
        rows[pose]={'body':layer,'otherSurfaces':extra,'wallSeconds':time.time()-start}
        result={'sourceSha256':route.sha(src),'candidate':str(dest),'candidateSha256':route.sha(dest),'sourceStateEquality':checks,'externalLibraries':libs,'packedImages':images,'polyEnumProof':enum,'poses':rows,'status':'PASS_TESTED_STATIC_SURFACE_SCOPE' if all(v['status']=='PASS_TESTED_BODY_CAPSULES' for row in rows.values() for v in row['body'].values()) and all(v['status']=='PASS_SURFACE_SEPARATION' for row in rows.values() for v in row['otherSurfaces'].values()) else 'FAIL_OR_UNRESOLVED','scopeLimits':['Hair/hair self separation not qualified.','Rigid head-parented static samples, no simulated motion or continuous collision.','Body gap is a conservative capsule clearance lower bound, not the exact minimum.','No runtime or character acceptance.']}
        (E/(prefix+'saved-native-groom-verification.json')).write_text(json.dumps(result,indent=2)+'\n')
        if result['status']!='PASS_TESTED_STATIC_SURFACE_SCOPE':break
    if '--render' in sys.argv:
        solid.stage.set_pose(rig,'neutral');solid.stage.eyes.E=E;fits=solid.stage.eyes.helper_centres()
        for view in ('face','oblique','profile'):solid.stage.eyes.render(label+'-native-envelope-hair',view,fits,'neutral')
    print('AFN13_SAVED_VERIFICATION_DONE',flush=True)

if __name__=='__main__':main()
