"""Present actual source renders and native sampled action, no motion synthesis."""
from pathlib import Path
import json,importlib.util
from PIL import Image,ImageDraw
sp=importlib.util.spec_from_file_location('r139review',Path(__file__).with_name('review-female-next-r0139-views.py'));s=importlib.util.module_from_spec(sp);sp.loader.exec_module(s);E=s.E
def main():
 s.sheet('r0139-original-failure-pose-comparison.png',[[('r138 B / original diagonal failure',E/'matched-baseline-diagonal-yaw-20-pitch+10-face.png'),('r139 / actual native lid following',E/'actual-lid-diagonal-yaw-20-pitch+10-face.png')],[('r138 B / up under second light',E/'second-light-baseline-up-face.png'),('r139 / same up / same second light',E/'second-light-a-up-face.png')]],'Actual complete head under identical angles/light/exposure; no overall static realism score or global contact claim.')
 s.sheet('r0139-oblique-and-body-operation.png',[[('r138 B / up oblique',E/'baseline-lid-up-oblique.png'),('r139 / same up oblique',E/'actual-lid-up-oblique.png')],[('r139 complete body / up gaze',E/'actual-lid-gaze-body-frame-037.png'),('r139 complete body / return neutral',E/'actual-lid-gaze-body-frame-049.png')]],'Actual whole-woman context; native skin/lash/wet-line operation, other layers/body held fixed.')
 rows=json.loads((E/'actual-lid-gaze-motion-controls.json').read_text('utf-8'));frames=[]
 for r in rows:
  im=Image.new('RGB',(640,688),'#191919');im.paste(Image.open(r['file']).convert('RGB'),(0,48));ImageDraw.Draw(im).text((12,12),'r139 native eye/lid follow / actual frame %d'%r['frame'],font=s.FONT,fill='white');frames.append(im)
 frames[0].save(E/'r0139-actual-native-gaze.gif',save_all=True,append_images=frames[1:],duration=167,loop=0)
 (E/'motion-presentation-scope.json').write_text(json.dumps({'actualNativeActionFrames':[r['frame'] for r in rows],'sourceFPS':24,'renderEvery4SourceFrames':True,'presentationGIFDelayMS':167,'noImageWarpingOrSynthesizedIntermediateFrames':True,'GIFIsSampledSourceMotionNotContinuousContactProof':True},indent=2)+'\n',encoding='utf-8');print('R139_ACTUAL_NATIVE_GAZE_PRESENTATION_READY')
if __name__=='__main__':main()
