import fs from 'node:fs/promises';import path from 'node:path';import {build} from 'esbuild';import {execFileSync} from 'node:child_process';import {FILES} from '../docs/routes/jigoku-2d/play/assets.mjs';
const root=process.cwd(),play=path.join(root,'docs/routes/jigoku-2d/play'),output=path.join(root,'.tmp/jigoku-release');await fs.mkdir(output,{recursive:true});
const assets={};for(const name of FILES){const data=await fs.readFile(path.join(play,'../combat',name));assets[name]=`data:${name.endsWith('.json')?'application/json':'image/webp'};base64,${data.toString('base64')}`;}
const result=await build({entryPoints:[path.join(play,'game.mjs')],bundle:true,format:'iife',minify:true,write:false,target:['es2022'],legalComments:'inline'});
const js=code=>code.replace(/<\/script/gi,'<\\/script');
let html=await fs.readFile(path.join(play,'index.html'),'utf8');html=html.replace('<link rel="stylesheet" href="style.css">',`<style>${await fs.readFile(path.join(play,'style.css'),'utf8')}</style>`);
html=html.replace('<script src="../combat/vendor/phaser-3.90.0.min.js"></script>',`<script>${js(await fs.readFile(path.join(play,'../combat/vendor/phaser-3.90.0.min.js'),'utf8'))}</script>`);
html=html.replace('<script type="module" src="game.mjs"></script>',`<script>window.SANADA_ASSETS=${JSON.stringify(assets)};${js(result.outputFiles[0].text)}</script>`);
await fs.writeFile(path.join(output,'index.html'),html);await fs.copyFile(path.join(play,'../combat/vendor/PHASER-LICENSE.md'),path.join(output,'PHASER-LICENSE.md'));
await fs.writeFile(path.join(output,'README.txt'),'真田・六文劫 — 燼關突圍\n\n解壓縮後，以 Chrome、Edge 或 Firefox 開啟 index.html。無需安裝或啟動伺服器。\nWASD／方向鍵移動、按住 J 連槍、空白鍵衝刺、K 無雙、R 集合／突進。\n手機以左搖桿與右側按鈕操作；手機系統可能限制下載 HTML 執行，這時請使用 HTTP 版本。\nPhaser 3.90 MIT 授權附於 PHASER-LICENSE.md。\n這是架空修羅戰境的 2D 關卡原型，沒有真實 3D 模型或真人動作捕捉。\n');
const zip=path.join(play,'sanada-jigoku.zip');execFileSync('python3',['-c','import sys,zipfile,pathlib\nwith zipfile.ZipFile(sys.argv[2],"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:\n for f in sorted(pathlib.Path(sys.argv[1]).iterdir()): z.write(f,f.name)',output,zip]);
console.log(JSON.stringify({standaloneBytes:Buffer.byteLength(html),zipBytes:(await fs.stat(zip)).size,embeddedAssets:FILES.length,html:path.relative(root,path.join(output,'index.html')),zip:path.relative(root,zip)}));
