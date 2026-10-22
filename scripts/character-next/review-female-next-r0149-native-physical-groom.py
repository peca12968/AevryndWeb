"""Match existing full-woman renders and review the actual147/148/149 window."""
from pathlib import Path
import json,datetime,hashlib,shutil
from PIL import Image,ImageDraw,ImageFont
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0149-native-scalp-sculpt';B=E.parent/'r0139-native-lid-follow'
F=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
def read(p):return json.loads(Path(p).read_text('utf-8-sig'))
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def sheet(name,rows,footer):
 im=Image.new('RGB',(640*len(rows[0]),688*len(rows)+48),'#191919');d=ImageDraw.Draw(im)
 for y,row in enumerate(rows):
  for x,(label,p) in enumerate(row):
   src=Image.open(p).convert('RGB');assert src.size==(640,640);im.paste(src,(640*x,688*y+48));d.text((640*x+10,688*y+12),label,font=F,fill='white')
 d.text((10,688*len(rows)+12),footer,font=F,fill='white');im.save(E/name)
def main():
 before=read(E/'before.json');now=datetime.datetime.now(datetime.timezone.utc)
 save(E/'continuation-resource-checkpoint.json',{'observedUTC':now.isoformat(),'originalStartedUTC':before['startedUTC'],'originalCheckpointUTC':before['resourceCheckpointUTC'],'checkpointElapsed':now>=datetime.datetime.fromisoformat(before['resourceCheckpointUTC']),'phase':'Existing complete A/source and5 actual renders, original builder and minimum independent reopen logs terminal with Blender quit; visual rejection, due whole review and exact archive remain. No job restarted.','previousGoalTurnClassification':'Progress in prompt maintenance only: v48 execution prompt and entries committed/remote verified. No character production/adoption/counting occurred in maintenance.','originalBaseCommit':before['baseCommit'],'currentHeadIncludesSeparateMaintenanceCommit':'049d241a5abd609f9a6d478187b934b3eeacec04','originalClocksAndCostsNotReset':True,'remainingBound':'No new candidate, capability probe or broad contact/runtime audit. Finish existing visual decision, required147/148/149 review and minimum complete source/rights/history. Aim history verification by05:00UTC; original deadlines remain and overrun is recorded.','freeBytes':{d:shutil.disk_usage(d+':/').free for d in ['C','D']}})
 clean=lambda r:{k:v for k,v in r.items() if k not in ['file','capture']}
 old=read(B/'a-view-controls.json');new=read(E/'a-view-controls.json');assert [clean(r) for r in old]==[clean(r) for r in new]
 def row(v):return [('r139 working / '+v,B/('matched-a-native-lid-follow-'+v+'.png')),('r149 rejected radial groom / '+v,E/('matched-a-native-physical-groom-'+v+'.png'))]
 for name,views in [('r0149-complete-head-body-comparison.png',['face','body-face']),('r0149-profile-back-comparison.png',['profile','back']),('r0149-oblique-comparison.png',['oblique'])]:sheet(name,[row(v) for v in views],'Same camera/light/exposure. Visible radial hairstyle failure; no appearance acceptance.')
 cols=[('r147 native lid correction',E.parent/'r0147-outer-lid-surface','matched-a-native-tarsal-corrective-'),('r148 local surface tress',E.parent/'r0148-native-groom-foundation','matched-a-local-native-tress-'),('r149 native physical groom',E,'matched-a-native-physical-groom-')]
 for name,views in [('three-round-complete-head-body.png',['face','body-face']),('three-round-complete-profile-back.png',['profile','back'])]:sheet(name,[[(label+' / '+v,p/(prefix+v+'.png')) for label,p,prefix in cols] for v in views],'Three original rounds147/148/149; existing renders only. Failed attempts remain in their original round.')
 finish=max((E/('matched-a-native-physical-groom-'+v+'.png')).stat().st_mtime for v in ['face','body-face','profile','oblique','back'])
 save(E/'matched-view-verification.json',{'allFiveActualViewControlsExactlyMatchWorkingR139':True,'onlyExcludedMetadata':['file','capture'],'baselineNotRerendered':True,'firstCompleteFiveViewUTC':datetime.datetime.fromtimestamp(finish,datetime.timezone.utc).isoformat(),'hairMassCroppingLimitation':'Head/profile/back camera crops the outward hair mass. Body view reveals the full-body failure but uppermost radial tips meet the top image border; entire-hair coverage is NOT accepted. Sufficient visible failure to reject without another render.','noNaturalMotionContactOrRuntimeAcceptance':True})
 print('R149_EXISTING_MATCHED_FULL_WOMAN_AND_147_148_149_REVIEW_BOARDS_READY')
if __name__=='__main__':main()
