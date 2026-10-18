"""Display-image footprint diagnostics, explicitly not physical density metrics."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0018-brow-readability'
def main():
    baseline=np.array(Image.open(E/'baseline-face.png').convert('RGB'),dtype=np.float64)/255
    constant=np.array(Image.open(E/'constant-diffuse-face.png').convert('RGB'),dtype=np.float64)/255
    emission=np.array(Image.open(E/'emission-mask-face.png').convert('RGB'),dtype=np.float64)/255
    candidatePath=E/'candidate-c-face.png'
    candidate=np.array(Image.open(candidatePath).convert('RGB'),dtype=np.float64)/255 if candidatePath.exists() else None
    metadata=json.loads((E/'baseline-diagnostic.json').read_text());bounds=next(x for x in metadata['renders'] if x['view']=='face')['projectedBrowBounds'];rows=[]
    def luma(srgb):
        rgb=np.where(srgb<=.04045,srgb/12.92,((srgb+.055)/1.055)**2.4);return rgb@np.array((.2126,.7152,.0722))
    for row in bounds:
        x0,y0,x1,y1=row['pixelBounds'];x0=max(0,int(np.floor(x0))-5);y0=max(0,int(np.floor(y0))-5);x1=min(1100,int(np.ceil(x1))+5);y1=min(1100,int(np.ceil(y1))+5)
        a=baseline[y0:y1,x0:x1];b=constant[y0:y1,x0:x1];m=emission[y0:y1,x0:x1];changed=np.max(np.abs(m-a),axis=2)>8/255
        value={'object':row['object'],'pixelROI':[x0,y0,x1,y1],'roiPixels':int(changed.size),'emissionDetectablyChangedPixels':int(changed.sum()),'emissionThresholdedFootprintFraction':float(changed.mean()),'meanAbsRGBChangeConstantMaterial':float(np.mean(np.abs(a-b))),'baselineMeanLinearizedDisplayLuma':float(luma(a).mean()),'constantMeanLinearizedDisplayLuma':float(luma(b).mean())}
        if candidate is not None:
            c=candidate[y0:y1,x0:x1];value['candidateCMeanLinearizedDisplayLuma']=float(luma(c).mean());value['candidateCRelativeLumaChange']=float(luma(c).mean()/luma(a).mean()-1)
        rows.append(value)
    (E/'brow-footprint-metrics.json').write_text(json.dumps({'status':'DISPLAY_ROI_MEASUREMENTS_ONLY','rows':rows,'threshold':8/255,'scope':'Fixed rectangular face-view ROIs from the original projected brow bounds, padded by 5 pixels. Fraction is thresholded change from a separately labelled red emission diagnostic, not physical fibre coverage/density or objective realism. RGB/luma values include anti-aliasing, shading and tone mapping; no albedo change is inferred.','diagnosis':'Original brown material vs constant diffuse produces little full-face change while fine-stroke footprint remains sparse; do not treat pigment-only darkening as the complete correction.'},indent=2)+'\n')
    print('R0018_DISPLAY_FOOTPRINT_DONE')
if __name__=='__main__':main()
