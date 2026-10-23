"""Inspect actual artist mesh volumes and original parent paths; no rig script."""
from pathlib import Path
import bpy,numpy as np,json,datetime
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');R=Path('D:/Download/Aevrynd');E=C/'evidence/character-female-next/r0196-artist-primary-volumes';source=R/'Reference/character/blender-studio-ellie-v1-cc-by4/ellie.blend'
bpy.ops.wm.open_mainfile(filepath=str(source))
def arr(d,p,k=3):
 a=np.empty((len(d),k),'f4');d.foreach_get(p,a.ravel());return a
out={};rows=[]
for name in ['GEO-ellie_hair','GEO-ellie_hair.groom_base','GEO-ellie_hair.scalp','GEO-ellie_head']:
 o=bpy.data.objects.get(name)
 if not o:continue
 V=arr(o.data.vertices,'co');o.data.calc_loop_triangles();T=np.array([t.vertices[:] for t in o.data.loop_triangles],'i4');out[name+'_V']=V;out[name+'_T']=T
 psrows=[]
 for ps in o.particle_systems:
  paths=[np.array([k.co[:] for k in p.hair_keys],'f4') for p in ps.particles];lengths=[len(p) for p in paths];valid=[p for p in paths if len(p)>1];flat=np.vstack(valid) if valid else np.zeros((0,3));out[ps.name+'_P']=flat;out[ps.name+'_counts']=np.array([len(x) for x in valid],'i4');psrows.append({'name':ps.name,'settingsCount':ps.settings.count,'storedParentParticles':len(paths),'validStoredPaths':len(valid),'lengths':sorted(set(lengths)),'rawBounds':np.stack([flat.min(0),flat.max(0)]).tolist() if len(flat) else None,'sampleFirstPath':valid[0].tolist() if valid else None})
 rows.append({'name':name,'rawVertices':len(V),'rawBounds':np.stack([V.min(0),V.max(0)]).tolist(),'particles':psrows})
np.savez_compressed(E/'original-artist-volume-and-parent-data.npz',**out)
q={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':str(source),'objects':rows,'readme':bpy.data.texts['ReadMe.txt'].as_string(),'embeddedRigScriptsNotExecuted':True,'actualParentRawCoordinatesNotAssumedWorldOrSourceTargetCorrespondence':True}
(E/'artist-primary-volume-readback.json').write_bytes((json.dumps(q,indent=2)+'\n').encode());print('R196_ORIGINAL_ARTIST_PRIMARY_VOLUME_READ',json.dumps(rows),flush=True)
