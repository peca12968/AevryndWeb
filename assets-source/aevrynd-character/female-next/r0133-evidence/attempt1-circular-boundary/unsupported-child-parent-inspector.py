"""Read exact original SIMPLE parent roles and source-root geometric support."""
from pathlib import Path
import bpy,numpy as np,json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0133-anatomical-scalp-chart';OLD=E.parent/'r0092-native-compatible-groom';D=R/'Reference/character/charmorph-vitruvian-cc0'
with bpy.data.libraries.load(str(D/'hair.blend'),link=False) as (src,dst):dst.objects=['hair-src']
o=dst.objects[0];bpy.context.scene.collection.objects.link(o);o.hide_viewport=False;o.hide_render=False;o.hide_set(False)
for md in o.modifiers:
 if md.type=='PARTICLE_SYSTEM':md.show_viewport=md.show_render=md.particle_system.name=='Eve'
ps=o.particle_systems['Eve'];ps.settings=ps.settings.copy();ps.settings.child_percent=ps.settings.rendered_child_count;bpy.context.scene.frame_set(1);bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());ps=ev.particle_systems['Eve'];parents=np.array([p.parent for p in ps.child_particles],'i4');assert len(ps.particles)==1077 and len(parents)==26925;source=np.load(OLD/'native-Eve-source.npz');raw=np.load(OLD/'native-Eve-actual-children.npz')['nativeRawAPI'];T=source['triangles'];mi=np.repeat(source['sourceFaceMaterial'],source['sourceFaceCounts']-2);outer=np.flatnonzero(np.isin(mi,[4,5]));tree=BVHTree.FromPolygons(source['bodyNative'].tolist(),T[outer].tolist(),all_triangles=True);rows=[]
for r in raw[:,0]:
 co,no,fi,ds=tree.find_nearest(Vector(r));rows.append([ds,outer[fi]])
rows=np.array(rows);np.savez_compressed(E/'original-child-parent-roles.npz',childParent=parents,rootToOriginalOuterSkinDistanceNative=rows[:,0],rootNearestOriginalOuterTriangle=rows[:,1].astype('i4'));old=json.loads((E/'attempt1-circular-boundary/source-domain-diagnostic.json').read_text('utf-8'));outside=[x for x in old['outside2um'] if x['path']<1077];report={'parents':1077,'children':len(parents),'childParentRange':[int(parents.min()),int(parents.max())],'originalSourceParentRootToFullOuterSkinDistanceQuantilesNative':np.quantile(rows[:1077,0],[0,.5,.95,1]).tolist(),'originalSourceChildRootToFullOuterSkinDistanceQuantilesNative':np.quantile(rows[1077:,0],[0,.5,.95,1]).tolist(),'actualOriginalParentsOutsideFirstAuthoredBoundary':outside,'sourceSIMPLEIsNotAutomaticallyAnatomicalChildFollicles':True,'noSourceModificationOrGroomGeneration':True};(E/'original-root-role-readback.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('R133_ORIGINAL_CHILD_ROLE_METADATA',parents.min(),parents.max(),np.quantile(rows[:1077,0],[0,.5,.95,1]),np.quantile(rows[1077:,0],[0,.5,.95,1]),flush=True)
