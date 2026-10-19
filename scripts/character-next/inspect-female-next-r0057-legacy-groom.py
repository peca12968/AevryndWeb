"""Read authored legacy facial hair and independently reopen the preview."""
from pathlib import Path
import bpy,numpy as np,json,hashlib
R=Path(r'D:\Download\Aevrynd');D=R/'Reference/character/charmorph-vitruvian-cc0';E=R/'Evidence/character-female-next/r0057-coherent-foundation'
bpy.ops.wm.open_mainfile(filepath=str(D/'canonical-female-data.blend'));body=bpy.data.objects['cm_vitruvian'];rows=[];arrays={}
for si,ps in enumerate(body.particle_systems):
    curves=[np.array([key.co[:] for key in p.hair_keys],dtype='f4').reshape(-1,3) for p in ps.particles];counts=np.array([len(p) for p in curves],dtype='i4');P=np.concatenate(curves) if counts.sum() else np.empty((0,3),dtype='f4');arrays['positions'+str(si)]=P;arrays['counts'+str(si)]=counts
    rows.append({'name':ps.name,'particles':len(curves),'keyCountRange':[int(counts.min()),int(counts.max())],'emptyParticles':int((counts<2).sum()),'firstKeys':next((p[:3].tolist() for p in curves if len(p)>=2),[]),'bounds':[P.min(0).tolist(),P.max(0).tolist()] if len(P) else [],'radiusM':ps.settings.root_radius*ps.settings.radius_scale})
np.savez_compressed(E/'canonical-facial-hair.npz',**arrays)
build=json.loads((E/'a-build-summary.json').read_text());assert hashlib.sha256(Path(build['output']).read_bytes()).hexdigest()==build['outputSha256']
bpy.ops.wm.open_mainfile(filepath=build['output']);body=bpy.data.objects['AFN57_CC0_COHERENT_FEMALE_BODY'];deps=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(deps)
actual=np.array([v.co[:] for v in body.data.shape_keys.key_blocks['AFN57_Supplied_Female_Morph'].data]);data=np.load(E/'a-canonical-female-data.npz');assert np.array_equal(actual,data['female'].astype('f4'))
row={'sourceA':build['output'],'sourceSha256':build['outputSha256'],'reopened':True,'femaleShapeCoordinatesExact':True,'legacyOriginal':rows,
    'legacyReopenedCounts':[{'name':ps.name,'particles':len(ps.particles)} for ps in body.particle_systems],
    'legacyEvaluatedCounts':[{'name':ps.name,'particles':len(ps.particles)} for ps in ev.particle_systems],
    'eyeImageSamples':[],'warning':'Preview job rendered all views then terminated with native allocator error -1073740940. This reopening does not erase that failure.'}
for image in bpy.data.images:
    if 'Iris_Color' in image.name or 'Sclera_Color' in image.name:
        q=np.array(image.pixels[:],dtype='f4').reshape(-1,4)[::128];row['eyeImageSamples'].append({'name':image.name,'size':list(image.size),'colorSpace':image.colorspace_settings.name,'sampleMinRGBA':q.min(0).tolist(),'sampleMaxRGBA':q.max(0).tolist(),'sampleMeanRGBA':q.mean(0).tolist()})
(E/'a-reopened-legacy-inspection.json').write_text(json.dumps(row,indent=2)+'\n',encoding='utf8');print('R57_LEGACY_INSPECTED',json.dumps(row),flush=True)
