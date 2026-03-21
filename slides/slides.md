---
marp: true
theme: default
class: lead
backgroundColor: #0d1117
color: #ffffff
style: |
  section {
    background: linear-gradient(135deg, #0d1117 0%, #1a237e 100%);
    color: #ffffff;
    font-family: 'Segoe UI', system-ui, sans-serif;
  }
  h1 { color: #64b5f6; font-size: 2.2em; }
  h2 { color: #90caf9; font-size: 1.6em; }
  h3 { color: #bbdefb; }
  strong { color: #ffffff; }
  a { color: #64b5f6; }
  pre { background: rgba(0,0,0,0.3); color: #e0e0e0; border: 1px solid rgba(255,255,255,0.15); border-radius: 8px; }
  code { background: rgba(255,255,255,0.1); color: #e0e0e0; padding: 2px 6px; border-radius: 4px; }
  blockquote { border-left: 4px solid #64b5f6; background: rgba(255,255,255,0.06); color: #e0e0e0; padding: 12px 16px; }
  table { background: transparent; border: 1px solid rgba(255,255,255,0.2); border-collapse: collapse; width: 100%; }
  th { background: rgba(255,255,255,0.1); color: #ffffff; border: 1px solid rgba(255,255,255,0.2); padding: 8px 12px; }
  td { background: rgba(255,255,255,0.05); color: #ffffff; border: 1px solid rgba(255,255,255,0.2); padding: 8px 12px; }
  tr { background: transparent !important; }
  li, p { color: #ffffff; }
  em { color: #90caf9; font-style: normal; }
  .highlight { color: #64b5f6; font-weight: bold; }
---

# 公車路線與站點設置規劃

**Bus Route & Stop Placement Optimization**

Eason Huang | 2026

---

## 問題概述

在 2D 城市網格中規劃公車路線 A→B 與站牌位置

**挑戰**：
- 路線規劃 × 站牌選址 = **組合最佳化（NP-hard）**
- 禁區避障、地形成本差異
- 多目標權衡：路線效率 vs 乘客便利 vs 建設成本

> **目標函數**：
> Cost = α · route_cost + β · Σwalk_cost + γ · Σstop_cost

---

## 數學建模

| 符號 | 意義 |
|------|------|
| G = (V, E) | NxN 網格圖 |
| R = (v₁, ..., vₖ) | A→B 路線 |
| S ⊆ R | 站牌集合（在路線上）|
| α, β, γ | 政策權重參數 |

**三項成本**：
- **C_route**：Σ terrain_cost — 路線行進成本
- **C_walk**：Σ 乘客到最近站牌的 Manhattan 距離
- **C_stop**：Σ (固定成本 + 地形加成)

**約束**：路徑連通、禁區不可通行、|S| ≤ max_stops

---

## 五種優化方法

| 方法 | 路線策略 | 站牌策略 | 特性 |
|------|---------|---------|------|
| **Baseline** | A* 最短路徑 | 等距放置 | 快速基準 |
| **Greedy** | A* 最短路徑 | 貪心選址 | 考慮乘客 |
| **GA** | 中繼點+A* | 染色體編碼 | 全域搜索 |
| **SA** | 中繼點+A* | 鄰域操作 | 收斂穩定 |
| **MILP** | A* 最短路徑 | 整數規劃 | 精確解 |

**關鍵差異**：Baseline/Greedy 固定路線，GA/SA 可透過中繼點改變路線形狀

---

## 測試集設計

| 地圖 | 規模 | 特徵 | 測試目的 |
|------|------|------|---------|
| Map 1 | 30×30, 20人 | 無禁區、均勻 | 基礎驗證、MILP ground truth |
| Map 2 | 50×50, 100人 | 兩群聚乘客 | 繞路效益 |
| Map 3 | 50×50, 100人 | 大禁區擋中間 | 避障能力 |
| Map 4 | 80×80, 500人 | 分散+高地形 | 擴展性 |
| Map 5 | 50×50, 100人 | 對角線分布 | 路線偏移策略 |

所有地圖以固定 seed 生成，確保可重現

---

## 實驗結果 — 總成本比較

| 地圖 | Baseline | Greedy | **GA** | **SA** | MILP |
|------|----------|--------|--------|--------|------|
| Map 1 | 231 | 220 | 211 | **206** | 222 |
| Map 2 | 1693 | 1654 | 595 | **571** | — |
| Map 3 | 1481 | 1391 | **979** | 992 | — |
| Map 4 | 10262 | 9921 | 5803 | **5635** | — |
| Map 5 | 2460 | 2314 | 747 | **638** | — |

**GA/SA 降低 30-70% 成本** — 透過中繼點改變路線形狀

---

## 實驗結果 — 覆蓋率 & 穩定性

**覆蓋率（步行距離 ≤ 10 格的乘客比例）**：

| 地圖 | Baseline | Greedy | GA | SA |
|------|----------|--------|-----|-----|
| Map 2 | 13% | 14% | 99% | **100%** |
| Map 5 | 1% | 4% | 84% | **95%** |

**穩定性（10 次執行 mean±std）**：

| 地圖 | GA | SA |
|------|-----|-----|
| Map 3 | 1111±155 | **987±33** |
| Map 4 | 6102±334 | **5710±103** |

SA 在大規模問題上穩定性明顯優於 GA

---

## 消融實驗（Map 2 × GA）

| 策略 | α | β | γ | 加權成本 | 路線 | 步行 | 站牌 |
|------|---|---|---|---------|------|------|------|
| 均衡 | 1.0 | 1.0 | 1.0 | 595 | 115 | 438 | 42 |
| 乘客優先 | 0.3 | 1.0 | 0.3 | 528 | 127 | 477 | 42 |
| 營運優先 | 1.0 | 0.3 | 0.3 | 262 | 105 | 487 | 36 |
| 極端乘客 | 0.1 | 1.0 | 0.1 | 502 | 119 | 486 | 42 |

**政策啟示**：社區接駁車 → 高 β（覆蓋優先）；幹線公車 → 高 α（效率優先）

---

## 各方法適用情境

| 方法 | 優點 | 缺點 | 適用情境 |
|------|------|------|---------|
| **Baseline** | 極快、確定 | 忽略乘客 | 快速基準 |
| **Greedy** | 快速、考慮乘客 | 路線固定 | 站牌優化 |
| **GA** | 全域搜索 | 較慢、不穩定 | 中規模最佳解 |
| **SA** | 穩定、大規模 | 依賴鄰域設計 | 大規模問題 |
| **MILP** | 保證最優 | 僅小規模 | Ground truth |

---

## 限制與未來方向

**當前限制**：
- 2D 網格（非真實路網）
- 單一路線（非多路線網絡）
- 靜態需求（不考慮時段變化）
- 均質乘客（不區分類別）

**未來方向**：
- 🚌 多路線網絡設計 + 轉乘優化
- 👥 乘客分類（通勤/老人/學生）+ 差異化權重
- 📊 整合市場調查數據的需求建模
- 🗺️ OpenStreetMap 真實路網整合
- ⚡ 商用 MILP solver (Gurobi) 擴展精確解範圍

---

## 結論

1. **成功建模**為三項加權成本最佳化問題
2. **五種方法**完整比較，涵蓋確定、啟發、元啟發、精確四類
3. **GA/SA 大幅優於 Baseline/Greedy**（30-70% 成本降低）
4. **SA 穩定性最佳**，適合大規模問題
5. **消融實驗**展示 α/β/γ 的政策意涵
6. **互動 Demo** 支援即時參數調整與方法比較

> **Demo**: [link] | **Report**: [link] | **GitHub**: [link]

**Thank you!**
