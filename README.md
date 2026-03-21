# 公車路線與站點設置規劃

Bus Route & Stop Placement Optimization — 面試題目二

## 專案說明

在 2D 城市網格中，從發車站 A 到目的地 B，規劃公車路線與站牌位置，最小化加權總成本：

**Cost = α · route_cost + β · Σwalk_cost + γ · Σ(fixed_cost + terrain_bonus)**

## 優化方法

| 方法 | 說明 |
|------|------|
| **Baseline** | A* 最短路徑 + 等距站牌 |
| **Greedy** | A* 路徑 + 貪心站牌選址 |
| **GA** | 基因演算法全域搜索 |
| **SA** | 模擬退火鄰域搜索 |
| **MILP** | 混合整數線性規劃精確解 |

## 線上展示

- **互動 Demo**: https://bus-route-planning-demo-project.vercel.app
- **技術報告**: https://bus-route-planning-demo-project.vercel.app/report/
- **簡報**: https://bus-route-planning-demo-project.vercel.app/slides/

## 技術棧

- **前端**: Vite + HTML Canvas (2D)
- **後端計算**: Python (numpy, PuLP)
- **部署**: Vercel

## 作者

Eason Huang
