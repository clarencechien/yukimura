"""Preserve the original lower body; restrict restored pixels to the vacated leg region."""
from pathlib import Path
import hashlib,json,math
from PIL import Image,ImageDraw
import numpy as np
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/routes/jigoku-2d/free-arm-settle';OUT.mkdir(exist_ok=True)
old=json.loads((ROOT/'docs/routes/jigoku-2d/free-arm-transition/transition.json').read_text());touch=old['frames'][3];reg=touch['registration'];box=reg['box'];scale=reg['scale'];offset=reg['offset']
source=ROOT/old['source'];raw=Image.open(source).convert('RGBA').crop(box);small=raw.resize((round(raw.width*scale),round(raw.height*scale)),Image.Resampling.LANCZOS);frame=Image.new('RGBA',(1152,768));frame.alpha_composite(small,offset)
project=lambda p:[offset[i]+p[i]*scale for i in range(2)]
restoredSource=ROOT/'assets/source/jigoku-2d/ghost-rig/touch-shin-clean.png';restored=Image.open(restoredSource).convert('RGBA');restoreScale=raw.width*scale/restored.width;clean=Image.new('RGBA',frame.size);clean.alpha_composite(restored.resize((round(restored.width*restoreScale),round(restored.height*restoreScale)),Image.Resampling.LANCZOS),offset)
# Curved belt boundary; lower body is foreground so the original torso can hinge behind it.
cut=[[0,423],[185,423],[235,466],[300,485],[410,472],[470,463],[530,456],[672,456]]
upper=[[0,0],[672,0]]+[[x,y+16] for x,y in reversed(cut)];lower=cut+[[672,724],[0,724]]
polys={'torso':upper,'lower':lower,'cap':[[x-1500,y] for x,y in [[1770,280],[1835,257],[1885,290],[1900,399],[1790,421]]],
 'shin':[[110,538],[155,519],[194,527],[223,557],[243,606],[207,634],[155,605],[112,568]],
 'waist':[[235,467],[300,485],[410,472],[470,463],[530,480],[550,603],[325,625],[235,545]],
 'shoe':[[161,606],[202,593],[241,606],[264,640],[262,660],[214,679],[110,680],[94,664],[105,643],[141,626]]}
vacated=[[105,546],[176,534],[206,548],[237,583],[247,615],[266,643],[269,669],[229,686],[88,689],[84,648],[128,617],[123,583]]
kneeKeep=[[55,463],[85,440],[140,432],[190,456],[210,497],[197,535],[158,551],[100,566],[60,544]]
def raster(poly):
 mask=Image.new('L',frame.size);ImageDraw.Draw(mask).polygon([tuple(project(v)) for v in poly],fill=255);return np.array(mask)
removed=np.minimum(raster(vacated),255-raster(kneeKeep))
polys['restore']=vacated
parts={}
for name,poly in polys.items():
 points=[project(p) for p in poly];im=clean if name=='restore' else frame;mask=Image.new('L',im.size);ImageDraw.Draw(mask).polygon([tuple(p) for p in points],fill=255);a=np.array(im);a[:,:,3]=np.minimum(a[:,:,3],np.array(mask));
 if name in ['lower','waist']:a[:,:,3]=np.minimum(a[:,:,3],255-removed)
 if name=='restore':a[:,:,3]=np.minimum(a[:,:,3],removed)
 piece=Image.fromarray(a);cropbox=piece.getbbox();piece=piece.crop(cropbox);piece.save(OUT/f'{name}.webp',lossless=True,method=6);parts[name]={'url':name+'.webp','box':cropbox,'polygon':points,'source':'restored' if name=='restore' else 'original','legMaskRule':'subtract' if name in ['lower','waist'] else 'inside' if name=='restore' else 'none'}
knee=project([150,527]);ankle=project([211,612]);toe=project([114,666])
for name,pivot,end in [('shin',knee,ankle),('shoe',ankle,toe)]:
 b=parts[name]['box'];parts[name].update(pivot=[pivot[0]-b[0],pivot[1]-b[1]],end=[end[0]-b[0],end[1]-b[1]])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
meta={'baselineCommit':'7b2848b5b8471383a34a30b5a8cb57912d2f269b','vacatedLegPolygon':[project(v) for v in vacated],'preservedKneePolygon':[project(v) for v in kneeKeep],'source':{'path':str(source.relative_to(ROOT)),'sha256':sha(source),'box':box,'scale':scale,'offset':offset},'restored':{'path':str(restoredSource.relative_to(ROOT)),'sha256':sha(restoredSource),'scale':restoreScale,'offset':offset,'generatedFile':'exec-6683c82d-6114-4d5b-bb98-f4e354602e91.png'},'parts':parts,'shoulder':touch['shoulder'],'hipPivot':[610,520],'knee':knee,'ankle':ankle,'toe':toe,'shinLength':math.dist(knee,ankle),'footLength':math.dist(ankle,toe),'foldStart':420,'foldEnd':500,'shinRotation':-45,'shoeRotation':-70,'method':'Original touch torso/cap/lower/waist/shin/shoe pixels; existing generated restoration restricted to the vacated shin/shoe region, preserving the original knee. Shared parts from the touch frame onward; translation before 400 ms joins the hip hinge at 400 ms. Fixed knee, shin and shoe rotate only after palm contact. Lower-body alpha occludes the tucking foot; no fading. Late segment changes final body silhouette and is not a biomechanical simulation.','runtimeChanged':False}
(OUT/'settle.json').write_text(json.dumps(meta,indent=2)+'\n');print({'knee':knee,'ankle':ankle,'shin':meta['shinLength'],'foot':meta['footLength'],'restoredScale':restoreScale})
