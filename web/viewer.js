window.OT_CONFIG = window.OT_CONFIG || {index:"index.json", dir:"problems/"};

const ZEN = "０１２３４５６７８９", KAN = "〇一二三四五六七八九";
const JP = {P:"歩",L:"香",N:"桂",S:"銀",G:"金",B:"角",R:"飛",K:"玉"};
const JPP = {P:"と",L:"杏",N:"圭",S:"全",B:"馬",R:"龍"};

/*
 * Piece rendering delegates to web/pieces-port.js
 * (window.OT_Pieces.pieceSVG, traditional style).
 * Fallback below keeps the previous inline-SVG so the board still renders
 * if pieces-port.js fails to load.
 * Pentagon SVG adapted from tokoroten/tsume
 * (apps/web/src/components/board/Piece.tsx, board.css):
 * inline-SVG koma, no image or font download. Defender pieces are rotated.
 */
const KOMA_PATH = "M50 3 L85 19 L94 102 L6 102 L15 19 Z";
const KOMA_HIGHLIGHT = "M50 8 L81 23 L89 96";
function pieceSVG(pc){
  if (window.OT_Pieces && typeof window.OT_Pieces.pieceSVG === "function"){
    return window.OT_Pieces.pieceSVG(pc, {style: "traditional"});
  }
  const kanji = pc.k === "K" ? (pc.c === "w" ? "玉" : "王")
    : (pc.p ? JPP[pc.k] : JP[pc.k]);
  const def = pc.c === "w" ? " piece--defender" : "";
  const prom = (pc.p && pc.k !== "K" && pc.k !== "G") ? " piece__kanji--promoted" : "";
  const bar = prom
    ? '<rect class="piece__promoted-bar" x="28" y="84" width="44" height="5" rx="2"/>' : "";
  return `<svg class="piece${def}" viewBox="0 0 100 108" aria-hidden="true">` +
    `<path class="piece__body" d="${KOMA_PATH}"/>` +
    `<path class="piece__highlight" d="${KOMA_HIGHLIGHT}"/>` +
    `<text class="piece__kanji${prom}" x="50" y="76" font-size="62">${kanji}</text>` +
    bar + `</svg>`;
}

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
const PROMOTABLE = {P:1,L:1,N:1,S:1,B:1,R:1};
function inZone(color, rank){ return color === "b" ? rank <= 3 : rank >= 7; }
function jpSq(f,r){ return ZEN[f]+KAN[r]; }
function escHtml(s){
  return String(s ?? "").replace(/[&<>"']/g, (c)=>({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"
  }[c]));
}
function openMovesDetails(){
  const det = document.querySelector("details");
  if (det) det.open = true;
}
function clearViewerForError(){
  cur = null;
  const b = document.getElementById("board");
  if (b) b.innerHTML = "";
  const h = document.getElementById("hands");
  if (h) h.textContent = "";
  const badges = document.getElementById("badges");
  if (badges) badges.innerHTML = "";
  const rv = document.getElementById("review");
  if (rv) rv.style.display = "none";
  const prov = document.getElementById("prov");
  if (prov) prov.textContent = "";
  const dlKif = document.getElementById("dlKif");
  if (dlKif){ dlKif.setAttribute("href", "#"); dlKif.removeAttribute("download"); }
  const dlJson = document.getElementById("dlJson");
  if (dlJson){ dlJson.setAttribute("href", "#"); dlJson.removeAttribute("download"); }
  openMovesDetails();
}
function renderMovesJP(sfen, usiList){
  const bd = parseSFEN(sfen);
  const out = [];
  let prevDest = null;
  for (let i=0;i<usiList.length;i++){
    const m = usiList[i];
    const side = (i%2===0) ? "▲" : "△";
    let destKey;
    if (m[1] === "*"){
      const k = m[0], f = +m[2], r = m.charCodeAt(3)-96;
      out.push(`${side}${jpSq(f,r)}${JP[k]}打`);
      destKey = sqkey(f,r);
      bd.sq[destKey] = {c: bd.side, k, p:false};
      bd.hand[bd.side][k] = (bd.hand[bd.side][k]||0) - 1;
    } else {
      const f1=+m[0], r1=m.charCodeAt(1)-96, f2=+m[2], r2=m.charCodeAt(3)-96;
      const prom = m.endsWith("+");
      const pc = bd.sq[sqkey(f1,r1)];
      if (!pc) throw new Error("missing piece at "+f1+","+r1+" for "+m);
      let name, suffix;
      if (prom){ name = JP[pc.k]; suffix = "成"; }
      else if (pc.p){ name = JPP[pc.k] || JP[pc.k]; suffix = ""; }
      else if (PROMOTABLE[pc.k] && (inZone(pc.c, r1) || inZone(pc.c, r2))){ name = JP[pc.k]; suffix = "不成"; }
      else { name = JP[pc.k]; suffix = ""; }
      destKey = sqkey(f2,r2);
      const dest = (destKey === prevDest) ? "同　" : jpSq(f2,r2);
      out.push(`${side}${dest}${name}(${f1}${r1})${suffix}`);
      const cap = bd.sq[destKey];
      if (cap) bd.hand[pc.c][cap.k] = (bd.hand[pc.c][cap.k]||0)+1;
      delete bd.sq[sqkey(f1,r1)];
      bd.sq[destKey] = {c: pc.c, k: pc.k, p: pc.p || prom};
    }
    bd.side = (bd.side === "b") ? "w" : "b";
    prevDest = destKey;
  }
  return out;
}
function render(){
  if (!cur) return;
  try {
    pos = posAt(ply);
  } catch (e) {
    const mvErr = document.getElementById("moves");
    if (mvErr) mvErr.textContent =
      "局面データが不正のため盤面を表示できません。データ修正をお待ちください。";
    return;
  }
  const last = lastSquares(ply).map(([f,r])=>sqkey(f,r));
  const t = document.getElementById("board"); t.innerHTML="";
  for (let r=1;r<=9;r++){
    const tr=document.createElement("tr");
    for (let f=9;f>=1;f--){
      const td=document.createElement("td");
      const pc=pos.sq[sqkey(f,r)];
      if (pc){
        td.innerHTML = pieceSVG(pc);
        td.className = (last.includes(sqkey(f,r)) ? "last" : "");
      } else if (last.includes(sqkey(f,r))) td.className="last";
      tr.appendChild(td);
    }
    t.appendChild(tr);
  }
  document.getElementById("hands").textContent =
    `攻方持駒: ${handStr(pos.hand.b)} ／ 玉方持駒: ${handStr(pos.hand.w)} ／ 手番: ${pos.side==="b"?"攻方":"玉方"} ／ ${ply}手目`;
  const mv=document.getElementById("moves"); mv.innerHTML="";
  const intendedHeader=document.createElement("div");
  intendedHeader.textContent="想定解法（原典翻刻）";
  intendedHeader.style.fontWeight="bold";
  mv.appendChild(intendedHeader);
  const intended = cur.intended_solution_usi;
  if (intended == null || (Array.isArray(intended) && intended.length === 0)){
    const d=document.createElement("div");
    d.textContent="想定解法：未翻刻";
    mv.appendChild(d);
  } else {
    const info=document.createElement("div");
    const n = cur.intended_solution_moves != null ? cur.intended_solution_moves : intended.length;
    const src = cur.intended_solution_source != null ? `（出典: ${cur.intended_solution_source}）` : "";
    info.textContent=`想定解法：${n}手${src}`;
    mv.appendChild(info);
    let intendedJp = null;
    try { intendedJp = renderMovesJP(cur.sfen, intended); } catch (e) { intendedJp = null; }
    const intendedList = intendedJp || intended;
    intendedList.forEach((s,i)=>{
      const d=document.createElement("div");
      d.textContent=`${i+1} ${s}`;
      mv.appendChild(d);
    });
  }
  const verifiedHeader=document.createElement("div");
  verifiedHeader.textContent="検証解（ソルバー確認）";
  verifiedHeader.style.fontWeight="bold";
  verifiedHeader.style.marginTop="0.5em";
  mv.appendChild(verifiedHeader);
  const movesJp = Array.isArray(cur.moves_jp) ? cur.moves_jp : null;
  if (!movesJp){
    const d=document.createElement("div");
    d.textContent="検証解データがありません";
    mv.appendChild(d);
  } else {
    movesJp.forEach((s,i)=>{
      const d=document.createElement("div");
      d.textContent = `${i+1} ${s}`;
      if (i < ply) d.className="cur";
      d.style.cursor="pointer";
      d.setAttribute("tabindex", "0");
      d.setAttribute("role", "button");
      const goToMove=()=>{ ply=i+1; render(); };
      d.onclick=goToMove;
      d.onkeydown=(e)=>{
        if (e.key === "Enter" || e.key === " "){ e.preventDefault(); goToMove(); }
      };
      mv.appendChild(d);
    });
  }
}
async function load(id){
  try {
    const res = await fetch((window.OT_CONFIG.dir||"problems/")+id+".json");
    if (!res.ok) throw new Error("HTTP " + res.status);
    cur = await res.json();
  } catch (e) {
    clearViewerForError();
    document.getElementById("title").textContent = "問題データの読み込みに失敗しました";
    document.getElementById("moves").textContent =
      "問題データを取得できませんでした。ネットワーク接続を確認してページを再読み込みしてください。";
    return;
  }
  ply = 0;
  document.getElementById("title").textContent =
    `${cur.collection_title||""} 第${cur.number}番（${cur.solution_moves}手詰）— ${cur.author||""}${cur.published_year?`（${cur.published_year}年）`:""}`;
  const badges = [];
  badges.push(`<span class="badge">局面検証:${cur.status.position_verified?"✅":"❌"}</span>`);
  badges.push(`<span class="badge">解答検証:${cur.status.solution_verified?"✅":"❌"}</span>`);
  badges.push(`<span class="badge">別解検証:${cur.status.unique_solution_verified?"✅":"未"}</span>`);
  document.getElementById("badges").innerHTML = badges.join("");
  const rv = document.getElementById("review");
  if (cur.verification.needs_manual_review){
    rv.style.display=""; rv.textContent = "⚠ 原典画像との照合が未了のため要レビュー（needs_manual_review）。利用時は出典を確認してください。";
  } else rv.style.display="none";
  const alt = cur.source && cur.source.digital && cur.source.digital.alternative_holding;
  const altLine = alt ? `代替所蔵: ${escHtml(alt.title)} ／ ${escHtml(alt.repository)} ／ ${escHtml(alt.identifier||"—")} ／ <a href="${escHtml(alt.url)}">アーカイブ</a>${alt.access?` ／ ${escHtml(alt.access)}`:""}<br>` : "";
  document.getElementById("prov").innerHTML =
    `原典: ${escHtml(cur.source.title)} ／ 所蔵: ${escHtml(cur.source.repository)} ／ 資料ID: ${escHtml(cur.source.identifier||"—")} ／ `+
    `ページ: ${escHtml(cur.source.page||"未照合")} ／ <a href="${escHtml(cur.source.url)}">アーカイブ</a><br>`+
    altLine +
    `検証: ${escHtml(cur.verification.method)}（${escHtml(cur.verification.tool)}）／ 参考: ${(cur.verification.reference_urls||[]).map(u=>`<a href="${escHtml(u)}">参考</a>`).join(" ")}<br>`+
    `権利: 原作品 ${escHtml(cur.rights.original_work)} ／ 本レコード ${escHtml(cur.rights.dataset_record)}`;
  document.getElementById("dlKif").href = "problems/"+id+".kif";
  document.getElementById("dlKif").download = id+".kif";
  document.getElementById("dlJson").href = "problems/"+id+".json";
  document.getElementById("dlJson").download = id+".json";
  render();
}
document.getElementById("prev").onclick=()=>{ if(cur && ply>0){ply--;render();} };
document.getElementById("next").onclick=()=>{ if(cur && ply<cur.solution_usi.length){ply++;render();} };
document.getElementById("start").onclick=()=>{ if(!cur) return; ply=0; render(); };
document.getElementById("end").onclick=()=>{ if(!cur) return; ply=cur.solution_usi.length; render(); };
document.getElementById("copySfen").onclick=()=>{
  if(!cur) return;
  navigator.clipboard.writeText(cur.sfen).then(()=>alert("SFENをコピーしました"))
    .catch(()=>alert("SFENのコピーに失敗しました。手動でコピーしてください。"));
};
(async ()=>{
  try {
    const res = await fetch(window.OT_CONFIG.index||"index.json");
    if (!res.ok) throw new Error("HTTP " + res.status);
    index = await res.json();
  } catch (e) {
    clearViewerForError();
    document.getElementById("title").textContent = "問題一覧の読み込みに失敗しました";
    document.getElementById("moves").textContent =
      "問題データを取得できませんでした。ネットワーク接続を確認してページを再読み込みしてください。";
    return;
  }
  const sel = document.getElementById("plist");
  for (const p of index.problems){
    const o=document.createElement("option");
    o.value=p.id; o.textContent=`${p.collection_title||p.collection_id} 第${p.number}番（${p.solution_moves}手詰）`;
    sel.appendChild(o);
  }
  // Deep-link receive: trim・小文字化・3桁形式に正規化（送受統一）。
  // 例: " Zukou-1 " -> "zukou-001"。形式不正はnull＋明示メッセージ。
  function normalizeId(raw){
    if (typeof raw !== "string") return null;
    const s = raw.trim().toLowerCase();
    const m = s.match(/^([a-z0-9_-]+)-(\d+)$/);
    if (!m) return null;
    return m[1] + "-" + m[2].padStart(3, "0");
  }
  function findById(raw){
    const nid = normalizeId(raw);
    if (!nid) return null;
    return index.problems.find((p)=>typeof p.id === "string" && p.id.trim().toLowerCase() === nid) || null;
  }
  function showIdError(raw){
    clearViewerForError();
    const disp = raw == null ? "" : String(raw).trim();
    const nid = normalizeId(raw);
    if (!nid){
      document.getElementById("title").textContent = "IDの形式が正しくありません";
      document.getElementById("moves").textContent =
        `ID「${disp}」の形式が正しくありません。半角で「作品集ID-3桁番号」の形式で入力してください（例: zukou-001）。前後の空白と大文字小文字は自動で正規化されます。作品集一覧（index.html）から選び直してください。`;
      return;
    }
    const cm = nid.match(/^(.+)-(\d{3})$/);
    const col = cm ? cm[1] : nid;
    const guessPage = col + ".html";
    document.getElementById("title").textContent = "指定の問題はこの作品集にありません";
    document.getElementById("moves").textContent =
      `ID「${disp}」（正規化後: ${nid}）はこの作品集にありません。正しい作品集ページ（${guessPage}?id=${nid}）で開き直すか、作品集一覧（index.html）から選び直してください。`;
  }
  function resolveAndLoad(raw){
    if (raw == null || String(raw).trim() === ""){
      const target = index.problems[0].id;
      syncSelect(target);
      load(target);
      return;
    }
    const hit = findById(raw);
    if (hit){
      syncSelect(hit.id);
      load(hit.id);
      return;
    }
    showIdError(raw);
  }
  function syncSelect(id){
    if ([...sel.options].some((o)=>o.value === id)) sel.value = id;
  }
  function pushUrl(id){
    try { history.pushState({id}, "", "?id="+encodeURIComponent(id)); } catch (e) {}
  }
  sel.onchange=()=>{ pushUrl(sel.value); load(sel.value); };
  window.addEventListener("popstate", (ev)=>{
    const fromState = ev.state && typeof ev.state.id === "string" ? ev.state.id : null;
    const raw = fromState !== null ? fromState : new URLSearchParams(location.search).get("id");
    resolveAndLoad(raw);
  });
  const rawInit = new URLSearchParams(location.search).get("id");
  resolveAndLoad(rawInit);
})();
