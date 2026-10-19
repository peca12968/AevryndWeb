"""Retain integrated static ocular repair, no appearance/formal/runtime promotion."""
from pathlib import Path
import json,hashlib,shutil,datetime
from PIL import Image,ImageDraw,ImageFont,ImageChops,ImageStat

R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source'
E=R/'Evidence/character-female-next/r0051-eye-wall'
OLD=R/'Evidence/character-female-next/r0050-eye-rest'
REPO=R/'sites-engine-journey';M=REPO/'assets-source/aevrynd-character/female-next'

def read(p):return json.loads(p.read_text(encoding='utf8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    now=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    mp=R/'engine/assets/characters/female-next/female-next.asset.json';m=read(mp)
    preserve={k:m[k] for k in ('currentSourceRevision','currentSource','strictOverallScore','strictScoreAppliesTo',
                              'runtimeAsset','runtimeStatus','enginePromotionApproved','websitePromotionApproved')}
    previousWorking={k:m[k] for k in ('workingReviewRevision','workingReviewSource','workingReviewSha256','workingReviewStatus')}
    assert m['workingReviewRevision']=='female-next-r0042-b'
    assert sha(S/Path(m['workingReviewSource']).name)==m['workingReviewSha256']
    proof=read(E/'b-integrated-static-verification.json');body=read(E/'b-saved-static-verification.json')
    build=read(E/'b-integrated-build-summary.json');raw=read(E/'b-build-summary.json');aa=read(E/'a-build-summary.json')
    source=Path(build['output']);assert sha(source)==proof['sourceSha256']==build['outputSha256']
    assert proof['status']=='PASS_STATED_OCULAR_REPAIR_AND_REBOUND_INTERFACES_NOT_FULL_CHARACTER'
    assert proof['ocularSelfPairs']==proof['fixedOpticalSurfacePairs']==proof['newOtherBodyIntersectingQuadPairs']==0
    assert proof['existingOtherBodySurfaceSelfPairs']==839
    assert sum(row['segments'] for row in proof['originalHairBodyCapsules'].values())==1544700
    assert all(row['unqualifiedSegments']==0 and not row['rootFailures'] for row in proof['originalHairBodyCapsules'].values())
    assert all(row['actualBodyAttachment']['unqualifiedNonAttachmentPairs']==0 for row in proof['rebuiltWetTissues'].values())
    assert read(OLD/'reopened-delivery-verification.json')['sourceSha256']==aa['sourceSha256']
    views=['face','oblique','profile','opposite-oblique','alternate-oblique','body-face','back','eyes']
    baseline=[]
    for view in views:
        src=OLD/f'before-{view}.png';dst=E/src.name;shutil.copy2(src,dst)
        baseline.append({'view':view,'actualOriginalRender':str(src),'sha256':sha(src),'copiedForComparisonOnly':True})
    shutil.copy2(OLD/'before-renders.json',E/'before-renders.json')
    strip=lambda rows:[{k:v for k,v in row.items() if k!='path'} for row in rows]
    for tag in ('a-after','b-after','b-integrated'):
        assert strip(read(E/f'{tag}-renders.json'))==strip(read(E/'before-renders.json'))
    write(E/'baseline-provenance.json',{'source':aa['source'],'sourceSha256':aa['sourceSha256'],
        'basis':'Reuse actual pinned r48 complete source views from r50; identical camera/stage/material metadata, no new baseline improvement claim.',
        'files':baseline})
    font=ImageFont.truetype('C:/Windows/Fonts/msjh.ttc',19);small=ImageFont.truetype('C:/Windows/Fonts/msjh.ttc',17)
    for title,chosen in [('delivery',['face','body-face']),('angles',['oblique','profile']),
                         ('additional',['opposite-oblique','alternate-oblique','back'])]:
        board=Image.new('RGB',(1200,640*len(chosen)+105),'#171b20');d=ImageDraw.Draw(board)
        for ri,view in enumerate(chosen):
            for ci,(tag,label) in enumerate([('before','修復前／r42B外觀、r48研究分層'),('b-integrated','修復後／B眼內壁與接合整合')]):
                d.text((600*ci+10,640*ri+8),label+' / '+view,font=font,fill='white')
                board.paste(Image.open(E/f'{tag}-{view}.png').convert('RGB').resize((600,600)),(600*ci,640*ri+38))
        d.text((10,640*len(chosen)+10),'實際完整人物，同相機／材質／光線／曝光；這輪是結構修復，沒有外觀升分。',font=small,fill='#edc889')
        d.text((10,640*len(chosen)+40),'完整受測眼區自交715→0；眼球與重綁接合通過。其他受測身體仍有839對原有自交。',font=small,fill='#d0d3d8')
        d.text((10,640*len(chosen)+70),'採用為有缺口的完整工作來源；不是完整碰撞、動態、引擎或女性最終驗收。',font=small,fill='#d0d3d8')
        board.save(E/f'r0051-{title}-comparison.png')
    imageMetrics={}
    for view in views:
        diff=ImageChops.difference(Image.open(E/f'before-{view}.png').convert('RGB'),Image.open(E/f'b-integrated-{view}.png').convert('RGB'))
        imageMetrics[view]={'meanAbsoluteRgbDifference0To255':ImageStat.Stat(diff).mean,
                            'interpretation':'Render pixel difference only; not a realism score or evidence of appearance gain.'}
    write(E/'render-comparison-metrics.json',imageMetrics)
    nextAction=(
        'Use r51 B integrated as the single complete working character: actual ocular posterior self715->0, '
        'eight fixed optics and six rebound wet-tissue joins qualified in neutral scope; original12,900scalp/brow '
        'curves1,544,700finite body capsules rechecked. Do not revive A unchanged-sculpt fairing, vertex-only '
        'optical clearance, r50 neutral-angle sweeps or old closed-lid solvers. Existing839nonocular surface '
        'pairs in changed/rounding scope remain unresolved; do not call global body contact passed. '
        'Next visible production theme: complete hairstyle large forms and scalp transition. Reassess actual full '
        'head/body views and the already retained r48 same-head guides/domain, select one complete style, and '
        'use an actually demonstrated Blender-native guide/sculpt/interpolation workflow rather than repeating '
        'stopped root-frame, radial-chart, world-knot or global wave constructions. First prove an anatomical '
        'scalp attachment and a small set of actual finite full paths plus a complete-head silhouette before '
        'dense followers; reject visibly cap/sheet/wire shapes immediately. Bound method validation to ten '
        'minutes and obtain a visible preview or falsification by the45-minute checkpoint. Explicitly report '
        'incomplete r48sideburn/temple/nape coverage; retained studies are not a finished groom. '
        'Keep skin brightness/material/stage fixed, independently check changed self/body/optical/attachment '
        'contacts before retaining; no dynamics claims without actual clip and continuous evidence. '
        'Face/skin realism, whole-body/clothes/oral rig, natural hair physics, remaining body/self/continuous '
        'contacts, Aevrynd runtime/LOD/performance, weighted85each80 and explicit female acceptance remain incomplete.'
    )
    audit={'revision':'female-next-r0051','decision':'RETAIN_INTEGRATED_B_STATIC_OCULAR_FUNCTION_REPAIR_NO_APPEARANCE_PROMOTION',
        'workingSource':str(source),'workingSourceSha256':sha(source),'previousWorking':previousWorking,
        'appearance':{'status':'NO_CLAIMED_COMPLETE_CHARACTER_APPEARANCE_GAIN','wholeCharacterImproved':False,
                     'observation':'Complete face/body appearance essentially unchanged. Staring expression, cap/sheet hair and flat skin remain major defects.',
                     'matchedFullHeadBodyAB':True,'otherAnglesAndSecondLight':True,'wholeCharacterScore':None},
        'function':{'status':'POSTERIOR_EYE_WALL_REPAIR_AND_WET_SOURCE_REBIND_INTEGRATED',
                    'nativeChangedVertices':len(aa['nativeChangedVertices']),
                    'editableNativeTopologyAndUVPreserved':True,'nativeMultiresRebuilt':True,
                    'noPermanentCorrectiveModifierOrService':True,'reboundTissues':build['reboundTissues'],
                    'limits':'Static neutral repair, not an expression/skeletal rig, blink or bone-following motion.'},
        'contact':{'status':'PASS_OCULAR_AND_REBOUND_INTERFACE_SCOPE_OTHER_BODY_FAILURES_REMAIN',
                   'sourceCompleteOcularSelfPairs':715,'repairedCompleteOcularSelfPairs':0,
                   'sourceCountScopeNote':'r50 reported438in a narrower moved-eye region; r51 tests both complete ocular regions against full body, hence source715. Do not compare mismatched scopes.',
                   'fixedOpticalPairs':0,'wetUnqualifiedAttachmentPairs':0,
                   'sourceOtherBodyFailures':body['inheritedOtherBodySelfContacts'],
                   'remainingOtherBodySurfacePairsInTestedChangedScope':839,
                   'hairCurves':12900,'hairBodyFiniteSegments':1544700,'hairBodyUnqualifiedSegments':0,
                   'evidence':str(E/'b-integrated-static-verification.json'),
                   'limit':'No full-character static/dynamic collision acceptance; counts are surface pairs, not exact global signed minimum distances.'},
        'runtime':{'status':'NOT_TESTED_NOT_PROMOTED','cpuGpuMemory':None},
        'candidateDecisions':{'A':'Reject retained-sculpt native fairing: coarse self/optics0 but actual high-sculpt4684self pairs.',
                              'B_raw':'Useful native Multires posterior rebase; eye scope0 but original wet interfaces fail after measured float rounding. Not adopted alone.',
                              'B_integrated':'Rebind six wet base/raised surfaces to actual rebuilt body; exact shared-source/barycentric interfaces pass original1um allowance. Retain as same complete working character with explicit remaining failures.'},
        'retainedStudies':{'r48':'Initial source scalp domain and29same-head authoring guides remain hidden research. Body rounding changes source domain triangles by measured submicrometre amounts; source lineage exact but this is not an accepted new root/path groom.',
                           'maximumScalpDomainSourceDeviationM':body['r48ScalpDomainTriangleMaximumDeviationM']},
        'stoppedMethods':['Vertex-only posterior optical clearance','Native posterior fairing while blindly retaining damaged sculpt displacement'],
        'nextAction':nextAction}
    write(E/'female-next-r0051.visual-audit.json',audit)
    write(E/'round-contract.json',{'intentStartUTC':'2026-10-19 17:27:07 UTC','consolidatedUTC':now,
        'intentRecordedBeforeWork':'User-facing commentary: bounded native versus sculpt source diagnosis, one structural repair with full-character/interface evidence.',
        'source':aa['source'],'sourceSha256':aa['sourceSha256'],
        'theme':'Posterior eye-wall source structure and required surface reattachment',
        'expectedOutcome':'Remove actual ocular self contacts while preserving complete-character appearance; functional retention only if actual affected checks pass.',
        'constructionCount':2,'dependencyIntegration':'B wet joins rebuilt as required integration, not a third style or parameter sweep.',
        'cheapFalsification':'Native hierarchy plus actual full optical mesh contact; independent undisplaced topology proof before B reshape.',
        'limits':'One heavy Blender,4threads,10-minute diagnostic,45-minute resource checkpoint. No new service/add-on.'})
    write(E/'reference-notes.json',{'sources':[
        {'url':'https://doc.cgal.org/latest/Surface_mesh_parameterization/index.html','access':'Fetched official manual',
         'basis':'Positive weights and convex border can support planar injectivity; neither a physical concave boundary nor our3D sculpt is certified by that theorem. Actual mesh tests decide.'},
        {'url':'https://docs.blender.org/manual/en/4.4/modeling/modifiers/generate/multiresolution.html','access':'Official indexed result; direct fetch failedHTTP402',
         'basis':'Not treated as fetched documentation. Installed Blender5.2.2 multires_reshape execution, exact full quad correspondence and actual readbacks independently establish this implementation.'}],
        'externalAssetsImported':False})
    write(E/'continuation.json',{'stage':'B_COMPLETE_HEAD_IN_PROGRESS',
        'previousGoalTurnClassification':'progress: r50 complete candidate reconciled/rejected and pushed80f03f3; no appearance gain',
        'lastGoalTurnClassification':'progress','progressKind':'INTEGRATED_COMPLETE_CHARACTER_STATIC_OCULAR_SOURCE_REPAIR',
        'appearanceImprovement':False,'functionalUnblocking':'Actual posterior self715->0 and required wet source joins rebuilt/verified; native editable Multires retained.',
        'workingReviewSource':str(source),'workingReviewSha256':sha(source),
        'latestEvidence':str(E/'female-next-r0051.visual-audit.json'),'integrationGaps':audit['retainedStudies'],
        'existingContactFailures':audit['contact']['sourceOtherBodyFailures'],
        'latestSources':[aa['output'],raw['output'],str(source)],'liveJobHandles':[],
        'nextAction':nextAction,'wholeCharacterScore':None,
        'resources':{'startUTC':'2026-10-19 17:27:07 UTC','checkpointUTC':'2026-10-19 18:12:07 UTC',
                     'reviewUTC':now,'blenderThreads':4,'heavyJobsAtOnce':1,'newNodeServers':0,'remoteJobs':0,
                     'fullHairBodyVerificationSeconds':body['seconds'],'goal':'ACTIVE_NOT_COMPLETE'},
        'stoppedMethods':audit['stoppedMethods'],
        'remainingGates':['Credible complete appearance','Full layered oral/body/clothes rig','Natural hair/self/continuous motion',
                          'Existing nonocular body self contacts','Actual Aevrynd runtime/LOD/CPU/GPU/memory','Weighted85 each80 and female acceptance']})
    descriptor=S/'aevrynd-female-next-r0051-authoring.json'
    write(descriptor,{'revision':'female-next-r0051','status':audit['decision'],
        'workingSource':str(source),'workingSourceSha256':sha(source),'baseSource':aa['source'],'baseSourceSha256':aa['sourceSha256'],
        'variants':[{'source':aa['output'],'sha256':aa['outputSha256'],'decision':'REJECT_HIGH_SCULPT_SELF'},
                    {'source':raw['output'],'sha256':raw['outputSha256'],'decision':'UNINTEGRATED_B_REBASE_WET_JOINS_FAIL'},
                    {'source':str(source),'sha256':sha(source),'decision':audit['decision']}],
        'rebuild':'Installed Blender5.2.2 --disable-autoexec --threads4: inspect51source; build51wall; verify51wall(A expectedfail); probe51rebase; build51rebased; verify51wall --variant-b (expectedraw wetfailure); integrate51; verify51integrated. Bundled Python/Pillow package51. Temporary decoded NPZ is reproducible from pinned sources; not a runtime dependency.',
        'provenance':'Existing CC0 body/texture and own code/groom; original provenance remains. No new external model, code library, service or software installed.',
        'limits':proof['limits'],'embeddedSceneStatus':'Saved scene label reflects pre-verification creation; current scoped adoption is in manifest and visual audit.'})
    m.update(workingReviewRevision='female-next-r0051-b-integrated',workingReviewSource='source/'+source.name,
        workingReviewSha256=sha(source),workingReviewStatus='RETAIN_SCOPED_STATIC_OCULAR_REPAIR_OTHER_CONTACTS_UNACCEPTED',
        latestStudyRevision='female-next-r0051',latestStudyStatus=audit['decision'],
        latestStudyEvidence=str(E/'female-next-r0051.visual-audit.json'),latestContinuation=str(E/'continuation.json'),
        nextRequiredWork=nextAction,characterAuthoringDescriptorR51='source/'+descriptor.name,
        previousCompleteWorkingReview=previousWorking)
    assert all(m[k]==v for k,v in preserve.items());write(mp,m)
    write(E/'local-cache-policy.json',{'path':str(E/'local-source-cache.npz'),
        'bytes':(E/'local-source-cache.npz').stat().st_size,
        'policy':'Local disposable source hierarchy arrays; re-created by inspect51 from pinned sources. No new Blender/runtime dependency. Do not duplicate in Git.'})
    files=[]
    def cp(src,dst):
        dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);assert sha(src)==sha(dst);files.append(dst)
    for path in (Path(aa['output']),Path(raw['output']),source,descriptor):cp(path,M/path.name)
    cp(mp,M/'female-next.asset.json')
    reports=['source-hierarchy.json','a-point-only-rejected.json','a-coarse-feasibility.json','a-build-summary.json',
             'a-saved-static-verification.json','b-rebase-feasibility.json','b-build-summary.json','b-saved-static-verification.json',
             'b-integrated-build-summary.json','b-integrated-static-verification.json','baseline-provenance.json',
             'render-comparison-metrics.json','round-contract.json','reference-notes.json','female-next-r0051.visual-audit.json',
             'continuation.json','local-cache-policy.json']
    for name in reports:cp(E/name,M/('r0051-'+name))
    for tag in ('before','a-after','b-after','b-integrated'):
        cp(E/f'{tag}-renders.json',M/f'r0051-{tag}-renders.json')
        for view in views:cp(E/f'{tag}-{view}.png',M/f'r0051-{tag}-{view}.png')
    for title in ('delivery','angles','additional'):
        name=f'r0051-{title}-comparison.png';cp(E/name,M/name)
    scripts=['inspect-female-next-r0051-eye-source.py','build-female-next-r0051-eye-wall.py',
             'probe-female-next-r0051-rebase.py','build-female-next-r0051-rebased-wall.py',
             'verify-female-next-r0051-eye-wall.py','integrate-female-next-r0051-eye-wall.py',
             'verify-female-next-r0051-integrated.py','package-female-next-r0051-eye-wall.py']
    for name in scripts:cp(R/'scripts/character-next'/name,REPO/'scripts/character-next'/name)
    for tag in ('source','build','verify','rebase-probe','rebase-build','verify-b','integrate','integrated-verify'):
        name=f'character-female-next-r0051-{tag}.log';cp(R/'Evidence'/name,M/name)
    snapshot={'revision':'female-next-r0051','files':[{'path':str(p.relative_to(REPO)).replace('\\','/'),
        'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]}
    write(E/'history-file-manifest.json',snapshot);cp(E/'history-file-manifest.json',M/'r0051-history-file-manifest.json')
    write(E/'git-paths.json',sorted(str(p.relative_to(REPO)).replace('\\','/') for p in files))
    print('R51_HISTORY_READY',len(files),sum(p.stat().st_size for p in files))

if __name__=='__main__':main()
