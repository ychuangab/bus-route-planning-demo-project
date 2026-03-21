#!/usr/bin/env node
/**
 * sync-docs.mjs
 * Converts report (Markdown→HTML) and slides (Marp→HTML) into public/ for deployment.
 */
import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import { marked } from 'marked';

// Find repo root by walking up from this script until we find report/REPORT.md
const FRONTEND = path.resolve(import.meta.dirname, '..');
let ROOT = FRONTEND;
for (let i = 0; i < 5; i++) {
  if (fs.existsSync(path.join(ROOT, 'report', 'REPORT.md'))) break;
  ROOT = path.resolve(ROOT, '..');
}
if (!fs.existsSync(path.join(ROOT, 'report', 'REPORT.md'))) {
  console.error('Cannot find report/REPORT.md from', FRONTEND);
  process.exit(1);
}
const PUBLIC = path.join(FRONTEND, 'public');

// ── Helper ──────────────────────────────────────────────
function copyDirSync(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const s = path.join(src, entry.name);
    const d = path.join(dest, entry.name);
    if (entry.isDirectory()) copyDirSync(s, d);
    else fs.copyFileSync(s, d);
  }
}

// ── 1. Report ───────────────────────────────────────────
console.log('Building report…');
const reportDir = path.join(PUBLIC, 'report');
fs.mkdirSync(reportDir, { recursive: true });

// Copy figures
const figSrc = path.join(ROOT, 'report', 'assets', 'figures');
const figDest = path.join(reportDir, 'assets', 'figures');
if (fs.existsSync(figSrc)) copyDirSync(figSrc, figDest);

// Convert markdown → HTML
const reportMd = fs.readFileSync(path.join(ROOT, 'report', 'REPORT.md'), 'utf-8');
const reportBody = marked.parse(reportMd);

const reportHtml = `<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>公車路線與站點設置規劃 — 技術報告</title>
<style>
  :root { --blue: #1a237e; --mid: #64b5f6; --light: #90caf9; --bg: #0d1117; --bg2: #161b22; --fg: #e0e0e0; }
  * { box-sizing: border-box; }
  body {
    max-width: 900px; margin: 0 auto; padding: 2rem 1.5rem;
    font-family: 'Noto Sans TC', 'Microsoft JhengHei', system-ui, sans-serif;
    color: var(--fg); line-height: 1.7; background: var(--bg);
  }
  h1 { color: #ffffff; border-bottom: 3px solid var(--mid); padding-bottom: .3em; }
  h2 { color: var(--mid); border-bottom: 1px solid #333; padding-bottom: .2em; }
  h3 { color: var(--mid); }
  hr { border-color: #333; }
  table { border-collapse: collapse; width: 100%; margin: 1em 0; }
  th, td { border: 1px solid #444; padding: .5em .8em; text-align: left; color: var(--fg); }
  th { background: #1565c0; color: #fff; }
  td { background: rgba(255,255,255,0.04); }
  code {
    background: rgba(255,255,255,0.08); padding: .15em .4em; border-radius: 3px;
    font-size: 0.9em; color: var(--light);
  }
  pre { background: var(--bg2); color: #ddd; padding: 1em; border-radius: 6px; overflow-x: auto; border: 1px solid #333; }
  pre code { background: none; color: inherit; padding: 0; }
  blockquote {
    border-left: 4px solid var(--mid); margin: 1em 0; padding: .5em 1em;
    background: rgba(100,181,246,0.08); color: var(--fg);
  }
  img { max-width: 100%; height: auto; display: block; margin: 1em auto; }
  a { color: var(--mid); }
  strong { color: #ffffff; }
</style>
</head>
<body>
${reportBody}
</body>
</html>`;

fs.writeFileSync(path.join(reportDir, 'index.html'), reportHtml);
console.log('  ✓ report/index.html');

// ── 2. Slides ───────────────────────────────────────────
console.log('Building slides…');
const slidesDir = path.join(PUBLIC, 'slides');
fs.mkdirSync(slidesDir, { recursive: true });

// Copy figures for slides too
const slidesMdRaw = fs.readFileSync(path.join(ROOT, 'slides', 'slides.md'), 'utf-8');
const slidesMdFixed = slidesMdRaw.replace(/\.\.\/report\/assets\/figures\//g, 'figures/');

const tmpSlidesMd = path.join(slidesDir, '_slides_tmp.md');
fs.writeFileSync(tmpSlidesMd, slidesMdFixed);

// Copy figures into slides dir
const slidesFigDest = path.join(slidesDir, 'figures');
if (fs.existsSync(figSrc)) copyDirSync(figSrc, slidesFigDest);

try {
  execSync(
    `npx marp --html --allow-local-files "${tmpSlidesMd}" -o "${path.join(slidesDir, 'index.html')}"`,
    { cwd: slidesDir, stdio: 'inherit' }
  );
  console.log('  ✓ slides/index.html');
} catch (e) {
  console.error('  ✗ Marp build failed:', e.message);
  process.exit(1);
} finally {
  if (fs.existsSync(tmpSlidesMd)) fs.unlinkSync(tmpSlidesMd);
}

console.log('Done!');
