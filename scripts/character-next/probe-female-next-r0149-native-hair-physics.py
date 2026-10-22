"""Single installed native hair-dynamics capability test, not a woman candidate."""
from pathlib import Path
import bpy,numpy as np,json,time,traceback
E=Path('D:/Download/Aevrynd/Evidence/character-female-next/r0149-native-scalp-sculpt');tick=time.time()
def main():
 try:
  bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=.09);ob=bpy.context.object;bpy.ops.object.particle_system_add();ps=ob.particle_systems[-1];s=ps.settings;s.type='HAIR';s.count=24;s.hair_length=.18;s.hair_step=3;s.display_step=3;s.render_step=3;s.child_type='INTERPOLATED';s.child_percent=3;s.rendered_child_count=3;ps.use_hair_dynamics=True;bpy.context.view_layer.update();ps.cloth.settings.quality=5;ps.cloth.settings.mass=.001;ps.cloth.settings.bending_stiffness=.05;scene=bpy.context.scene
  def points():
   bpy.context.view_layer.update();obj=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());system=obj.particle_systems[-1];return np.array([[system.co_hair(obj,particle_no=i,step=k)[:] for k in range(9)] for i in range(len(system.particles)+len(system.child_particles))]),len(system.particles),len(system.child_particles)
  scene.frame_set(1);P,n,c=points()
  for f in range(2,25):scene.frame_set(f)
  Q,nn,cc=points();move=float(np.linalg.norm(Q-P,axis=2).max());assert np.isfinite(Q).all() and nn==n and cc==c and move>1e-5;np.savez_compressed(E/'native-hair-physics-capability.npz',before=P,after=Q);out={'installedNativeHairDynamicsActuallyMoved':True,'parents':n,'children':c,'pointsShape':Q.shape,'maximumMovementM':move,'frames':[1,24],'seconds':time.time()-tick,'fixtureOnlyNotCompleteWomanOrAppearanceGain':True};(E/'native-hair-physics-capability.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print('R149_NATIVE_HAIR_PHYSICS_REAL_CAPABILITY_DONE',out,flush=True)
 except Exception:(E/'native-hair-physics-capability-failure.json').write_text(json.dumps({'traceback':traceback.format_exc(),'seconds':time.time()-tick},indent=2)+'\n',encoding='utf-8');raise
if __name__=='__main__':main()
