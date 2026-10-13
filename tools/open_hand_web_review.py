"""Package the WebGL viewer and both GLBs without sibling-file or CDN dependencies."""
from pathlib import Path
import base64,json,subprocess
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'renders/open-hand';ASSET=ROOT/'assets/optimized/open-hand'
subprocess.run([str(ROOT/'node_modules/.bin/esbuild'),str(ROOT/'tools/open-hand-preview.ts'),'--bundle','--format=iife','--minify','--outfile=/tmp/open-hand-viewer.js'],check=True,cwd=ROOT)
models=[base64.b64encode((ASSET/f'kote-lod{i}.glb').read_bytes()).decode() for i in (0,1)]
script=Path('/tmp/open-hand-viewer.js').read_text().replace('</script','<\\/script')
page='''<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>赤備籠手・遊戲模型</title><style>*{box-sizing:border-box}body{margin:0;background:#131719;color:#e8e3d7;font:15px/1.6 system-ui}header,footer{max-width:1050px;margin:auto;padding:16px 20px}h1{font-size:24px;margin:0}p{margin:6px 0;color:#bfc2bf}canvas{display:block;width:100%;height:65vh;min-height:300px;touch-action:none}button{background:#71282d;color:#fff;border:1px solid #ae685b;padding:9px 13px;margin:5px 5px 5px 0;border-radius:4px;cursor:pointer}#status{font-variant-numeric:tabular-nums}small{color:#c0b3a1}</style><header><h1>赤備籠手・遊戲模型</h1><p>拖曳旋轉 · 滾輪／雙指縮放 · 手機預設 LOD 1</p><button data-lod="0">近景 LOD 0</button><button data-lod="1">遠景 LOD 1</button><button id="palm">查看另一面</button><button id="rotate">自動旋轉</button><p id="status">啟動 WebGL…</p></header><canvas aria-label="可旋轉的籠手 3D 模型"></canvas><footer><p>MPFB / MakeHuman CC0 人體基底 · Blender 烘焙 · Babylon.js 即時 PBR</p><small>固定握槍姿勢，保留骨架；尚無開合手動畫。這是素材檢視，尚未替換線上遊戲角色。模型、貼圖與程式均已內嵌，下載本頁後可用支援 WebGL 的瀏覽器開啟；若文件預覽器禁用腳本，請改用瀏覽器。</small></footer><script>window.embeddedHands='''+json.dumps(models)+''';</script><script>'''+script+'''</script></html>'''
preview=OUT/'game-canvas-lod0.png'
if preview.exists():
    uri='data:image/png;base64,'+base64.b64encode(preview.read_bytes()).decode()
    page=page.replace('<canvas aria-label="可旋轉的籠手 3D 模型"></canvas>', '<div style="position:relative"><img id="fallback" src="'+uri+'" alt="遊戲模型實際畫面；互動檢視需瀏覽器支援 JavaScript 與 WebGL" style="position:absolute;inset:0;width:100%;height:100%;object-fit:contain;background:#101415"><canvas aria-label="可旋轉的籠手 3D 模型"></canvas></div>')
(OUT/'game-model.html').write_text(page)
print(json.dumps({'viewer_bytes':len(page.encode()),'models':[len(x) for x in models]}))
