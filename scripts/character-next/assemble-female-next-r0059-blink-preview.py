"""Rebuild the looping preview strictly from actual rendered source frames."""
from pathlib import Path
from PIL import Image
import json,hashlib
E=Path(r'D:\Download\Aevrynd\Evidence\character-female-next\r0059-authored-blink')
def main():
    a=json.loads((E/'a-blink-clip-renders.json').read_text());frames=[Image.open(x['path']).convert('RGB') for x in a['frames']];assert len(frames)==48 and all(x.size==(480,480) for x in frames)
    palette=frames[0].quantize(colors=256,method=Image.Quantize.MEDIANCUT);out=[x.quantize(palette=palette,dither=Image.Dither.FLOYDSTEINBERG) for x in frames];durations=[(round((i+1)*100/24)-round(i*100/24))*10 for i in range(48)];assert sum(durations)==2000
    p=E/'a-actual-blink.gif';out[0].save(p,save_all=True,append_images=out[1:],duration=durations,loop=0,optimize=False,disposal=2)
    with Image.open(p) as gif:
        total=0
        for i in range(gif.n_frames):gif.seek(i);total+=gif.info.get('duration',0)
        assert total==2000
    (E/'a-blink-preview.json').write_text(json.dumps({'file':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'sourceFrames':48,'actualRenderedFrames':True,'durationMS':total,'loop':True,'warning':'GIF256-colour preview; source PNG frames and Blender geometry are the evidence. No continuous contact or engine performance inference.'},indent=2)+'\n',encoding='utf8')
    print('R59_ACTUAL_GIF',p.stat().st_size,total,flush=True)
if __name__=='__main__':main()
