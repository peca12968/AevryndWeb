"""Reopen full saved owned model, prove exact geometry/material/control state,
then produce complete matched before/after views from saved files. Separately
reopen r41's PRIVATE rejected native pilot, never archive its geometry/images.
"""
import bpy,importlib.util,json,time,sys
from pathlib import Path
import numpy as np
from mathutils.bvhtree import BVHTree
sp=importlib.util.spec_from_file_location('quality42v',Path(__file__).with_name('build-female-next-r0042-shadow-quality.py'));q=importlib.util.module_from_spec(sp);sp.loader.exec_module(q)
a=q.a;f=q.f;b=q.b;E=q.E;v=q.v;ch=a.i.i.ch;m=ch.rod.m
def record():
    hair=bpy.data.objects[f.OLD];p,r=m.eval_arrays(hair);helpers={}
    for name in (m.GUIDE,m.REST):
        o=bpy.data.objects[name];gp,gr=v.hair_arrays(o);helpers[name]={'positions':f.sha(gp),'radii':f.sha(gr),'matrix':b.matrix(o.matrix_world),'materials':[x.name for x in o.data.materials]}
    return {'state':f.state(),'evaluatedHair':{'positions':f.sha(p),'radii':f.sha(r),'curves':len(p),'points':int(p.shape[0]*p.shape[1]),'finite':bool(np.isfinite(p).all() and np.isfinite(r).all())},'helpers':helpers,'config':b.config(bpy.context.scene)}
def poseRows(rows):return [{k:x[k] for k in ('view','cameraMatrix','lens','resolution')} for x in rows]
def main():
    start=time.time();summary=json.loads((E/'b-build-summary.json').read_text());assert b.sha(q.OUT)==summary['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(q.OUT));s=bpy.context.scene;after=record();candidateLight=[a.light(o) for o in s.objects if o.type=='LIGHT'];expected=after['config']['eevee'];assert expected['taa_render_samples']==256 and expected['use_shadow_jitter_viewport'];assert all(x['jitter'] and x['shadow'] for x in candidateLight);assert s.render.hair_type=='STRIP' and s.render.hair_subdiv==0
    for o in s.objects:
        if o.type=='LIGHT':o.data.use_shadow_jitter=False
    s.eevee.taa_render_samples=64;s.eevee.use_shadow_jitter_viewport=False;restored=record()
    bpy.ops.wm.open_mainfile(filepath=str(a.SRC));original=record();assert restored==original;assert after['evaluatedHair']==original['evaluatedHair'] and after['helpers']==original['helpers']
    originalLights=[a.light(o) for o in bpy.context.scene.objects if o.type=='LIGHT']
    assert [{k:x for k,x in row.items() if k!='jitter'} for row in originalLights]==[{k:x for k,x in row.items() if k!='jitter'} for row in candidateLight]
    f.E=E;f.render('verified-before');beforeHead=json.loads((E/'verified-before-renders.json').read_text());beforeExtra=ch.review.extras('verified-before',E)
    bpy.ops.wm.open_mainfile(filepath=str(q.OUT));f.render('verified-after');afterHead=json.loads((E/'verified-after-renders.json').read_text());afterExtra=ch.review.extras('verified-after',E)
    assert poseRows(beforeHead)==poseRows(afterHead)
    assert [{k:x[k] for k in ('view','camera','lens','resolution')} for x in beforeExtra]==[{k:x[k] for k in ('view','camera','lens','resolution')} for x in afterExtra]
    #Original stage excludes new renderer flags? Compare only physical lights
    #above; the intentional renderer-quality difference is explicitly recorded.
    a.save('saved-full-character-verification.json',{'source':str(a.SRC),'sourceSha256':b.sha(a.SRC),'candidate':str(q.OUT),'candidateSha256':b.sha(q.OUT),'exactOriginalFullStateWhenOnly3JitterAnd2QualityFlagsRestored':True,'allOriginalMeshesUVMaterialsSkinFieldsAndStageRestoredExact':True,'evaluatedHairRestExact':after['evaluatedHair'],'liveGuideAndRestHelpersExact':after['helpers'],'hairPrimitive':'STRIP','hairSubdivision':0,'allCameraPoseResolutionMatched':True,'originalLights':originalLights,'newLights':candidateLight,'changes':{'light.use_shadow_jitter':[False,True],'eevee.taa_render_samples':[64,256],'eevee.use_shadow_jitter_viewport':[False,True]},'fixedExposure':original['config']['exposure'],'fixedColorTransform':original['config']['transform'],'matchedHeadRows':poseRows(afterHead),'matchedAdditionalViews':[{k:x[k] for k in ('view','camera','lens','resolution')} for x in afterExtra],'contactScope':'No new geometry/contact scope. Only existing exact-version neutral evidence may carry over; all-child/self/continuous and natural motion/runtime remain unqualified.','seconds':time.time()-start})
    if '--with-private-pilot' not in sys.argv:
        print('R42_VERIFIED_FULL_OWNED_MODEL',time.time()-start,flush=True);return
    #Optional independent native pilot proof; no private input is needed for
    #constructing or verifying the owned full model above.
    E41=E.parent/'r0041-complete-path-groom';pilotBuild=json.loads((E41/'b-build-summary.json').read_text());pilotFile=Path(pilotBuild['nativePilotOutput']);assert b.sha(pilotFile)==pilotBuild['nativePilotSha256'];bpy.ops.wm.open_mainfile(filepath=str(pilotFile));o=bpy.data.objects['AFN41_B_PRIVATE_ACTUAL_PILOT'];p,r=ch.ad.read_native(o);V,T=b.evaluated(bpy.data.objects[b.BODY],True);tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True);proof=f.flowcheck.check(p,r,tree,V[T]);assert proof['unqualifiedSegments']==10 and len(p)==256
    a.save('r41-pilot-reopened-summary.json',{'source':str(pilotFile),'sha256':b.sha(pilotFile),'curves':len(p),'body':{k:proof[k] for k in ('status','curves','segments','unqualifiedSegments','minimumSampledCVSurfaceGapM','minimumCertifiedClearanceLowerBoundM')},'savedState':'Initial10failure native pilot, further nonlinear-map midpoint provedinside. No full hairstyle expanded.','privateOnly':True})
    print('R42_VERIFIED_FULL_MODEL_AND_REJECTED_PILOT',time.time()-start,flush=True)
def inventory():
    bpy.ops.wm.open_mainfile(filepath=str(q.OUT));s=bpy.context.scene;private=[o.name for o in bpy.data.objects if o.name.startswith(('AFN39_','AFN40_','AFN41_'))];assert not private
    images=[{'name':im.name,'packed':bool(im.packed_file),'source':im.source,'size':list(im.size)} for im in bpy.data.images if im.source=='FILE']
    lights=[o for o in s.objects if o.type=='LIGHT'];a.save('owned-source-inventory.json',{'source':str(q.OUT),'sha256':b.sha(q.OUT),'noPrivateGroomStudyObjects':True,'origin':'Build opens only pinned ownedr38B, thenr42A; no third-party groom library or private data appended.','fileImages':images,'linkedLibraries':[lib.filepath for lib in bpy.data.libraries],'objectTypeCounts':{k:sum(o.type==k for o in bpy.data.objects) for k in sorted(set(o.type for o in bpy.data.objects))},'localRNADocumentation':{'light.use_shadow_jitter':lights[0].data.bl_rna.properties['use_shadow_jitter'].description,'eevee.taa_render_samples':s.eevee.bl_rna.properties['taa_render_samples'].description,'eevee.use_shadow_jitter_viewport':s.eevee.bl_rna.properties['use_shadow_jitter_viewport'].description},'scope':'Source inventory only, no engine portability/performance qualification.'})
    print('R42_OWNED_SOURCE_INVENTORY_PASS',flush=True)
if __name__=='__main__':
    if '--inventory-only' in sys.argv:inventory()
    else:main()
