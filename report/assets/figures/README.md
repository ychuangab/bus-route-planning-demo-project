# 報告圖表清單

以下圖表需以 Gemini 生成，放置於本目錄。

## 統一風格

所有圖表請遵循以下風格，確保視覺一致：
- **背景：** 白色或淺灰 (#f5f5f5)
- **主色：** 深藍 #1a237e、中藍 #1565c0、淺藍 #64b5f6
- **強調色：** 橘色 #ff9800（SA/站牌）、綠色 #4caf50（起點/通過）、紅色 #f44336（終點/警告）、紫色 #9c27b0（MILP）
- **文字：** 深灰 #333，無襯線字體，中文標籤
- **線條：** 2px 粗度，圓角
- **尺寸：** 1200×800px，適合報告嵌入

---

## Fig.1 — 總成本比較柱狀圖

**檔名：** `fig01-total-cost.png`
**用於：** Ch 6 實驗結果與比較

**Prompt：**
> Create a grouped bar chart comparing total cost across 5 maps and 5 optimization methods.
>
> X-axis: "Map 1", "Map 2", "Map 3", "Map 4", "Map 5"
> Y-axis: "總成本 (Total Cost)"
>
> 5 bars per map group, colored by method:
> - Baseline (gray #9e9e9e): 231, 1693, 1481, 10262, 2460
> - Greedy (green #4caf50): 220, 1654, 1391, 9921, 2314
> - GA (blue #1565c0): 211, 595, 979, 5803, 747
> - SA (orange #ff9800): 206, 571, 992, 5635, 638
> - MILP (purple #9c27b0): 222, 2769*, N/A, N/A, N/A
>
> For MILP Map 2 (2769), add an asterisk "*" and a small annotation: "超時非最優解".
> For MILP on Map 3-5, show a short bar with "N/A" label (solver failed or skipped).
> Note: MILP Map 2 cost (2769) is HIGHER than Baseline (1693), because MILP fixes the A* shortest route and cannot detour toward passenger clusters — this is a key limitation worth highlighting visually.
>
> Add a color legend at the top-right corner.
> Title: "五種方法總成本比較"
> White background, clean minimal style, subtle grid lines on Y-axis only.
> Size: 1200×800px.

---

## Fig.2 — 覆蓋率比較柱狀圖

**檔名：** `fig02-coverage.png`
**用於：** Ch 6 實驗結果與比較

**Prompt：**
> Create a grouped bar chart comparing passenger coverage rate across 5 maps and 5 methods.
>
> X-axis: "Map 1", "Map 2", "Map 3", "Map 4", "Map 5"
> Y-axis: "覆蓋率 Coverage Rate (%)" from 0% to 100%
>
> 5 bars per map group, colored by method:
> - Baseline (gray #9e9e9e): 70%, 13%, 39%, 30%, 1%
> - Greedy (green #4caf50): 75%, 14%, 42%, 30.8%, 4%
> - GA (blue #1565c0): 85%, 99%, 79%, 51.6%, 84%
> - SA (orange #ff9800): 85%, 100%, 75%, 51.8%, 95%
> - MILP (purple #9c27b0): 70%, 7%*, N/A, N/A, N/A
>
> For MILP Map 2 (7%), add an asterisk "*" and annotation: "超時非最優解，覆蓋率反而最低".
> For MILP on Map 3-5, show "N/A" label (no bar).
>
> Add a horizontal dashed green line at 80% labeled "良好覆蓋率門檻".
> Add a color legend at the top-right corner.
> Title: "五種方法覆蓋率比較（步行距離 ≤ 10 格）"
> White background, clean minimal style. Size: 1200×800px.

---

## Fig.3 — GA vs SA 穩定性箱型圖

**檔名：** `fig03-stability-boxplot.png`
**用於：** Ch 6 實驗結果與比較

**Prompt：**
> Create a box plot comparing the stability of GA vs SA across 5 maps, each with 10 independent runs.
>
> X-axis: 5 map groups, each with 2 boxes (GA in blue #1565c0, SA in orange #ff9800).
> Y-axis: "總成本 (Total Cost)"
>
> Data (mean ± std, min, max):
> - Map 1: GA (209.4±6.5, 194~216), SA (205.5±0.5, 205~206)
> - Map 2: GA (634.0±30.3, 590~685), SA (598.0±33.0, 567~676)
> - Map 3: GA (1111.3±154.9, 964~1392), SA (986.9±33.0, 951~1064)
> - Map 4: GA (6101.6±334.0, 5787~6679), SA (5710.4±102.9, 5627~5905)
> - Map 5: GA (737.9±31.1, 683~783), SA (654.5±20.4, 629~704)
>
> Show box with Q1/median/Q3, whiskers at min/max. Individual data points as semi-transparent dots.
>
> Highlight that SA consistently has smaller spread (lower std) than GA.
> Add annotation on Map 3: "GA std=155 vs SA std=33"
> Add annotation on Map 4: "GA std=334 vs SA std=103"
>
> Legend: blue = GA, orange = SA
> Title: "GA vs SA 穩定性比較（10 次獨立執行）"
> White background, clean style. Size: 1200×800px.

---

## Fig.4 — 消融實驗雷達圖

**檔名：** `fig04-ablation-radar.png`
**用於：** Ch 7 消融實驗

**Prompt：**
> Create a radar chart (spider chart) comparing 5 weight strategies on Map 2 using GA optimizer.
>
> Three axes (triangular radar):
> - "路線成本 Route Cost"
> - "步行成本 Walk Cost"
> - "站牌成本 Stop Cost"
>
> 5 overlapping polygons, one per strategy:
> - "均衡" (α=1.0, β=1.0, γ=1.0): route=115, walk=438, stop=42 — solid blue #1565c0
> - "乘客優先" (α=0.3, β=1.0, γ=0.3): route=127, walk=477, stop=42 — solid green #4caf50
> - "營運優先" (α=1.0, β=0.3, γ=0.3): route=105, walk=487, stop=36 — solid orange #ff9800
> - "站牌節省" (α=0.3, β=0.3, γ=1.0): route=117, walk=454, stop=42 — solid purple #9c27b0
> - "極端乘客" (α=0.1, β=1.0, γ=0.1): route=119, walk=486, stop=42 — solid red #f44336
>
> Each polygon has semi-transparent fill (20% opacity) and solid 2px border.
> Show data point values at each vertex.
>
> Add a legend showing strategy name + (α, β, γ) values.
> Title: "消融實驗 — 權重策略對成本分項影響（Map 2 × GA）"
> White background, clean style. Size: 1000×1000px.

---

## Fig.5 — Map 2 路線形狀對比

**檔名：** `fig05-route-comparison.png`
**用於：** Ch 6 實驗結果與比較

**Prompt：**
> Create a side-by-side comparison of two bus routes on a 50×50 city grid (Map 2).
>
> **Left panel — "Baseline（A* 最短路徑）":**
> A 50×50 grid with light gray background. Start point "A" at top-left area (green #4caf50 circle), End point "B" at bottom-right area (red #f44336 circle).
> Draw a straight/diagonal shortest route from A to B in gray #9e9e9e thick line.
> Show two clusters of passengers (small white dots):
> - Cluster 1: ~50 dots grouped at upper-right area
> - Cluster 2: ~50 dots grouped at lower-left area
> The route passes far from both clusters.
> Place 8 equidistant stop markers (orange #ff9800 squares) along the route.
> Label: "Coverage: 13%" in red.
>
> **Right panel — "SA（中繼點偏移路線）":**
> Same grid, same passengers, same A and B.
> Draw a curved/zigzag route (orange #ff9800 thick line) that detours through BOTH passenger clusters.
> The route bends toward upper-right cluster then curves to lower-left cluster before reaching B.
> Place 8 stop markers (orange squares) at positions near passenger clusters.
> Draw faint lines from passengers to their nearest stop.
> Label: "Coverage: 100%" in green.
>
> Add a shared title: "路線形狀對比 — Baseline vs SA（Map 2）"
> Between panels, add annotation: "SA 透過中繼點改變路線形狀，覆蓋率從 13% 提升至 100%"
> White background, clean style. Size: 1400×700px.

---

## Fig.6 — 問題架構與方法層次圖

**檔名：** `fig06-architecture.png`
**用於：** Ch 3 數學建模 / Ch 5 演算法設計

**Prompt：**
> Create a layered architecture diagram showing the bus route optimization system structure.
>
> **Top layer — "輸入 (Input)"** (light gray rounded box):
> Three items in a row:
> - "NxN 網格地圖" with grid icon
> - "乘客位置分布" with dots icon
> - "端點 A, B" with pin icon
>
> Arrow down →
>
> **Middle layer — "優化方法 (Optimizers)"** (blue section):
> Five boxes in a row, each a rounded card:
> - "Baseline" (gray #9e9e9e) — subtitle: "A* + 等距站牌"
> - "Greedy" (green #4caf50) — subtitle: "A* + 貪心選址"
> - "GA" (blue #1565c0) — subtitle: "染色體 = 中繼點+站牌"
> - "SA" (orange #ff9800) — subtitle: "鄰域操作+退火"
> - "MILP" (purple #9c27b0) — subtitle: "整數規劃精確解"
>
> All five boxes connect down to a shared component:
> **Shared layer — "A* 路徑引擎"** (dark blue #1a237e rounded box):
> "A* Pathfinding — Manhattan heuristic, 禁區避障, 中繼點路由"
>
> Arrow down →
>
> **Bottom layer — "評估引擎 (Evaluation)"** (light blue #64b5f6 rounded box):
> Three output items:
> - "Cost = α·route + β·walk + γ·stop"
> - "覆蓋率 Coverage"
> - "多次執行統計 mean±std"
>
> Arrow down →
>
> **Output box** (white with border):
> "results.json → 互動 Demo / 報告 / 簡報"
>
> White background, clean layered diagram style with subtle shadows. Size: 1200×900px.
