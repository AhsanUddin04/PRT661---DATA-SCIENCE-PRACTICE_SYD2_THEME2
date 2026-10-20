// Shared helpers for building the A4 report with docx-js
const fs = require("fs");
const path = require("path");
const {
  Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell, WidthType, ShadingType,
  BorderStyle, ImageRun, PageBreak, ExternalHyperlink, TabStopType,
} = require("docx");

const FONT = "Times New Roman";
const BODY = 23;        // 11.5 pt
const SMALL = 18;       // 9 pt (tables)
const CONTENT_W = 9638; // A4 with 2 cm margins (11906 - 2*1134)
const BLUE = "1F4E8C";

let figN = 0, tabN = 0;

// --- inline markup: **bold**, *italic*, `code`, [text](url) ---------------------
function runs(text, opts = {}) {
  const out = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/g;
  let last = 0, m;
  const size = opts.size || BODY;
  const base = { font: FONT, size, color: opts.color };
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push(new TextRun({ ...base, text: text.slice(last, m.index), bold: opts.bold, italics: opts.italics }));
    const t = m[0];
    if (t.startsWith("**")) out.push(new TextRun({ ...base, text: t.slice(2, -2), bold: true, italics: opts.italics }));
    else if (t.startsWith("`")) out.push(new TextRun({ font: "Consolas", size: size - 3, text: t.slice(1, -1), color: "333333" }));
    else if (t.startsWith("[")) {
      const mm = t.match(/\[([^\]]+)\]\(([^)]+)\)/);
      out.push(new ExternalHyperlink({ link: mm[2], children: [new TextRun({ ...base, text: mm[1], style: "Hyperlink", color: "1155CC", underline: {} })] }));
    } else out.push(new TextRun({ ...base, text: t.slice(1, -1), italics: true, bold: opts.bold }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun({ ...base, text: text.slice(last), bold: opts.bold, italics: opts.italics }));
  return out;
}

const P = (text, o = {}) => new Paragraph({
  children: runs(text, o), alignment: o.align || AlignmentType.JUSTIFIED,
  spacing: { after: o.after ?? 100, before: o.before ?? 0, line: o.line || 252 }, keepNext: o.keepNext,
});
const H1 = (t, o = {}) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text: t, font: FONT })],
  pageBreakBefore: o.pageBreak ?? false, spacing: { before: 120, after: 120 } });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text: t, font: FONT })],
  spacing: { before: 200, after: 80 }, keepNext: true });
const H3 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun({ text: t, font: FONT })],
  spacing: { before: 140, after: 60 }, keepNext: true });
const B = (text, lvl = 0) => new Paragraph({ numbering: { reference: "bullets", level: lvl }, children: runs(text),
  alignment: AlignmentType.LEFT, spacing: { after: 50, line: 252 } });
const N = (text, ref = "numbers") => new Paragraph({ numbering: { reference: ref, level: 0 }, children: runs(text),
  spacing: { after: 50, line: 252 } });
const PB = () => new Paragraph({ children: [new PageBreak()] });

function caption(kind, text) {
  const n = kind === "Figure" ? ++figN : ++tabN;
  return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 40, after: 140 }, keepNext: kind === "Table",
    children: [new TextRun({ text: `${kind} A4.${n} — `, bold: true, font: FONT, size: 20 }), ...runs(text, { size: 20, italics: true })] });
}

function figure(file, widthPx, cap) {
  const buf = fs.readFileSync(file);
  // read PNG size
  const w = buf.readUInt32BE(16), h = buf.readUInt32BE(20);
  const width = widthPx, height = Math.round(widthPx * h / w);
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 60, after: 20 }, keepNext: true,
      children: [new ImageRun({ type: "png", data: buf, transformation: { width, height },
        altText: { title: cap.slice(0, 60), description: cap, name: path.basename(file) } })] }),
    caption("Figure", cap),
  ];
}

const border = { style: BorderStyle.SINGLE, size: 4, color: "A6ADB4" };
const borders = { top: border, bottom: border, left: border, right: border };

function table(headers, rows, widths, cap, o = {}) {
  const total = widths.reduce((a, b) => a + b, 0);
  const size = o.size || SMALL;
  const mk = (cells, head, zebra) => new TableRow({ tableHeader: head, cantSplit: true, children: cells.map((c, i) =>
    new TableCell({ borders, width: { size: widths[i], type: WidthType.DXA },
      shading: { fill: head ? "DCE6F2" : (zebra ? "F6F8FA" : "FFFFFF"), type: ShadingType.CLEAR, color: "auto" },
      margins: { top: 40, bottom: 40, left: 80, right: 80 },
      children: String(c).split("\n").map(line => new Paragraph({ alignment: (o.align && o.align[i]) || AlignmentType.LEFT,
        spacing: { after: 0, line: 228 }, children: runs(line, { size, bold: head || (o.boldRow && o.boldRow(cells)) }) })) })) });
  const out = [];
  if (cap) out.push(caption("Table", cap));
  out.push(new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: widths,
    rows: [mk(headers, true), ...rows.map((r, k) => mk(r, false, k % 2 === 1))] }));
  out.push(new Paragraph({ spacing: { after: 80 }, children: [] }));
  return out;
}

function code(lines, cap) {
  const out = [];
  const cell = new TableCell({ borders: { top: border, bottom: border, left: border, right: border },
    width: { size: CONTENT_W, type: WidthType.DXA }, shading: { fill: "F4F5F7", type: ShadingType.CLEAR, color: "auto" },
    margins: { top: 60, bottom: 60, left: 120, right: 120 },
    children: lines.map(l => new Paragraph({ spacing: { after: 0, line: 220 },
      children: [new TextRun({ text: l || " ", font: "Consolas", size: 15.5 })] })) });
  out.push(new Table({ width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: [CONTENT_W], rows: [new TableRow({ children: [cell] })] }));
  if (cap) out.push(caption("Figure", cap)); else out.push(new Paragraph({ spacing: { after: 80 }, children: [] }));
  return out;
}

function csv(file) {
  const [h, ...rows] = fs.readFileSync(file, "utf8").trim().split("\n");
  const keys = h.split(",");
  return rows.map(r => { const v = r.split(","); const o = {}; keys.forEach((k, i) => o[k] = isNaN(+v[i]) || v[i] === "" ? v[i] : +v[i]); return o; });
}

const f1 = x => (+x).toFixed(1), f2 = x => (+x).toFixed(2), f3 = x => (+x).toFixed(3);
const int = x => Math.round(+x).toLocaleString("en-AU");

module.exports = { P, H1, H2, H3, B, N, PB, figure, table, code, caption, csv, runs, f1, f2, f3, int,
  FONT, BODY, SMALL, CONTENT_W, BLUE, AlignmentType };
