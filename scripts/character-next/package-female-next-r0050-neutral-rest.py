"""Archive one rejected complete neutral-eye candidate with actual A/B evidence."""
from pathlib import Path
import datetime
import hashlib
import json
import shutil
from PIL import Image, ImageDraw, ImageFont

R = Path(r'D:\Download\Aevrynd')
S = R / 'engine/assets/characters/female-next/source'
E = R / 'Evidence/character-female-next/r0050-eye-rest'
REPO = R / 'sites-engine-journey'
M = REPO / 'assets-source/aevrynd-character/female-next'

def read(p):
    return json.loads(p.read_text(encoding='utf8'))

def write(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf8')

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    mp = R / 'engine/assets/characters/female-next/female-next.asset.json'
    m = read(mp)
    preserved_keys = ['workingReviewSource', 'workingReviewRevision', 'workingReviewSha256',
                      'workingReviewStatus', 'currentSourceRevision', 'currentSource',
                      'strictOverallScore', 'strictScoreAppliesTo', 'runtimeAsset',
                      'runtimeStatus', 'enginePromotionApproved', 'websitePromotionApproved']
    preserved = {k: m[k] for k in preserved_keys}
    working = S / Path(m['workingReviewSource']).name
    assert sha(working) == m['workingReviewSha256']
    build = read(E / 'a-build-summary.json')
    proof = read(E / 'reopened-delivery-verification.json')
    contact = read(E / 'a-contact-progress.json')
    candidate = Path(build['output'])
    assert sha(candidate) == build['outputSha256'] == proof['candidateSha256'] == contact['sha256']
    assert contact['status'] == 'FAIL_BODY_SELF_OR_FIXED_OPTICS_STOP'
    assert contact['changedBodySelfBefore']['actualNonAdjacentPairs'] == 438
    assert contact['changedBodySelfAfter']['actualNonAdjacentPairs'] == 434
    assert all(row['actualSurfaceIntersectionPairs'] == 0 for row in contact['bodyOptics'].values())
    base_views, after_views = read(E / 'before-renders.json'), read(E / 'a-after-renders.json')
    strip_path = lambda rows: [{k:v for k,v in row.items() if k != 'path'} for row in rows]
    assert strip_path(base_views) == strip_path(after_views)
    views = ['face','oblique','profile','opposite-oblique','alternate-oblique','body-face','back']
    for tag in ('before','a-after'):
        for view in views:
            assert (E / f'{tag}-{view}.png').exists()

    font = ImageFont.truetype('C:/Windows/Fonts/msjh.ttc', 19)
    small = ImageFont.truetype('C:/Windows/Fonts/msjh.ttc', 17)
    columns = [('before','完整工作人物／保留 r42B 外觀'),
               ('a-after','R50A 中性眼皮試驗／判退')]
    for title, chosen in [('delivery',['face','body-face']),
                          ('angles',['oblique','profile']),
                          ('additional',['opposite-oblique','alternate-oblique','back'])]:
        board = Image.new('RGB', (1200, 640*len(chosen)+105), '#171b20')
        draw = ImageDraw.Draw(board)
        for ri, view in enumerate(chosen):
            for ci, (tag,label) in enumerate(columns):
                draw.text((600*ci+10, 640*ri+8), label+' / '+view, font=font, fill='white')
                board.paste(Image.open(E/f'{tag}-{view}.png').convert('RGB').resize((600,600)),
                            (600*ci,640*ri+38))
        draw.text((10,640*len(chosen)+10),'實際三維模型，同相機／材質／燈光／曝光；只有局部眼神變化，完整人物改善不足。',font=small,fill='#edc889')
        draw.text((10,640*len(chosen)+40),'眼部受測表面自交：來源438對、候選434對；並未通過接觸，不能以數量略降當成果。',font=small,fill='#d0d3d8')
        draw.text((10,640*len(chosen)+70),'未升分、未採用、未替換runtime／網站；不是眨眼、表情骨架或自然毛髮動態成果。',font=small,fill='#d0d3d8')
        board.save(E/f'r0050-{title}-comparison.png')

    next_action = (
        'Keep r42B as the complete working character and r48 hidden scalp/29 guides as incomplete authoring research. '
        'Do not repeat r50 angular neutral-rest amplitude sweeps: complete-face benefit was insufficient and actual '
        'changed-region source/candidate self surfaces remain unqualified (438/434 pairs). Next production theme: '
        'repair the actual eye-rim source structure before further expression shaping. Within one bounded ten-minute '
        'diagnostic locate existing self witnesses in native versus evaluated Multires layers, then make one structural '
        'rim/inner-wall repair on the complete character; use independent evidence to distinguish geometry defects '
        'from verifier assumptions. Rebuild wet-margin/lash surface bindings when the support changes; do not simply '
        'move roots, hide inner walls, flatten all sculpt detail, rescale rejected Half, or relax tolerance. '
        'Show matched full head/body views before expensive expansion. If a structural repair is visually unchanged, '
        'retain only if it genuinely removes the adoption blocker and actual affected-scope checks pass, with no '
        'appearance-score gain. Stop a falsified construction; no more support-only loop. '
        'Credible complete skin/hair, oral/body/clothes rig, natural hair dynamics, all-layer static/self/continuous '
        'contact, actual engine/LOD/CPU/GPU/memory and female acceptance remain incomplete.'
    )
    audit = {
        'revision':'female-next-r0050',
        'decision':'REJECT_A_INSUFFICIENT_COMPLETE_APPEARANCE_AND_FAILED_STATIC_BODY_SELF',
        'source':build['source'], 'sourceSha256':build['sourceSha256'],
        'candidate':str(candidate), 'candidateSha256':sha(candidate),
        'appearance':{
            'status':'INSUFFICIENT_COMPLETE_CHARACTER_GAIN', 'appearanceImprovement':False,
            'localObservation':'A slightly more relaxed neutral upper lid; no sleepy native Half adoption. The complete face remains mannequin-like; cap/sheet hair and flat skin remain obvious.',
            'matchedHeadBodyAB':True, 'multiangleAndSecondLighting':True,
            'newWholeCharacterScore':None,
            'diagnostics':'Removing cornea changes iris/catchlights but does not fix stare. Rejected r44 native Half looks sleepy and is not a full-sculpt/contact-qualified reference.'},
        'function':{
            'status':'SCOPED_AUTHORING_MECHANISM_ONLY_NO_COMPLETED_CHARACTER_FUNCTION',
            'scope':'One hidden static artist control and shared post-Multires world field on body plus ten wet/lash objects; selected value read back after reopening.',
            'zeroControlRecoversSource':build['zeroControlExactSourceRecovery'],
            'materialsSkinFieldsHairStageExact':True,
            'limitations':'Not a facial rig, blink or animation; angular injectivity of the ideal field is not finite mesh collision proof.'},
        'contact':{
            'status':'FAIL_ACTUAL_BODY_SELF_IN_AFFECTED_REGION',
            'actualSelfPairsBefore':438, 'actualSelfPairsAfter':434,
            'fixedEightOpticalSurfaceIntersectionPairs':0,
            'scope':'One neutral static evaluated full-sculpt pose, 40427 affected body triangles; nonadjacent float32 BVH pairs refined by float64 triangle intersection. Pair counts are surface-pair witnesses, not penetration volumes or exact minimum signed clearance.',
            'baselineVsNew':'Both baseline and candidate fail. Totals alone do not identify all introduced/removed pair identities. Existing defects are not exempted and no method success is claimed.',
            'uncompleted':'Wet/lash attachment, between-object and original-curve updates stopped at body gate; no full contact pass, self/dynamic/continuous qualification or global minimum distance claim.',
            'evidence':'a-contact-progress.json'},
        'runtime':{'status':'NOT_TESTED_NOT_PROMOTED','cpuGpuMemory':None},
        'methodDecision':'Stop this neutral-rest construction as a route to meaningful complete-face improvement; do not sweep angle/cap/support widths. Ideal continuous map mathematics is retained as method evidence only, not adopted as a character feature.',
        'researchDisposition':{'retainedCharacterFeature':False,
            'purpose':'Archived reproducible failure; paired material/cornea/shape observations constrain the next structural eye-rim repair.',
            'minimumIntegrationStep':'No automatic integration of this rejected candidate. Repair and independently qualify actual source eye structure first.'},
        'nextAction':next_action,
    }
    write(E/'female-next-r0050.visual-audit.json', audit)
    write(E/'continuation.json', {
        'stage':'B_COMPLETE_HEAD_IN_PROGRESS',
        'previousGoalTurnClassification':'progress: v13 prompt and handoff entries saved/pushed e85de60; prompt maintenance, no model iteration or appearance improvement',
        'lastGoalTurnClassification':'progress',
        'progressKind':'RECONCILE_RENDER_AND_REJECT_EXISTING_COMPLETE_R50A_WITH_ACTUAL_FAILURE_EVIDENCE',
        'classificationReason':'Previously unregistered complete candidate independently reopened, missing source full-character views rendered, same-stage A/B audited, actual self-contact failure reconciled and adoption rejected; stale r49 next step superseded.',
        'workingReviewSource':str(working),'workingReviewSha256':sha(working),
        'latestEvidence':str(E/'female-next-r0050.visual-audit.json'),
        'appearanceImprovement':False,'functionalUnblocking':'None; source eye-rim structure still blocks adoption.',
        'usefulResearch':audit['researchDisposition'], 'latestSources':[str(candidate)],
        'liveJobHandles':[], 'nextAction':next_action,
        'resources':{'originalProductionStartUTC':'2026-10-19 16:58:10 UTC',
                     'reconciliationStartUTC':'2026-10-19 17:22:47 UTC',
                     'reviewUTC':now,'blenderThreads':4,'heavyJobsAtOnce':1,
                     'completeCandidates':1,'newNodeServers':0,'remoteJobs':0,
                     'goal':'ACTIVE_NOT_COMPLETE'},
        'wholeCharacterScore':None,
        'remainingGates':['Credible complete head/body appearance','Full layered editable/rigged character',
                          'All-layer static/self/continuous motion contact','Natural hair dynamics',
                          'Actual Aevrynd runtime/LOD/performance','Weighted85 each80 and explicit female acceptance'],
    })
    desc = S/'aevrynd-female-next-r0050-authoring.json'
    write(desc, {'revision':'female-next-r0050','status':audit['decision'],
        'source':build['source'],'sourceSha256':build['sourceSha256'],
        'candidate':str(candidate),'candidateSha256':sha(candidate),
        'control':build['control'],'attribute':build['attribute'],
        'selectedAngleRad':build['selectedAngleRad'],
        'rebuild':'Installed Blender5.2.2 background --disable-autoexec --threads4. inspect50eye-appearance, build50neutral-rest, verify50neutral-rest (expected body-self failure stop), finish50baseline. Package with bundled Python/Pillow. No new add-on/service.',
        'use':'Historical rejected study, not a replacement complete working character or runtime.',
        'provenance':'Own deformation code on existing source. Existing material/texture/hair provenance unchanged; no new external asset imported.',
        'limits':proof['limits']})
    m.update(latestStudyRevision='female-next-r0050',latestStudyStatus=audit['decision'],
             latestStudyEvidence=str(E/'female-next-r0050.visual-audit.json'),
             latestContinuation=str(E/'continuation.json'),nextRequiredWork=next_action,
             characterAuthoringDescriptorR50='source/'+desc.name,
             rejectedNeutralEyeRestSource='source/'+candidate.name,
             rejectedNeutralEyeRestSha256=sha(candidate))
    assert all(m[k] == value for k,value in preserved.items())
    write(mp,m)
    files=[]
    def cp(src,dst):
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dst)
        assert sha(src)==sha(dst)
        files.append(dst)
    cp(candidate,M/candidate.name)
    cp(desc,M/desc.name)
    cp(mp,M/'female-next.asset.json')
    reports=['round-contract.json','a-build-summary.json','continuous-map-bound.json',
             'appearance-falsification.json','a-contact-progress.json',
             'reopened-delivery-verification.json','female-next-r0050.visual-audit.json','continuation.json']
    for name in reports:
        cp(E/name,M/('r0050-'+name))
    for tag in ('before','a-after'):
        cp(E/f'{tag}-renders.json',M/f'r0050-{tag}-renders.json')
        for view in views+['eyes']:
            cp(E/f'{tag}-{view}.png',M/f'r0050-{tag}-{view}.png')
    for tag in ('diagnostic-no-cornea','reference-rejected-native-half'):
        for suffix in ('-face.png','-eyes.png','-renders.json'):
            cp(E/(tag+suffix),M/('r0050-'+tag+suffix))
    for title in ('delivery','angles','additional'):
        name=f'r0050-{title}-comparison.png'
        cp(E/name,M/name)
    for name in ('inspect-female-next-r0050-eye-appearance.py','build-female-next-r0050-neutral-rest.py',
                 'verify-female-next-r0050-neutral-rest.py','finish-female-next-r0050-baseline.py',
                 'package-female-next-r0050-neutral-rest.py'):
        cp(R/'scripts/character-next'/name, REPO/'scripts/character-next'/name)
    for suffix in ('eye-inspection','neutral-build','neutral-verification','delivery'):
        name=f'character-female-next-r0050-{suffix}.log'
        cp(R/'Evidence'/name,M/name)
    snapshot={'revision':'female-next-r0050','workingSourceUnchanged':True,
              'files':[{'path':str(p.relative_to(REPO)).replace('\\','/'),
                        'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]}
    write(E/'history-file-manifest.json',snapshot)
    cp(E/'history-file-manifest.json',M/'r0050-history-file-manifest.json')
    write(E/'git-paths.json',sorted(str(p.relative_to(REPO)).replace('\\','/') for p in files))
    print('R50_HISTORY_READY',len(files),sum(p.stat().st_size for p in files))

if __name__ == '__main__':
    main()
