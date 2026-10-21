"""Presentation of actual extra operation captures; no scene/image synthesis."""
from pathlib import Path
import json,importlib.util
from PIL import Image,ImageDraw,ImageFont
sp=importlib.util.spec_from_file_location('r138sheets',Path(__file__).with_name('review-female-next-r0138-views.py'));s=importlib.util.module_from_spec(sp);sp.loader.exec_module(s);E=s.E
def main():
 poses=[(1,'neutral'),(9,'yaw -20'),(25,'yaw +20'),(37,'pitch +10'),(45,'pitch -10'),(49,'return neutral')]
 s.sheet('r0138-b-actual-gaze-poses.png',[[('B / '+label,E/('b-gaze-face-frame-%03d.png'%f)) for f,label in poses[:3]],[('B / '+label,E/('b-gaze-face-frame-%03d.png'%f)) for f,label in poses[3:]]],'Actual sampled poses of the same full woman; finite/continuous all-avatar contact remains unaccepted.')
 frames=[]
 for f,label in poses:
  out=Image.new('RGB',(640,688),'#191919');out.paste(Image.open(E/('b-gaze-face-frame-%03d.png'%f)).convert('RGB'),(0,48));ImageDraw.Draw(out).text((12,12),'B / '+label+' / sampled pose, not continuous video',font=s.font,fill='white');frames.append(out)
 frames[0].save(E/'r0138-b-actual-gaze-poses.gif',save_all=True,append_images=frames[1:],duration=500,loop=0)
 # Independent diagnostic stage is 800x800. It is recorded separately and
 # must not be claimed pixel-matched to the 640x640 primary A/B images.
 extra=[[('B independent diagonal -20/+10',E/'b-diagonal-yaw-20-pitch+10-face.png'),('B independent diagonal +20/-10',E/'b-diagonal-yaw+20-pitch-10-face.png')],[('B independent whole-body gaze frame9',E/'b-gaze-body-frame-009.png'),('B independent whole-body return frame49',E/'b-gaze-body-frame-049.png')]]
 out=Image.new('RGB',(1600,1744),'#191919');d=ImageDraw.Draw(out)
 for y,row in enumerate(extra):
  for x,(label,p) in enumerate(row):
   im=Image.open(p).convert('RGB');assert im.size==(800,800);out.paste(im,(800*x,848*y+48));d.text((800*x+12,848*y+12),label,font=s.font,fill='white')
 d.text((12,1708),'Actual independent operation context; own recorded 800px stage, not primary 640px matched A/B.',font=s.font,fill='white');out.save(E/'r0138-b-independent-operation-context.png')
 light=json.loads((E/'matched-second-light-controls.json').read_text('utf-8'));assert light['controlsExactlyMatchExceptFilename'];s.sheet('r0138-b-second-light-comparison.png',[[('r126 retained baseline / second light',Path(light['baselineImage'])),('B neutral / same second light',E/'b-second-light-neutral-face.png'),('B yaw +20 / same second light',E/'b-second-light-yaw20-face.png')]],'Matched alternate illumination: protected face/skin preserved, no static realism gain claimed.')
 (E/'extra-operation-capture-scope.json').write_text(json.dumps({'primaryMatchedABResolution':[640,640],'primaryFiveViewsExactlyMatched':True,'independentExtraDiagnosticResolution':[800,800],'independentExtraStageRecordedIn':'b-actual-gaze-body-controls.json','notClaimedMatchedToPrimaryResolutionOrStage':True,'sixPoseGIF':'r0138-b-actual-gaze-poses.gif','GIFUsesActualRenderedSelectedFrames':[1,9,25,37,45,49],'GIFDurationEachMS':500,'GIFIsPosePresentationNot24FPSVideoOrContinuousContactEvidence':True},indent=2)+'\n',encoding='utf-8');print('R138_ACTUAL_OPERATION_SUPPLEMENT_SHEETS_DONE')
if __name__=='__main__':main()
