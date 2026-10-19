"""Archive owned r39 failures and source-transfer findings; no private data."""
import json,hashlib,shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0039-complete-guides';PVT=E/'private'
REPO=R/'sites-engine-journey';M=REPO/'assets-source/aevrynd-character/female-next'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def font(n):return ImageFont.truetype('C:/Windows/Fonts/msjh.ttc',n)
def layout(folder,name,left,right,titles,views,lines):
    out=Image.new('RGB',(1200,660*len(views)+110),(22,25,30));d=ImageDraw.Draw(out)
    for row,view in enumerate(views):
        for col,(prefix,title) in enumerate(zip((left,right),titles)):
            x=col*600;y=row*660;d.text((x+12,y+8),title,font=font(19),fill='white');d.text((x+12,y+35),view,font=font(16),fill=(185,196,209))
            out.paste(Image.open(folder/f'{prefix}-{view}.png').convert('RGB').resize((600,600),Image.Resampling.LANCZOS),(x,y+60))
    for j,line in enumerate(lines):d.text((12,660*len(views)+10+j*31),line,font=font(17),fill=(239,205,152) if j==0 else (190,201,213))
    out.save(folder/name)
def main():
    ownA=read(E/'a-build.json');ownB=read(E/'b-build.json');private=read(E/'private-study-summary.json');check=read(E/'matched-additional-views.json');assert check['matched']
    manifest_path=S.parent/'female-next.asset.json';manifest=read(manifest_path);assert manifest['workingReviewRevision']=='female-next-r0038-b'
    working=S/'aevrynd-female-next-r0038-b-live-groom-authoring.blend';assert sha(working)==manifest['workingReviewSha256']
    for d in (ownA,ownB):assert sha(Path(d['output']))==d['outputSha256']
    private_source=Path(private['C1']['path']);assert sha(private_source)==private['C1']['sha256']
    for lab in ('a','b'):
        layout(E,f'r0039-{lab}-rejected-head-comparison.png','before',lab+'-after',('r38 B／保留的完整工作人物',f'r39 {lab.upper()}／已判退自有候選'),('face','oblique','profile'),
          ['判退：帽殼、平滑髮簾或條帶；代表接觸通過不等於外觀改善。','同12000根、半徑、材質、光線、曝光與人物；完整子髮／自碰撞／動態／引擎未驗收。'])
        layout(E,f'r0039-{lab}-rejected-additional-comparison.png','before',lab+'-after',('原完整工作人物',f'r39 {lab.upper()}／已判退研究'),('opposite-oblique','alternate-oblique','body-face','back'),
          ['固定拍攝條件的其他角度與全身來源檢視；本輪未更換主工作人物。','全身、衣物、骨架、動態與引擎仍未驗收。'])
    layout(PVT,'r0039-private-artist-transfer-head-comparison.png','c-private-before','c1-private',('同11223根／原髮型對照','人工梳理範例轉接／私人研究'),('face','oblique','profile'),
       ['原髮型：Daniel Bystedt，Blender Hair Styles demo；Aevrynd僅做轉接／表面變形。','資料標示CC BY-SA但版本未核定；衍生檔未公開、未升為正式資產。','接觸未通過：256根代表髮絲仍有199段未合格；非完整子髮／自碰撞／動態驗收。'])
    layout(PVT,'r0039-private-artist-transfer-additional-comparison.png','c-private-before','c1-private',('同11223根／原髮型對照','Daniel Bystedt髮型轉接研究'),('opposite-oblique','alternate-oblique','body-face','back'),
       ['原髮型為他人作品；這是本機轉接研究，不是已完成的自有引擎角色。','授權版本與接觸仍未驗收；不替換主線、runtime或網站。'])
    decision='REJECT_OWN_STYLES_RETAIN_PRIVATE_TRANSFER_FINDINGS_ONLY'
    next_action=('Keep r38B live-groom-authoring as the ONE owned complete working source, r37C fallback. r39A/B are rejected, no appearance score increase. '
       'Do not repeat smooth global free-control grids, angular patch contraction/offset patterns or shader/density changes. '
       'PrivateC1 uses DanielBystedt HairStyles geometry and remains unadopted: actual hair flow is more natural, but license version is unspecified and256representatives still have199unqualified body segments. '
       'Source raw376guides independently show472unqualified surface-capsule segments;71are after20mm from roots,58of those are centerline crossings. No blanketroot exception is justified. Donor head is open, so nearest-normal sign/depth diagnostics are not signed-volume proof. '
       'C2 global contact fitting was NOT applied: required27.94mm at a crown point90.6mm along a101.3mmstrand inside the current closed head, exceeding the prior12mm repair guard. Do not just increase that guard or claim corrected pose. '
       'Next concrete production: inspect/re-author the specific complete raw3Dguide paths with late body crossings on the actual head, preserving good artist flow; distinguish genuine follicle joins from later crossings without arbitrary exclusions. Test all guide paths first, then generate/bake followers with explicit same-scalp-island guide lineage and independently verify all actual displayed children/body/optics/tissues/brows/lashes/self contacts. '
       'Do not blindly reuse original generated children or transfer a private study into formal assets. Resolve exact upstream terms or documented compatible attribution/share-alike handling before any public derivative data or runtime adoption; existing private study can support work without an inaccessible source-search loop. '
       'No further generic tooling, vendor hunt or whole-head parameter sweep. Retain current face/eye/skin layers and source exposure. Full hair dynamics, facial/oral/body/clothing rig, continuous contacts, rebuildable engine/LOD/performance, weighted85each80 and female user acceptance remain required; no male work or website/runtime promotion.')
    audit={'revision':'female-next-r0039','decision':decision,'workingSource':str(working),'workingSourceSha256':sha(working),
      'appearance':{'acceptedOwnedImprovement':False,'newOverallScore':None,'A':'Rounded continuous cap remains under both EEVEE and matched Cycles/Huang; rejected.','B':'Intentional gaps become visible bands/curtains, insufficient full-head naturalness; rejected.','C1':'Private derivative reference transfer has more varied human-like3Dflow, still rough/contact-failing and not an adopted owned asset.','renderingDiagnostic':'Same paired Cycles/Huang used only to falsify material-only explanation. No shader/renderer or performance promotion.'},
      'function':{'A_B':'Complete new native guide paths and patch-local lineage built, roots/radii/count/material/body layers preserved; saved .blend studies exist. Not appearance acceptance.',
        'C1':'Own source-to-target actual-skin ray-anchor RBF and exact actual-body root rebind; max saved root reconstruction error'+str(private['C1']['maximumSavedRootBindingReconstructionErrorM'])+'m. No injectivity/deforming-rig inference.'},
      'contact':{'A':{k:ownA['representativeBody'][k] for k in ('curves','segments','status','unqualifiedSegments','minimumCertifiedClearanceLowerBoundM')},
        'B':{k:ownB['representativeBody'][k] for k in ('curves','segments','status','unqualifiedSegments','minimumCertifiedClearanceLowerBoundM')},
        'C0UnqualifiedRepresentativeSegments':463,'C1UnqualifiedRepresentativeSegments':199,'representativeCurves':256,'C2':'Rejected over12mm displacement budget; no correction applied,199remain.',
        'limits':'All counts refer to complete finite segments of representative curves, not all children. A failed curve can contain interior segments not separately counted by surface-crossing checks. No all-child/self/dynamic/contact-safe claim.'},
      'runtime':{'asset':None,'status':'NOT_PROMOTED','exporterLODPerformance':'NOT_QUALIFIED'},
      'privateStudy':private,'femaleAccepted':False,'maleStarted':False,'nextAction':next_action}
    save(E/'female-next-r0039.visual-audit.json',audit)
    refs={'officialHairStyles':'https://www.blender.org/download/demo-files/','author':'Daniel Bystedt','inFileNotice':'CC BY-SA license','sourceFileSha256':private['sourceFileSha256'],
      'rightsFinding':'Official card and in-file notice giveCC BY-SA without version. Website content defaults toCC BY4.0, which does not establish this separate SA asset version. No source-version inference or new public grant was made.',
      'publicArchiveBoundary':'Only ownA/Bgeometry, own scripts/reports and minimal research statistics. No private donor/retarget positions, anchors, full raw texts, images or derivative .blend redistributed.',
      'primaryMethodReference':'https://research.dreamworks.com/wp-content/uploads/2018/07/a36-somasundaram-Edited.pdf',
      'newPaidDependencies':[],'newSoftwareInstalled':False}
    save(E/'references-and-rights.json',refs)
    save(S/'aevrynd-female-next-r0039-authoring.json',{'revision':'female-next-r0039','status':decision,'ownedStudies':[{'source':d['output'],'sha256':d['outputSha256'],'scope':'VISUALLY_REJECTED_STATIC_GUIDE_STUDY'} for d in (ownA,ownB)],
      'retainedWorkingSource':str(working),'privateReferenceStudy':{'path':str(private_source),'sha256':sha(private_source),'sourceAuthor':'Daniel Bystedt','status':'PRIVATE_NOT_ADOPTED_CONTACT_AND_LICENSE_UNQUALIFIED'},'nextAction':next_action})
    formal={k:manifest.get(k) for k in ('workingReviewRevision','workingReviewSource','workingReviewSha256','workingReviewStatus','currentSourceRevision','currentSource','strictOverallScore','strictScoreAppliesTo','runtimeAsset','runtimeStatus','enginePromotionApproved','websitePromotionApproved')}
    manifest.update({'latestStudyRevision':'female-next-r0039-c1-private','latestStudyStatus':decision,'latestStudyEvidence':str(E/'female-next-r0039.visual-audit.json'),'latestContinuation':str(E/'continuation.json'),'nextRequiredWork':next_action,
      'characterAuthoringDescriptorR39':'source/aevrynd-female-next-r0039-authoring.json','privateReferenceHairStudyR39':{'source':str(private_source),'sha256':sha(private_source),'author':'Daniel Bystedt original groom; Aevrynd retarget only','status':'PRIVATE_NOT_ADOPTED','scope':'Local11223fibre private derivative study; no public geometry/runtime promotion.'},
      'rejectedOwnedHairStudiesR39':[{'source':d['output'],'sha256':d['outputSha256'],'decision':'VISUALLY_REJECTED'} for d in (ownA,ownB)]})
    assert {k:manifest.get(k) for k in formal}==formal;save(manifest_path,manifest)
    save(E/'continuation.json',{'stage':'B_COMPLETE_HEAD_IN_PROGRESS','lastGoalTurnClassification':'progress',
      'classificationReason':'Actual two owned complete-head candidates falsified, a private artist-reference transfer visibly changes flow and identifies body-contact defects, own surface transfer reduces representative failures463to199. Owned working character unchanged; no accepted appearance/physics/runtime score increase.',
      'previousGoalTurnClassification':'progress: verified rest-exact r38B live authoring, pushed e342b35',
      'workingReviewSource':str(working),'workingReviewSha256':sha(working),'workingReviewStatus':manifest['workingReviewStatus'],
      'immediateFallback':str(S/'aevrynd-female-next-r0037-c-anatomical-eye-review.blend'),'immediateFallbackSha256':'4d14d272a7ad71b4b5f0fff1d60e793001e7e1620e69636feac8c6c5837db0b9',
      'privateStudy':{'source':str(private_source),'sha256':sha(private_source),'status':'UNADOPTED_CONTACT_AND_LICENSE_UNQUALIFIED','sourceAuthor':'Daniel Bystedt'},
      'latestEvidence':str(E/'female-next-r0039.visual-audit.json'),'liveJobHandles':[],'nextAction':next_action,
      'doNotRepeat':['Smooth global free-control grids with near-monotone fall','Angular scalp-patch contraction/offset patterns that render as bands','Old fixed exit/loft/funnel/ring/sheet and whole-head velocity-field routes','Increasing repair budget, density/radius or collision tolerance to hide failures','Treating reference-groom data as owned/promoted or distributing private data before terms resolved','Counting root reconstruction/representatives/static diagnostics as all-child/self/dynamics/runtime acceptance'],
      'remainingGates':['Complete believable face/hair, eye/oral/body/clothes rig and all motions','All applicable actual geometry and continuous contact/self gates','Natural hair motion, engine/export/LOD/real hardware performance','Weighted85each80 final gates and explicit female acceptance before male'],
      'resources':read(E/'resource-checkpoint.json'),'overallCharacterScore':None,'history':'Exact-file owned archive and push verification follow; private derivative data intentionally not public.'})
    entries=[]
    def archive(src,dst):
        dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);assert sha(src)==sha(dst)
        entries.append({'source':str(src),'archive':str(dst),'sha256':sha(dst),'bytes':dst.stat().st_size})
    for name in ('aevrynd-female-next-r0039-a-complete-guide-paths.blend','aevrynd-female-next-r0039-b-patch-local-locks.blend','aevrynd-female-next-r0039-a-complete-guide-controls.npz','aevrynd-female-next-r0039-b-patch-local-controls.npz','aevrynd-female-next-r0039-authoring.json'):archive(S/name,M/name)
    for p in sorted((R/'scripts/character-next').glob('*r0039*.py')):archive(p,REPO/'scripts/character-next'/p.name)
    excluded={'official-hair-license-anchor.json','official-license-contexts.json','history-file-manifest.json','git-paths.json'}
    for p in sorted(E.iterdir()):
        if p.is_file() and p.suffix in ('.json','.png') and p.name not in excluded:
            archive(p,M/(p.name if p.name.startswith('r0039-') else 'r0039-'+p.name))
    # Logs contain no raw geometry; omit private/proposal outputs with world
    # coordinate examples, preserving only reproducible own public jobs.
    for name in ('build','patches','scattering','review'):
        p=R/f'Evidence/character-female-next-r0039-{name}.log';archive(p,M/f'r0039-{name}.log')
    archive(manifest_path,M/'female-next.asset.json')
    save(E/'history-file-manifest.json',{'files':entries,'scope':decision,'excluded':'Entire private directory, artist/retarget images and .blend/.npz/coordinate reports, raw HTML licensing contexts and private solver stdout. Public summary preserves stats/hashes/author/source and all own code; no public derivative asset promotion.'})
    archive(E/'history-file-manifest.json',M/'r0039-history-file-manifest.json')
    paths=sorted({str(Path(row['archive']).relative_to(REPO)).replace('\\','/') for row in entries});save(E/'git-paths.json',paths)
    print(json.dumps({'files':len(paths),'bytes':sum(row['bytes'] for row in entries),'workingUnchanged':str(working),'privateResearchOnly':str(private_source),'decision':decision},indent=2))
if __name__=='__main__':main()
