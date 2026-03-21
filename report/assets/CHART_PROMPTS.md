# 圖表生成提示（供 Gemini 使用）

## 風格要求
- Dark mode 背景 (#0d1117)
- 藍色主題 (#64b5f6, #1565c0)
- 白色文字，清晰可讀
- 乾淨的圖表線條，避免多餘裝飾

## 圖表清單

### Fig 1: 總成本比較柱狀圖
5 張地圖 × 5 種方法的總成本柱狀圖（grouped bar chart）。
X 軸：Map 1-5，Y 軸：Total Cost。
5 種方法用不同顏色：Baseline(灰), Greedy(綠), GA(藍), SA(橙), MILP(紫)。
MILP 在 Map 2-5 標示 "N/A"。

### Fig 2: 覆蓋率比較柱狀圖
同上格式，Y 軸改為 Coverage Rate (%)。

### Fig 3: GA vs SA 穩定性箱型圖
5 張地圖，GA 和 SA 各 10 次執行的總成本分布。
用箱型圖 (box plot) 展示 min/Q1/median/Q3/max。

### Fig 4: 消融實驗雷達圖
5 組權重在 Map 2 上的三項成本比較。
用雷達圖 (radar chart)，三軸為 route_cost, walk_cost, stop_cost。

### Fig 5: Map 2 路線形狀對比
展示 Baseline vs GA 在 Map 2 的路線差異。
Baseline 直線路徑 vs GA 偏移接近乘客群聚的路線。

### Fig 6: 問題架構圖
展示問題的三層結構：路線規劃 → 站牌選址 → 成本評估。
包含 A* 底層、5 種上層方法、評估引擎的關係。
