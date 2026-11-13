// 털천 원단 무늬 후보 (800x800, 이음새 없이 반복되도록 가장자리 넘는 모양은 반대편에도 그림)
function wrapDraw(w,h,fn){for(const dx of [-w,0,w])for(const dy of [-h,0,h])fn(dx,dy);}
function blobPts(r,x,y,s,k,j){const o=[];for(let i=0;i<k;i++){const a=i/k*Math.PI*2,rr=s*(1-j/2+r()*j);o.push([x+rr*Math.cos(a),y+rr*Math.sin(a)]);}return chaikin(o,3);}
function fillPts(g,v){g.beginPath();v.forEach((p,i)=>i?g.lineTo(p[0],p[1]):g.moveTo(p[0],p[1]));g.closePath();g.fill();}
const PATTERNS_NEW=[
 ['호피',mk(800,800,(g,w,h)=>{g.fillStyle='#EDBE73';g.fillRect(0,0,w,h);const r=rng(11);
   for(let gy=0;gy<8;gy++)for(let gx=0;gx<8;gx++){const x=gx*100+(gy%2)*50+r()*30-15,y=gy*100+r()*30-15,s=26+r()*12;
     const cen=blobPts(r,0,0,s*.8,7,.5),segs=3+Math.floor(r()*2),a0=r()*6;
     wrapDraw(w,h,(dx,dy)=>{g.save();g.translate(x+dx,y+dy);g.fillStyle='#B97A34';fillPts(g,cen);
       g.strokeStyle='#2E2622';g.lineCap='round';for(let k=0;k<segs;k++){const a=a0+k*(Math.PI*2/segs);g.lineWidth=9+r()*5;g.beginPath();g.arc(0,0,s,a,a+Math.PI*2/segs*.62);g.stroke();}g.restore();});}})],
 ['젖소',mk(800,800,(g,w,h)=>{g.fillStyle='#FBFAF6';g.fillRect(0,0,w,h);const r=rng(5);g.fillStyle='#2E2A30';
   const C=[[120,140,110],[520,90,80],[380,420,130],[700,360,70],[160,560,85],[620,660,105],[260,780,55],[60,330,45]];
   for(const [x,y,s] of C){const v=blobPts(r,0,0,s,9,.7);wrapDraw(w,h,(dx,dy)=>fillPts(g,v.map(p=>[p[0]+x+dx,p[1]+y+dy])));}})],
 ['체커보드',mk(800,800,(g,w,h)=>{g.fillStyle='#FFE1EB';g.fillRect(0,0,w,h);g.fillStyle='#F35C8A';for(let y=0;y<8;y++)for(let x=0;x<8;x++)if((x+y)%2)g.fillRect(x*100,y*100,100,100);})],
 ['하트',mk(800,800,(g,w,h)=>{g.fillStyle='#FFD3E1';g.fillRect(0,0,w,h);const hp=new Path2D();for(let i=0;i<=60;i++){const t=i/60*Math.PI*2,x=16*Math.pow(Math.sin(t),3),y=-(13*Math.cos(t)-5*Math.cos(2*t)-2*Math.cos(3*t)-Math.cos(4*t));i?hp.lineTo(x,y):hp.moveTo(x,y);}
   for(let gy=0;gy<5;gy++)for(let gx=0;gx<5;gx++){const x=gx*160+(gy%2)*80,y=gy*160+40;wrapDraw(w,h,(dx,dy)=>{g.save();g.translate(x+dx,y+dy);g.rotate((gx+gy)%2?.25:-.25);g.scale(2.4,2.4);g.fillStyle=(gx+gy)%3?'#F35C8A':'#E0283A';g.fill(hp);g.restore();});}})],
 ['지브라',mk(800,800,(g,w,h)=>{g.fillStyle='#FBFAF6';g.fillRect(0,0,w,h);g.fillStyle='#2E2A30';const r=rng(3);
   for(let i=0;i<10;i++){const x0=i*80+r()*20,amp=18+r()*14,ph=r()*6,w0=22+r()*14,v=[];
     for(let y=0;y<=800;y+=10)v.push([x0+amp*Math.sin(y/800*Math.PI*4+ph)+w0*(.6+.4*Math.sin(y/800*Math.PI*2+i)),y]);
     for(let y=800;y>=0;y-=10)v.push([x0+amp*Math.sin(y/800*Math.PI*4+ph)-w0*(.6+.4*Math.sin(y/800*Math.PI*2+i)),y]);
     wrapDraw(w,0.0001,(dx)=>fillPts(g,v.map(p=>[p[0]+dx,p[1]])));}})],
 ['타탄',mk(800,800,(g,w,h)=>{g.fillStyle='#C8323C';g.fillRect(0,0,w,h);
   const B=[[0,70,'rgba(31,42,92,.55)'],[100,24,'rgba(31,42,92,.55)'],[150,10,'rgba(244,216,74,.8)'],[160,40,'rgba(30,90,60,.5)']];
   for(let o=0;o<800;o+=200)for(const [p,s,c] of B){g.fillStyle=c;g.fillRect(o+p,0,s,h);g.fillRect(0,o+p,w,s);}
   g.strokeStyle='rgba(255,255,255,.35)';g.lineWidth=3;for(let o=0;o<800;o+=200){g.beginPath();g.moveTo(o+185,0);g.lineTo(o+185,h);g.moveTo(0,o+185);g.lineTo(w,o+185);g.stroke();}})],
];
