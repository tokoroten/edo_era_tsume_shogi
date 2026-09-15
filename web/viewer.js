window.OT_CONFIG = window.OT_CONFIG || {index:"index.json", dir:"problems/"};

const ZEN = "０１２３４５６７８９", KAN = "〇一二三四五六七八九";
const JP = {P:"歩",L:"香",N:"桂",S:"銀",G:"金",B:"角",R:"飛",K:"玉"};
const JPP = {P:"と",L:"杏",N:"圭",S:"全",B:"馬",R:"龍"};

let index=null, cur=null, ply=0, pos=null;

function parseSFEN(sfen){
  const [bpart, side, hpart] = sfen.split(" ");
  const sq = {};
  bpart.split("/").forEach((seg, ri)=>{
    const rank = ri+1; let f = 9, prom = false;
    for (const c of seg){
      if (c === "+"){ prom = true; continue; }
      if (/\d/.test(c)){ f -= +c; continue; }
      const color = (c === c.toUpperCase()) ? "b" : "w";
      sq[f+","+rank] = {c: color, k: c.toUpperCase(), p: prom};
      f--; prom = false;
    }
  });
  const hand = {b:{}, w:{}};
  if (hpart !== "-"){
    for (const m of hpart.matchAll(/(\d*)([RBGSNLPrbgsnlp])/g)){
      const color = (m[2] === m[2].toUpperCase()) ? "b" : "w";
      const k = m[2].toUpperCase();
      hand[color][k] = (hand[color][k]||0) + (m[1] ? +m[1] : 1);
    }
  }
  return {sq, hand, side};
}
function sqkey(f,r){ return f+","+r; }
function applyUSI(pos, usi){
  if (usi[1] === "*"){
    const k = usi[0], f = +usi[2], r = usi.charCodeAt(3)-96;
    pos.sq[sqkey(f,r)] = {c: pos.side, k, p:false};
    pos.hand[pos.side][k]--;
  } else {
    const f1=+usi[0], r1=usi.charCodeAt(1)-96, f2=+usi[2], r2=usi.charCodeAt(3)-96;
    const prom = usi.endsWith("+");
    const pc = pos.sq[sqkey(f1,r1)];
    const cap = pos.sq[sqkey(f2,r2)];
    if (cap) pos.hand[pos.side][cap.k] = (pos.hand[pos.side][cap.k]||0)+1;
    delete pos.sq[sqkey(f1,r1)];
    pos.sq[sqkey(f2,r2)] = {c: pc.c, k: pc.k, p: pc.p || prom};
  }
  pos.side = (pos.side === "b") ? "w" : "b";
}
function posAt(n){
  const p = parseSFEN(cur.sfen);
  for (let i=0;i<n;i++) applyUSI(p, cur.solution_usi[i]);
  return p;
}
function lastSquares(n){
  if (n===0) return [];
  const u = cur.solution_usi[n-1];
  if (u[1]==="*") return [[+u[2], u.charCodeAt(3)-96]];
  return [[+u[0], u.charCodeAt(1)-96],[+u[2], u.charCodeAt(3)-96]];
}
function handStr(h){
  const order=["R","B","G","S","N","L","P"], out=[];
  for (const k of order) if (h[k]>0) out.push(JP[k]+(h[k]>1?h[k]:""));
  return out.join(" ") || "なし";
}
function render(){
  pos = posAt(ply);
  const last = lastSquares(ply).map(([f,r])=>sqkey(f,r));
  const t = document.getElementById("board"); t.innerHTML="";
  for (let r=1;r<=9;r++){
    const tr=document.createElement("tr");
    for (let f=9;f>=1;f--){
      const td=document.createElement("td");
      const pc=pos.sq[sqkey(f,r)];
      if (pc){
        td.textContent = pc.p ? JPP[pc.k] : JP[pc.k];
        td.className = pc.c + (last.includes(sqkey(f,r)) ? " last" : "") + (pc.p?" prom":"");
      } else if (last.includes(sqkey(f,r))) td.className="last";
      tr.appendChild(td);
    }
    t.appendChild(tr);
  }
  document.getElementById("hands").textContent =
    `攻方持駒: ${handStr(pos.hand.b)} ／ 玉方持駒: ${handStr(pos.hand.w)} ／ 手番: ${pos.side==="b"?"攻方":"玉方"} ／ ${ply}手目`;
  const mv=document.getElementById("moves"); mv.innerHTML="";
  cur.moves_jp.forEach((s,i)=>{
    const d=document.createElement("div");
    d.textContent = `${i+1} ${s}`;
    if (i < ply) d.className="cur";
    d.style.cursor="pointer";
    d.onclick=()=>{ ply=i+1; render(); };
    mv.appendChild(d);
  });
}
async function load(id){
  cur = await (await fetch((window.OT_CONFIG.dir||"problems/")+id+".json")).json();
  ply = 0;
  document.getElementById("title").textContent =
    `${cur.collection_title||""} 第${cur.number}番（${cur.solution_moves}手詰）— ${cur.author}${cur.published_year?"『"+cur.collection_title+"』"+cur.published_year+"年":""}`;
  const badges = [];
  badges.push(`<span class="badge">局面検証:${cur.status.position_verified?"✅":"❌"}</span>`);
  badges.push(`<span class="badge">解答検証:${cur.status.solution_verified?"✅":"❌"}</span>`);
  badges.push(`<span class="badge">別解検証:${cur.status.unique_solution_verified?"✅":"未"}</span>`);
  document.getElementById("badges").innerHTML = badges.join("");
  const rv = document.getElementById("review");
  if (cur.verification.needs_manual_review){
    rv.style.display=""; rv.textContent = "⚠ 原典画像との照合が未了のため要レビュー（needs_manual_review）。利用時は出典を確認してください。";
  } else rv.style.display="none";
  document.getElementById("prov").innerHTML =
    `原典: ${cur.source.title} ／ 所蔵: ${cur.source.repository} ／ 資料ID: ${cur.source.identifier||"—"} ／ `+
    `ページ: ${cur.source.page||"未照合"} ／ <a href="${cur.source.url}">アーカイブ</a><br>`+
    `検証: ${cur.verification.method}（${cur.verification.tool}）／ 照合用参考: ${(cur.verification.reference_urls||[]).map(u=>`<a href="${u}">参考KIF</a>`).join(" ")}<br>`+
    `権利: 原作品 ${cur.rights.original_work} ／ 本レコード ${cur.rights.dataset_record}`;
  document.getElementById("dlKif").href = "problems/"+id+".kif";
  document.getElementById("dlKif").download = id+".kif";
  document.getElementById("dlJson").href = "problems/"+id+".json";
  document.getElementById("dlJson").download = id+".json";
  render();
}
document.getElementById("prev").onclick=()=>{ if(ply>0){ply--;render();} };
document.getElementById("next").onclick=()=>{ if(ply<cur.solution_usi.length){ply++;render();} };
document.getElementById("start").onclick=()=>{ ply=0; render(); };
document.getElementById("end").onclick=()=>{ ply=cur.solution_usi.length; render(); };
document.getElementById("copySfen").onclick=()=>{
  navigator.clipboard.writeText(cur.sfen).then(()=>alert("SFENをコピーしました"));
};
(async ()=>{
  index = await (await fetch(window.OT_CONFIG.index||"index.json")).json();
  const sel = document.getElementById("plist");
  for (const p of index.problems){
    const o=document.createElement("option");
    o.value=p.id; o.textContent=`${p.collection_title||p.collection_id} 第${p.number}番（${p.solution_moves}手詰）`;
    sel.appendChild(o);
  }
  sel.onchange=()=>load(sel.value);
  await load(index.problems[0].id);
})();
