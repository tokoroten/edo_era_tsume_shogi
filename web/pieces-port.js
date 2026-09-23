"use strict";
/* web/pieces-port.js
 * tsume 盤面ソースの駒描画移植版（viewer.js と共存可能）。
 *
 * 移植元:
 * - board/Piece.tsx（五角形 inline-SVG、style 3種、成駒の二重手がかり）
 * - board/piece-glyphs.ts（漢字/ラテン表記、玉方の玉・攻方の王の使い分け）
 * - board/ShogiBoard.tsx（手番色分け=isDefender、CSSクラス契約）
 * - styles/board.css（駒パートのクラス契約）
 *
 * 共存方針:
 * - このファイルは IIFE + window.OT_Pieces 名前空間のみで公開する。
 *   トップレベルに const KOMA_PATH 等を置かないため、viewer.js の同名
 *   定数と衝突しない（classic script 二重読み込みでも再宣言エラーなし）。
 * - viewer.js は一切書き換えない。統合は将来別タスクで viewer.js 側の
 *   呼び出し1行を OT_Pieces.pieceSVG に差し替える形で行う。
 *
 * 必要なCSSクラス（zukou.html / musou.html に既存のものと同名）:
 *   .piece / .piece--defender / .piece__body / .piece__highlight /
 *   .piece__kanji / .piece__kanji--promoted / .piece__latin /
 *   .piece__promoted-bar
 * hybrid / international を使う場合は .piece__latin の規則も必要。
 */
(function () {
  // 駒の五角形。画像・外部フォント不要の inline-SVG。
  var KOMA_PATH = "M50 3 L85 19 L94 102 L6 102 L15 19 Z";
  var KOMA_HIGHLIGHT = "M50 8 L81 23 L89 96";

  /**
   * 駒種ごとの盤面サイズ（表面 幅×高さ mm）。
   * 移植元: tsume apps/web Piece.tsx KOMA_DIMENSIONS
   * （天童佐藤の御蔵・雲南作木製駒の一製造元の比率。普遍規格ではない。
   *  香・歩は一律縮小ではなく細身。成っても形状は変わらないため
   *  成前種で引く）。
   */
  var KOMA_DIMENSIONS = {
    K: [28, 31.5], R: [27, 30.5], B: [27, 30.5], G: [26, 29.5],
    S: [26, 29.5], N: [25, 28.5], L: [23, 28], P: [22.5, 27]
  };

  /** 玉基準のXYスケールと、字形を歪ませないための文字スケール。 */
  function komaScales(pieceType) {
    var d = KOMA_DIMENSIONS[pieceType] || KOMA_DIMENSIONS.P;
    var base = KOMA_DIMENSIONS.K;
    var sx = d[0] / base[0], sy = d[1] / base[1];
    return { sx: sx, sy: sy, glyph: Math.min(sx, sy) };
  }

  function fmt(n) {
    return (Math.round(n * 10000) / 10000).toString();
  }

  // 基本漢字（未成駒）。玉/王は pieceKanji() で手番により使い分ける。
  var KANJI = {
    K: "王", R: "飛", B: "角", G: "金",
    S: "銀", N: "桂", L: "香", P: "歩"
  };

  // 成駒の漢字。K・G には成駒がないため含めない。
  var PROMOTED_KANJI = {
    P: "と", L: "杏", N: "圭", S: "全", B: "馬", R: "龍"
  };

  // international / hybrid 用ラテン表記。
  var LATIN = {
    K: "K", R: "R", B: "B", G: "G",
    S: "S", N: "N", L: "L", P: "P"
  };

  var VALID_TYPES = { K: 1, R: 1, B: 1, G: 1, S: 1, N: 1, L: 1, P: 1 };

  /**
   * 成駒として装飾すべきか。K・G は成れないため除外する。
   * Piece.tsx の promoted 判定と同等。
   */
  function shouldShowPromoted(pieceType, promoted) {
    return Boolean(promoted) && pieceType !== "K" && pieceType !== "G";
  }

  /**
   * 漢字1文字を返す。玉方の玉・攻方の王の使い分けは印刷物の慣習。
   * @param {string} pieceType "K|R|B|G|S|N|L|P"
   * @param {boolean} promoted
   * @param {boolean} isDefender 玉方なら true
   */
  function pieceKanji(pieceType, promoted, isDefender) {
    if (pieceType === "K") return isDefender ? "玉" : "王";
    if (promoted && PROMOTED_KANJI[pieceType]) return PROMOTED_KANJI[pieceType];
    return KANJI[pieceType] || "?";
  }

  /**
   * ラテン表記を返す。成駒（K・G除く）は "+X" 形。
   */
  function pieceLatin(pieceType, promoted) {
    var base = LATIN[pieceType] || "?";
    if (shouldShowPromoted(pieceType, promoted)) return "+" + base;
    return base;
  }

  /** viewer.js 形 {c,k,p} と tsume 形 {type,color,promoted} の両方を受け付ける。 */
  function normalize(piece) {
    var pieceType = piece.type || piece.k || "P";
    if (!VALID_TYPES[pieceType]) pieceType = "P";
    var color = piece.color || piece.c || "b";
    var promoted = Boolean(piece.promoted !== undefined ? piece.promoted : piece.p);
    return {
      pieceType: pieceType,
      isDefender: color === "w",
      promoted: promoted
    };
  }

  /** SVGテキストノード用エスケープ（現行の駒文字には記号が無いが念のため）。 */
  function escapeXml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  /**
   * 駒SVG文字列を返す。viewer.js の pieceSVG(pc) と対応するが、
   * 第2引数で Piece.tsx の style 3種を切り替えできる。
   *
   * @param {{k?:string,type?:string,c?:string,color?:string,p?:boolean,promoted?:boolean}} piece
   * @param {{style?: "traditional"|"hybrid"|"international"}} [options]
   * @returns {string} svg 要素のHTML文字列
   */
  function pieceSVG(piece, options) {
    var style = (options && options.style) || "traditional";
    if (style !== "hybrid" && style !== "international") style = "traditional";

    var n = normalize(piece);
    var kanji = pieceKanji(n.pieceType, n.promoted, n.isDefender);
    var latin = pieceLatin(n.pieceType, n.promoted);
    var showPromoted = shouldShowPromoted(n.pieceType, n.promoted);

    var svgClass = "piece" + (n.isDefender ? " piece--defender" : "");
    var kanjiClass = "piece__kanji" + (showPromoted ? " piece__kanji--promoted" : "");
    var latinClass = "piece__latin" + (showPromoted ? " piece__kanji--promoted" : "");

    // 成駒は色（赤文字）だけでなく下線バーも付ける。
    // 色だけに依存しない二重の手がかり（Piece.tsx の注釈と同趣旨）。
    var bar = "";
    if (showPromoted) {
      if (style === "hybrid") {
        bar = '<rect class="piece__promoted-bar" x="32" y="70" width="36" height="4" rx="2"/>';
      } else {
        bar = '<rect class="piece__promoted-bar" x="28" y="84" width="44" height="5" rx="2"/>';
      }
    }

    // 本体（五角形＋光沢）は駒種の実寸比でXYスケールする。
    // 文字は min 比で等方スケールし、細身駒でも字形を歪ませない
    // （Piece.tsx と同等の二重 <g transform> 構成）。
    var sc = komaScales(n.pieceType);
    var bodyOpen = '<svg class="' + svgClass + '" viewBox="0 0 100 108" aria-hidden="true">' +
      '<g transform="translate(50 54) scale(' + fmt(sc.sx) + " " + fmt(sc.sy) + ') translate(-50 -54)">' +
      '<path class="piece__body" d="' + KOMA_PATH + '"/>' +
      '<path class="piece__highlight" d="' + KOMA_HIGHLIGHT + '"/></g>';
    var glyphOpen = '<g transform="translate(50 54) scale(' + fmt(sc.glyph) + ') translate(-50 -54)">';

    if (style === "hybrid") {
      return bodyOpen + glyphOpen +
        '<text class="' + kanjiClass + '" x="50" y="64" font-size="50">' + escapeXml(kanji) + "</text>" +
        '<text class="piece__latin" x="50" y="94" font-size="24">' + escapeXml(latin) + "</text>" +
        bar + "</g></svg>";
    }
    if (style === "international") {
      var fontSize = latin.length > 1 ? 42 : 58;
      return bodyOpen + glyphOpen +
        '<text class="' + latinClass + '" x="50" y="76" font-size="' + fontSize + '">' +
        escapeXml(latin) + "</text>" + bar + "</g></svg>";
    }
    // traditional: 現行 viewer.js と同じ配置（漢字のみ、y=76 / 62px）。
    return bodyOpen + glyphOpen +
      '<text class="' + kanjiClass + '" x="50" y="76" font-size="62">' + escapeXml(kanji) + "</text>" +
      bar + "</g></svg>";
  }

  /**
   * スクリーンリーダー用の駒名（任意）。統合時に td の aria-label へ利用可能。
   * 例: "玉方の銀" / "攻方のと"。
   */
  function describePiece(piece) {
    var n = normalize(piece);
    var kanji = pieceKanji(n.pieceType, n.promoted, n.isDefender);
    return (n.isDefender ? "玉方の" : "攻方の") + kanji;
  }

  window.OT_Pieces = {
    pieceSVG: pieceSVG,
    pieceKanji: pieceKanji,
    pieceLatin: pieceLatin,
    shouldShowPromoted: shouldShowPromoted,
    describePiece: describePiece,
    komaScales: komaScales,
    KOMA_PATH: KOMA_PATH,
    KOMA_HIGHLIGHT: KOMA_HIGHLIGHT,
    KOMA_DIMENSIONS: KOMA_DIMENSIONS
  };
})();
