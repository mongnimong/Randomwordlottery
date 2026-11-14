import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src).read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)


rep("const LAYER_NAME={mouth:'입',hand:'손',body:'몸통',leg:'발'};", "const LAYER_NAME={mouth:'입',hand:'손',body:'몸통',leg:'발',stk:'새 파츠'};")
rep("const LABEL={tex:'재료',body:'몸통',handL:'손',handR:'손',legL:'발',legR:'발',mouth:'입'};", "const LABEL={tex:'재료',body:'몸통',handL:'손',handR:'손',legL:'발',legR:'발',mouth:'입',stk:'새 파츠'};")
rep("const LAYER_SEL={mouth:'mouth',hand:'handL',leg:'legL',body:'body'};", "const LAYER_SEL={mouth:'mouth',hand:'handL',leg:'legL',body:'body',stk:'stk'};")
rep("const LAYER_COLOR=g=>g==='mouth'?", "const LAYER_COLOR=g=>g==='stk'?(st.stkColor||'#bbbbbb'):g==='mouth'?")
rep("function baseScale(key){", "function baseScale(key){if(key==='stk')return st.stk?st.stk.base:1;")
rep("function bbox(key){const o=st[key];", "function bbox(key){const o=st[key];if(key==='stk')return stkCv?{w:stkCv.width,h:stkCv.height}:null;")
rep("    else if(g==='mouth')drawMouth(c,k);}",
    "    else if(g==='mouth')drawMouth(c,k);\n    else if(g==='stk'&&stkCv&&st.stk){const im=stkImage();c.save();xf(c,st.stk,k);c.drawImage(im,-im.width/2,-im.height/2);c.restore();}}")
rep("  for(const g of [...st.order].reverse()){if(st.locked[g])continue;\n",
    "  for(const g of [...st.order].reverse()){if(st.locked[g])continue;\n"
    "    if(g==='stk'&&stkCv&&st.stk){const o=st.stk,m=new DOMMatrix().translate(o.x,o.y).rotate(o.rot*180/Math.PI).scale(o.scale).inverse(),q=m.transformPoint(new DOMPoint(pt.x,pt.y)),"
    "ix=Math.round(q.x+stkCv.width/2),iy=Math.round(q.y+stkCv.height/2);if(ix>=0&&iy>=0&&ix<stkCv.width&&iy<stkCv.height&&stkA[iy*stkCv.width+ix]>40)return'stk';}\n")

# UI: 마무리 탭 맨 위에 실험 상자
rep('''    <div class="pane" data-pane="out" hidden>
      <h2>마무리</h2>''', '''    <div class="pane" data-pane="out" hidden>
      <h2>🧪 새 파츠 만들기 (실험)</h2>
      <div class="patopt">
        <p class="hint" style="margin:0">흰 종이에 그린 파츠 그림(사진·스캔)을 올리면, 흰 바탕을 자동으로 지우고 캔버스에 붙여요. 끌어서 옮기고, 두 손가락이나 슬라이더로 크기·회전을 바꿔요.</p>
        <div class="row"><label class="btn primary small">그림 올리기<input class="vh" id="stkIn" type="file" accept="image/*"></label><button class="btn small" id="stkDel">지우기</button><button class="btn small" id="stkOrig">원래 색</button></div>
        <div class="label" style="margin-top:4px">살색(채운 부분) 색 바꾸기</div><div class="row" id="stkSw"></div>
      </div>
      <h2>마무리</h2>''')

rep("let bgImg=null;", r"""let bgImg=null;
/* ---------- 실험: 그림 → 새 파츠 ---------- */
let stkCv=null,stkA=null,stkFill=null,stkLum=null,stkCache={};
function stkImage(){const c=st.stkColor;if(!c)return stkCv;if(stkCache[c])return stkCache[c];
  const w=stkCv.width,h=stkCv.height,out=mk(w,h,g=>g.drawImage(stkCv,0,0)),g=out.getContext('2d'),d=g.getImageData(0,0,w,h),n=parseInt(c.slice(1),16),R=n>>16&255,G=n>>8&255,B=n&255;
  let sum=0,cnt=0;for(let i=0;i<w*h;i++)if(stkFill[i]){sum+=stkLum[i];cnt++;}const avg=cnt?sum/cnt:200;
  for(let i=0;i<w*h;i++)if(stkFill[i]){const t=Math.min(1.25,stkLum[i]/avg);d.data[i*4]=Math.min(255,R*t);d.data[i*4+1]=Math.min(255,G*t);d.data[i*4+2]=Math.min(255,B*t);}
  g.putImageData(d,0,0);return stkCache[c]=out;}
async function loadStk(f){if(!f)return;try{const url=URL.createObjectURL(f);const im=new Image();im.src=url;await im.decode();URL.revokeObjectURL(url);
  const sc=Math.min(1,900/Math.max(im.naturalWidth,im.naturalHeight)),W=Math.round(im.naturalWidth*sc),H=Math.round(im.naturalHeight*sc);
  const c0=mk(W,H,g=>g.drawImage(im,0,0,W,H)),d=c0.getContext('2d').getImageData(0,0,W,H).data;
  // 1) 바깥 테두리에서 시작해 '하얀 바탕'만 지운다(그림 안쪽 흰색, 예: 이빨은 남김)
  const lum=new Float32Array(W*H),white=new Uint8Array(W*H),bg=new Uint8Array(W*H);
  for(let i=0;i<W*H;i++){const r=d[i*4],g2=d[i*4+1],b=d[i*4+2],mx=Math.max(r,g2,b),mn=Math.min(r,g2,b);lum[i]=.3*r+.59*g2+.11*b;white[i]=(lum[i]>205&&mx-mn<28)?1:0;}
  const q=[];for(let x=0;x<W;x++){q.push(x,(H-1)*W+x);}for(let y=0;y<H;y++){q.push(y*W,y*W+W-1);}
  while(q.length){const i=q.pop();if(bg[i]||!white[i])continue;bg[i]=1;const x=i%W,y=(i/W)|0;if(x>0)q.push(i-1);if(x<W-1)q.push(i+1);if(y>0)q.push(i-W);if(y<H-1)q.push(i+W);}
  // 2) 남은 부분을 잘라 담고, 먹선/채운 부분 구분(채운 부분만 색 바꾸기)
  let x0=W,y0=H,x1=0,y1=0;for(let i=0;i<W*H;i++)if(!bg[i]){const x=i%W,y=(i/W)|0;if(x<x0)x0=x;if(x>x1)x1=x;if(y<y0)y0=y;if(y>y1)y1=y;}
  if(x1<=x0){toast('그림을 찾지 못했어요. 흰 바탕에 그린 그림인지 확인해 주세요.');return;}
  const pad=4,cw=x1-x0+1+pad*2,ch=y1-y0+1+pad*2,out=mk(cw,ch,()=>{}),og=out.getContext('2d'),od=og.createImageData(cw,ch);
  stkA=new Uint8Array(cw*ch);stkFill=new Uint8Array(cw*ch);stkLum=new Float32Array(cw*ch);
  for(let y=y0;y<=y1;y++)for(let x=x0;x<=x1;x++){const i=y*W+x,j=(y-y0+pad)*cw+(x-x0+pad);if(bg[i])continue;
    // 바탕과 닿은 가장자리는 살짝 투명하게(계단 줄이기)
    const edge=(x>0&&bg[i-1])||(x<W-1&&bg[i+1])||(y>0&&bg[i-W])||(y<H-1&&bg[i+W]);const a=edge?Math.max(60,Math.min(255,(255-lum[i])*3)):255;
    od.data[j*4]=d[i*4];od.data[j*4+1]=d[i*4+1];od.data[j*4+2]=d[i*4+2];od.data[j*4+3]=a;stkA[j]=a;stkLum[j]=lum[i];stkFill[j]=(lum[i]>95&&!white[i])?1:0;}
  og.putImageData(od,0,0);stkCv=out;stkCache={};
  const base=K*Math.min(1,260/Math.max(cw,ch));st.stk={x:500,y:470,scale:base,rot:0,base};st.stkColor=null;
  if(!st.order.includes('stk'))st.order.push('stk');renderStkSw();select('stk');renderLayers();toast('새 파츠를 붙였어요. 끌어서 옮겨 보세요');}
  catch(e){toast('이 그림은 열 수 없어요. JPG나 PNG로 골라 주세요.');}}
function renderStkSw(){swatchRow('#stkSw',TONES,()=>st.stkColor||'',c=>{st.stkColor=c;});}
$('#stkOrig').onclick=()=>{st.stkColor=null;renderStkSw();draw();};
$('#stkIn').onchange=e=>{loadStk(e.target.files[0]);e.target.value='';};
$('#stkDel').onclick=()=>{stkCv=null;st.stk=null;st.order=st.order.filter(g=>g!=='stk');if(st.sel==='stk')st.sel='handL';renderLayers();draw();};""")
open(dst, 'w').write(s)
print('ok')
