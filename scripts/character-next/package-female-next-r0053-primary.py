"""Archive the rejected full design and scoped root/tool research honestly."""
from pathlib import Path
import json,hashlib,shutil,datetime
from PIL import Image,ImageDraw,ImageFont
R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source'
E=R/'Evidence/character-female-next/r0053-new-primary-groom';REPO=R/'sites-engine-journey'
M=REPO/'assets-source/aevrynd-character/female-next'

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    now=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    mp=R/'engine/assets/characters/female-next/female-next.asset.json';m=read(mp)
    preserveKeys=['workingReviewRevision','workingReviewSource','workingReviewSha256','workingReviewStatus',
        'currentSourceRevision','currentSource','strictOverallScore','strictScoreAppliesTo','runtimeAsset',
        'runtimeStatus','enginePromotionApproved','websitePromotionApproved']
    preserved={name:m[name] for name in preserveKeys}
    working=S/Path(m['workingReviewSource']).name
    assert sha(working)==m['workingReviewSha256']=='b86f7eeedf6fd6a4d9a7f13ff42dc4051907516bc90be8261f02e7678242a3ff'
    root=read(E/'grown-fixed-saved-readback.json');pilot=read(E/'grown-fixed-pilot-saved-static-verification.json')
    retained=read(E/'retained-authoring-readback.json')
    assert root['rootClassificationCounts']=={'outside':64} and root['surfaceUVExactlyExpectedFloat32']
    assert root['segmentsBelowOneMicron']==0 and root['inheritedSixExact']
    assert pilot['actualFiniteBodyCapsules']['status']=='PASS_TESTED_STATIC_CAPSULES'
    assert pilot['actualFiniteMasterSelfCapsules']['overlapsBeyondNumericalAllowance']==0
    assert retained['entireVisibleCharacterStateExactR51'] and sha(Path(retained['source']))==retained['sourceSha256']
    summaries=['foundation-build.json','refined-foundation-build.json','primary-build-summary.json',
               'grown-pilot-build-summary.json','grown-fixed-pilot-build-summary.json','grown-fixed-build-summary.json']
    snapshots=[]
    for name in summaries:
        data=read(E/name);p=Path(data['output']);assert sha(p)==data['outputSha256']
        snapshots.append({'source':str(p),'sha256':sha(p),'role':name})
    snapshots.append({'source':retained['source'],'sha256':retained['sourceSha256'],'role':'Complete unchanged review appearance with hidden research'})
    # Compare rendering conditions, never present the thick diagnostic as hair.
    strip=lambda rows:[{k:v for k,v in row.items() if k!='path'} for row in rows]
    assert strip(read(E/'before-renders.json'))==strip(read(E/'grown-fixed-actual-fibres-renders.json'))
    font=ImageFont.truetype('C:/Windows/Fonts/msjh.ttc',18);small=ImageFont.truetype('C:/Windows/Fonts/msjh.ttc',16)
    def board(name,columns,views,width=500):
        h=width+38;out=Image.new('RGB',(width*len(columns),h*len(views)+118),'#181c21');draw=ImageDraw.Draw(out)
        for ri,view in enumerate(views):
            for ci,(tag,label) in enumerate(columns):
                draw.text((ci*width+8,ri*h+8),label+' / '+view,font=font,fill='white')
                out.paste(Image.open(E/f'{tag}-{view}.png').convert('RGB').resize((width,width)),(ci*width,ri*h+36))
        y=h*len(views)
        notes=['全頭造型判退：髮根外翻、支架式輪廓與硬轉折；沒有可採用的整體外觀改善。',
               '白線僅為路徑診斷，半徑1毫米；實際髮絲半徑9–55微米，未製作密集子髮。',
               '六條試驗的762段身體／自碰撞通過；64條只驗證髮根與保存資料，未驗收完整髮型接觸／動態。']
        for j,note in enumerate(notes):draw.text((9,y+10+34*j),note,font=small,fill='#e6c58a' if j==0 else '#d0d5df')
        out.save(E/name)
    columns=[('before','保留完整人物 r51 B'),('grown-fixed-actual-fibres','r53 實際64條／未增密'),('grown-fixed-path-diagnostic','r53 加粗路徑／非成品')]
    board('r0053-complete-review.png',columns,['face','body-face'])
    board('r0053-angle-review.png',columns,['oblique','profile','back'])
    reference={'sources':[
        'https://studio.blender.org/training/blender-fundamentals-45-lts/using-multiple-objects/',
        'https://studio.blender.org/training/blender-fundamentals-45-lts/fine-control/'],
        'retrieval':'Official public HTML fetched and relevant text read after web fetch402.',
        'productionDecision':'First block complete volumes, inspect orthographic silhouettes, and sculpt separate editable quad clumps using Face Sets/hiding. Use this to establish actual three-dimensional hair mass before new strand paths.',
        'scope':'These lessons use a stylized gnome. Only the blocking/editing workflow is relevant; that character is not realism evidence or an imported asset for this adult woman.',
        'noExternalGeometryOrAddonImported':True}
    write(E/'next-production-reference.json',reference)
    nextAction=(
        'Keep complete working r51B and the r53retained research container. Stop the old29r48world-station '
        'template as the shape source: long-seed tip drags retain spikes; short native extension with corrected '
        'sampling fixes technical defects but full64still form outward root arches, rigid turns and scaffold-like '
        'silhouettes. Do not densify, add strokes, tune radii/strength/normal-exit constants, or revive stopped '
        'root-frame/radial/loft/global-flow transfers. NEXT one production theme: establish a coherent complete '
        'hairstyle volume on this same head using real adult hairstyle references and Blender editable quad '
        'clump meshes/Face Sets/Grab silhouette sculpting. First choose front/profile/back design references, '
        'then one bounded8–12main-clump blockout with natural scalp-to-free flow. The coarse full-head/body '
        'shape must be convincing in orthographic and existing review views/second light before constructing '
        'new strand guides. Mesh clumps are explicit authoring proxies, not final physical hair. No shared '
        'exit ring/funnel and no oldr48/r53route positions as templates. Reuse the validated actual-skin '
        'scalp domain,64root barycentric/FLOAT2UV bindings and corrected uniform sampling only where useful; '
        'do not redo root research or use the rejected full paths. Validate all new finite paths independently '
        'before any children. Full appearance, oral/clothes/body rig, known nonocular body failures, '
        'natural hair/self/continuous dynamics and actual engine/LOD/performance remain incomplete.'
    )
    research={'purpose':'Actual anatomical scalp region,64physical root/UV anchors and editable native authoring/sampling infrastructure.',
        'scope':'64root-only actual-surface proof; six full finite static body/self master paths. Complete64shape rejected; not an accepted groom or dynamics.',
        'integration':'Hidden scoped data integrated in an independently reopened complete character with exact r51visible state.',
        'minimumIntegrationStep':'Use retained skin/root anchors with new masters derived from a convincing whole-head volume blockout. Do not reuse the rejected route geometry; test all paths before child interpolation.'}
    stopped='Oldr48world-station-directed full master groom with generic normal/tangent departure, including native short-root growth and corrected sampling, as a natural complete hairstyle.'
    audit={'revision':'female-next-r0053','decision':'REJECT_GUIDE_TEMPLATE_GROOM_RETAIN_ROOTS_AND_NATIVE_SAMPLING',
        'appearance':{'status':'REJECT_COMPLETE_COARSE_FORM','appearanceImprovement':False,'wholeCharacterScore':None,
            'observations':['Root positions are bound, but trajectories fan outward into scaffold-like arches.',
                'Crown/lateral mass and hard station turns do not read as a coherent natural hairstyle.',
                'Sparse64physical fibres are expected; rejection is about flow and silhouette, not a demand for density.'],
            'actualHeadBodyMultiangleAndSecondLight':True,'denseChildrenGenerated':False,'thickPathsAreDiagnosticsOnly':True},
        'function':{'status':'RETAIN_SCOPED_AUTHORING_ONLY','retainedSource':retained,'rootData':root,'usefulResearch':research,
            'fixedImplementationDefects':['Native UV attribute must be FLOAT2.',
                'Uneven route stations at fixed quadratic parameters caused overshoot.',
                'Tip extension produced repeated samples and a long final span; uniform path reparameterization removes it.',
                'Each new root needs its own departure, not another guide root exit.'],
            'unusedInterpolationProbe':'Guarded inspection script authored but deliberately not executed after full-form visual rejection; no interpolation asset graph loaded.'},
        'contact':{'status':'SIX_STATIC_MASTERS_AND_64_ROOTS_ONLY',
            'qualifiedPilotCurves':6,'qualifiedPilotFiniteBodySegments':762,'pilotBodyUnqualifiedSegments':0,'pilotMasterSelfOverlapPairs':0,
            'qualifiedRootPositions':64,'minimumSampledRootCapsuleGapM':root['minimumSampledRootCapsuleSurfaceGapM'],
            'full64PathsSelfOtherOpticsContinuousDynamics':'NOT_RUN_AFTER_VISUAL_REJECTION',
            'sourceBody':'Unchanged r51. Existing839nonocular tested source self pairs remain unaccepted; not a whole-body collision pass.'},
        'runtime':{'status':'NOT_TESTED_NOT_PROMOTED','cpuGpuTimeMemory':None},
        'stoppedMethod':stopped,'nextAction':nextAction,'usefulResearch':research}
    write(E/'female-next-r0053.visual-audit.json',audit)
    write(E/'continuation.json',{'stage':'B_COMPLETE_HEAD_IN_PROGRESS','previousGoalTurnClassification':read(E/'round-contract.json')['previousGoalTurnClassification'],
        'lastGoalTurnClassification':'progress','progressKind':'SCOPED_ROOT_AUTHORING_RETAINED_FULL_DESIGN_REJECTED',
        'appearanceImprovement':False,'functionalUnblocking':'Native editing and root-binding infrastructure only; no completed new character appearance/dynamics feature.',
        'workingReviewSource':str(working),'workingReviewSha256':sha(working),'latestEvidence':str(E/'female-next-r0053.visual-audit.json'),
        'retainedResearchSource':retained['source'],'retainedResearchSha256':retained['sourceSha256'],
        'liveJobHandles':[],'stoppedMethods':[stopped],'usefulResearch':research,'nextAction':nextAction,
        'wholeCharacterScore':None,'resources':{'reviewUTC':now,'blenderThreads':4,'heavyJobsAtOnce':1,'newNodeServers':0,'remoteJobs':0,
            'observedMaximumBlenderWorkingSetMB':2349,'meaning':'Sampled process working set, not instrumented peak or runtime performance.','goal':'ACTIVE_NOT_COMPLETE'},
        'remainingGates':['Credible complete appearance','Complete layered oral/clothes/body rig','Known nonocular body contacts',
            'Natural hair and full self/continuous contact','Actual engine/LOD/CPU/GPU/memory','Weighted85each80 and explicit female acceptance']})
    descriptor=S/'aevrynd-female-next-r0053-authoring.json'
    write(descriptor,{'revision':'female-next-r0053','status':audit['decision'],'completeWorkingSource':str(working),'sourceSha256':sha(working),
        'researchContainer':retained,'snapshots':snapshots,'usefulResearch':research,
        'rebuild':'Blender5.2.2 threads4. build53scalp-foundation: default coarse cage, --evaluated-boundary refined actual skin. run53primary-events needs hidden GUI --enable-event-simulate and pinnedrefined startupfile: default rejected long-tip trial; --short-grow --pilot rejected initial six; add--corrected-route qualified six; startup correctedpilot file with --short-grow --corrected-route --resume-pilot continues58. verify53primary flags match chosen trial; --readback-only for visually rejected full64, no full contact claim. retain53authoring restores original visible character and hides rejected research. Native event geometry can vary with installed build/viewport rounding; archived world/pixel gestures and output hashes are authoritative, rebuilt files need revalidation.',
        'provenance':'Existing owned/CC0character provenance unchanged. Native production tool APIs only; no Blender C++/node graph, donor geometry, add-on or service imported into engine.',
        'limits':['No complete appearance gain','No accepted full64groom','No dense children, new hair dynamics or runtime','Female not accepted']})
    m.update(latestStudyRevision='female-next-r0053',latestStudyStatus=audit['decision'],
        latestStudyEvidence=str(E/'female-next-r0053.visual-audit.json'),latestContinuation=str(E/'continuation.json'),nextRequiredWork=nextAction,
        characterAuthoringDescriptorR53='source/'+descriptor.name,
        anatomicalNativeGroomResearchSource='source/'+Path(retained['source']).name,
        anatomicalNativeGroomResearchSha256=retained['sourceSha256'],anatomicalNativeGroomResearchScope=research['scope'])
    oldProof=read(R/'Evidence/character-female-next/r0051-eye-wall/b-integrated-static-verification.json')
    assert oldProof['sourceSha256']==m['workingReviewSha256']
    # Correct stale r38shadow-only wording without changing adoption or evidence.
    m['workingReviewScope']='Retained r51B integrated posterior ocular wall and wet-tissue interface static repair; source skin/materials/stage and original hair preserved. Existing nonocular source self failures, full appearance/dynamics/runtime remain unaccepted.'
    assert all(m[name]==value for name,value in preserved.items());write(mp,m)
    contract=read(E/'round-contract.json');contract.update(reviewUTC=now,decision=audit['decision'],
        fullCoarseDesigns=2,correctedSixMasterPilot=True,denseChildrenGenerated=False,
        pilotLimitation='Six good static paths did not establish an acceptable complete hairstyle. Full64form rejects the route template.')
    write(E/'round-contract.json',contract)
    files=[]
    def cp(src,dst):
        dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);assert sha(src)==sha(dst);files.append(dst)
    for row in snapshots:cp(Path(row['source']),M/Path(row['source']).name)
    cp(descriptor,M/descriptor.name);cp(mp,M/'female-next.asset.json')
    for src in sorted(E.iterdir()):
        if src.suffix in ('.json','.npz','.png') and src.name not in ('git-paths.json','history-file-manifest.json'):
            cp(src,M/(src.name if src.name.startswith('r0053-') else 'r0053-'+src.name))
    for src in sorted((R/'scripts/character-next').glob('*female-next-r0053*.py')):cp(src,REPO/'scripts/character-next'/src.name)
    for src in sorted((R/'Evidence').glob('character-female-next-r0053-*.log')):cp(src,M/src.name)
    for src in sorted((R/'Evidence').glob('character-female-next-r0053-*.err')):cp(src,M/src.name)
    files.extend([M/'.gitattributes',REPO/'scripts/character-next/.gitattributes'])
    write(E/'history-file-manifest.json',{'revision':'female-next-r0053','files':[{'path':str(p.relative_to(REPO)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]})
    cp(E/'history-file-manifest.json',M/'r0053-history-file-manifest.json')
    write(E/'git-paths.json',sorted(str(p.relative_to(REPO)).replace('\\','/') for p in files))
    print('R53_HISTORY_READY',len(files),sum(p.stat().st_size for p in files),flush=True)

if __name__=='__main__':main()
