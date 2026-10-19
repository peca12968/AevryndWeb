"""Bounded source-emitter falsification using native evaluated hair keys."""
from pathlib import Path
import bpy,numpy as np,json,time,hashlib,sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(r'D:\Download\Aevrynd');D=R/'Reference/character/charmorph-vitruvian-cc0';E=R/'Evidence/character-female-next/r0058-source-emitter'
def main():
    tick=time.time();provenance=json.loads((E/'source-provenance.json').read_text());p=Path(provenance['file']);assert hashlib.sha256(p.read_bytes()).hexdigest()==provenance['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(p))
    if bpy.context.object and bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
    inventory=[]
    for o in bpy.context.scene.objects:
        inventory.append({'name':o.name,'type':o.type,'vertices':len(o.data.vertices) if o.type=='MESH' else None,'matrix':list(sum((list(row) for row in o.matrix_world),[])),'modifiers':[{'name':m.name,'type':m.type,'viewport':m.show_viewport,'render':m.show_render} for m in o.modifiers],'systems':[{'name':ps.name,'particles':len(ps.particles),'countSetting':ps.settings.count,'globalHair':ps.is_global_hair,'childType':ps.settings.child_type,'renderChildCount':ps.settings.rendered_child_count,'displayChildCount':ps.settings.child_percent,'rootRadius':ps.settings.root_radius,'tipRadius':ps.settings.tip_radius,'radiusScale':ps.settings.radius_scale,'hairKeys':len(ps.particles[0].hair_keys) if ps.particles else 0,'densityGroup':ps.vertex_group_density} for ps in o.particle_systems]})
    o=bpy.data.objects['hair-src'];P=np.array([v.co[:] for v in o.data.vertices],dtype='f4');canonical=np.load(D/'Default.npy').astype('f4');src57=np.load(R/'Evidence/character-female-next/r0057-coherent-foundation/canonical-mesh-data.npz')
    sourceFaces=np.array([vi for poly in o.data.polygons for vi in poly.vertices],dtype='i4');polyCounts=np.array([len(poly.vertices) for poly in o.data.polygons],dtype='i4')
    sameCount=len(P)==len(canonical);sameTopo=sameCount and np.array_equal(sourceFaces,src57['corners']) and np.array_equal(polyCounts,src57['polygonCounts'])
    differences=np.linalg.norm(P-canonical,axis=1) if sameCount else None
    enabled='--enable-native-modifier' in sys.argv
    female='--female' in sys.argv
    prefix='c-female-' if female else ('b-enabled-' if enabled else '')
    if female:
        morph=np.load(D/'Gender_Female.npz');F=np.load(D/'Default.npy').copy();F[morph['idx']]+=morph['delta'];o.data.vertices.foreach_set('co',F.astype('f4').ravel());o.data.update()
    if enabled:
        for md in o.modifiers:
            if md.type=='PARTICLE_SYSTEM':md.show_viewport=md.particle_system.name=='Bob'
    bpy.context.scene.frame_set(1)
    # Only parent guides are inspected. Disabling child generation cannot repair
    # a parent path; it bounds this falsification and avoids a dense render.
    for ob in bpy.context.scene.objects:
        for ps in ob.particle_systems:ps.settings.child_type='NONE'
    bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());ps=next(s for s in ev.particle_systems if s.name=='Bob');mod=next(m for m in ev.modifiers if m.type=='PARTICLE_SYSTEM' and m.particle_system.name=='Bob')
    counts=np.array([len(p.hair_keys) for p in ps.particles],dtype='i4')
    Q=np.array([key.co_object(ev,mod,particle)[:] for particle in ps.particles for key in particle.hair_keys],dtype='f4');assert np.isfinite(Q).all() and len(Q)>0
    starts=np.r_[0,np.cumsum(counts)[:-1]];roots=Q[starts]
    me=ev.to_mesh();me.calc_loop_triangles();V=np.array([v.co[:] for v in me.vertices],dtype='f4');tri=np.array([t.vertices[:] for t in me.loop_triangles],dtype='i4');ev.to_mesh_clear()
    tree=BVHTree.FromPolygons(V.tolist(),tri.tolist(),all_triangles=True);rootDistance=np.array([tree.find_nearest(Vector(q))[3] for q in roots]);npz=np.load(D/'Bob.npz');npzQ=npz['data'];nonroots=np.delete(Q,starts,axis=0);sameHairShape=npzQ.shape==nonroots.shape
    np.savez_compressed(E/(prefix+'native-emitter-and-bob-data.npz'),emitterPositions=P,emitterCorners=sourceFaces,emitterPolygonCounts=polyCounts,evaluatedEmitterPositions=V,evaluatedEmitterTriangles=tri,hairPositions=Q,hairCounts=counts,rootDistances=rootDistance,emitterMatrix=np.array(o.matrix_world))
    info={'source':provenance,'inventory':inventory,'enabledNativeBobModifier':enabled,'suppliedFemaleMorph':1 if female else 0,'embeddedTextsDisabledNotImported':[t.name for t in bpy.data.texts],'canonicalBodyVertexCount':len(canonical),'emitterVertexCount':len(P),'canonicalTopologyExact':sameTopo,'canonicalCoordinatesExact':bool(sameCount and np.array_equal(P,canonical)),'maximumNativeEmitterVsCanonicalCoordinateDifferenceM':float(differences.max()) if sameCount else None,'nativeHairParticles':len(counts),'nativeHairKeyCounts':sorted(set(counts.tolist())),'nativeHairBounds':[Q.min(0).tolist(),Q.max(0).tolist()],'sourceNPZShape':list(npzQ.shape),'nativeFlatShape':list(Q.shape),'sourceNPZVsNativeNonrootMaximumDifferenceM':float(np.linalg.norm(npzQ-nonroots,axis=1).max()) if sameHairShape else None,'nativeRootUnsignedDistanceRangeM':[float(rootDistance.min()),float(rootDistance.max())],'nativeRootsOver100Micrometres':int((rootDistance>.0001).sum()),'actualEmitterEvaluatedVertices':len(V),'actualEmitterEvaluatedTriangles':len(tri),'notACollisionPass':'Unsigned root checks are lineage diagnosis only; actual finite paths/full head not qualified.','seconds':time.time()-tick}
    (E/(prefix+'native-source-inspection.json')).write_text(json.dumps(info,indent=2)+'\n',encoding='utf8')
    print('R58_NATIVE_EMITTER',prefix,len(P),'SAME_TOPOLOGY',sameTopo,'MAX_DELTA',info['maximumNativeEmitterVsCanonicalCoordinateDifferenceM'],'GUIDES',len(counts),'ROOT_RANGE',info['nativeRootUnsignedDistanceRangeM'],'NPZ_NONROOT_DIFF',info['sourceNPZVsNativeNonrootMaximumDifferenceM'],time.time()-tick,flush=True)
if __name__=='__main__':main()
