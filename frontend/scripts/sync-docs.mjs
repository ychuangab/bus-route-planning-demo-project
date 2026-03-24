#!/usr/bin/env node
/**
 * sync-docs.mjs
 * Converts report (Markdown→HTML) and slides (Marp→HTML) into public/ for deployment.
 */
import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { marked } from 'marked';

// Node 18 compat: import.meta.dirname not available until Node 21
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Find repo root by walking up from this script until we find report/REPORT.md
const FRONTEND = path.resolve(__dirname, '..');
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

const NAV_STYLES = `
.page-nav {
  position: fixed; top: 0; left: 0; right: 0; z-index: 1000;
  background: rgba(13,17,23,0.95); backdrop-filter: blur(8px);
  border-bottom: 1px solid #30363d;
  display: flex; justify-content: center; align-items: center; gap: 4px; height: 42px;
  font-family: 'Segoe UI', system-ui, sans-serif;
}
.page-nav a {
  color: #8b949e; text-decoration: none; padding: 4px 14px;
  border-radius: 6px; font-size: 0.875rem; font-weight: 500;
  transition: color 0.15s, background 0.15s;
}
.page-nav a:hover { color: #e0e0e0; background: rgba(255,255,255,0.06); }
.page-nav a.active { color: #64b5f6; font-weight: 600; }
.page-nav .nav-sep { color: #30363d; user-select: none; }
`;

const NAV_HTML = (active) => `<nav class="page-nav">
  <a href="/"${active==='demo'?' class="active"':''}>Demo</a>
  <span class="nav-sep">·</span>
  <a href="/report/"${active==='report'?' class="active"':''}>Report</a>
  <span class="nav-sep">·</span>
  <a href="/slides/"${active==='slides'?' class="active"':''}>Slides</a>
</nav>`;

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
    padding-top: calc(2rem + 44px);
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
  .katex { font-size: 1.1em; }
${NAV_STYLES}
</style>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"
  onload="renderMathInElement(document.body, {delimiters:[{left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false}]});"></script>
</head>
<body>
${NAV_HTML('report')}
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
  // Inject nav bar into Marp-generated slides HTML
  const slidesHtmlPath = path.join(slidesDir, 'index.html');
  const slidesNavStyles = `<style>
.page-nav-slides {
  position: fixed; top: 0; left: 0; right: 0; z-index: 99999;
  background: rgba(13,17,23,0.88); backdrop-filter: blur(8px);
  border-bottom: 1px solid rgba(48,54,61,0.8);
  display: flex; justify-content: center; align-items: center; gap: 4px; height: 38px;
  font-family: 'Segoe UI', system-ui, sans-serif;
  transition: opacity 0.3s;
}
.page-nav-slides a {
  color: #8b949e; text-decoration: none; padding: 3px 12px;
  border-radius: 6px; font-size: 0.8rem; font-weight: 500;
}
.page-nav-slides a:hover { color: #e0e0e0; background: rgba(255,255,255,0.08); }
.page-nav-slides a.active { color: #64b5f6; font-weight: 600; }
.page-nav-slides .nav-sep { color: #30363d; user-select: none; }
</style>`;
  const slidesNavHtml = `<nav class="page-nav-slides" id="slides-nav">
  <a href="/">Demo</a>
  <span class="nav-sep">·</span>
  <a href="/report/">Report</a>
  <span class="nav-sep">·</span>
  <a href="/slides/" class="active">Slides</a>
</nav>
<script>(function(){
  var nav=document.getElementById('slides-nav'),t;
  function hide(){nav.style.opacity='0.15';}
  function show(){nav.style.opacity='1';clearTimeout(t);t=setTimeout(hide,2500);}
  document.addEventListener('mousemove',show);
  t=setTimeout(hide,2500);
})();<\/script>`;
  let slidesHtml = fs.readFileSync(slidesHtmlPath, 'utf-8');
  slidesHtml = slidesHtml.replace('</style></head><body>', `${slidesNavStyles}</style></head><body>${slidesNavHtml}`);
  fs.writeFileSync(slidesHtmlPath, slidesHtml);
  console.log('  ✓ slides/index.html (nav injected)');
} catch (e) {
  console.error('  ✗ Marp build failed:', e.message);
  process.exit(1);
} finally {
  if (fs.existsSync(tmpSlidesMd)) fs.unlinkSync(tmpSlidesMd);
}

console.log('Done!');
