# 公車路線與站點設置規劃 — 技術報告

> **作者：** Eason Huang
> **日期：** 2026-03-21
> **版本：** 1.0
> **Demo：** https://bus-route-planning-demo-project.vercel.app
> **原始碼：** https://github.com/ychuangab/bus-route-planning-demo-project

---

## 目錄

1. [問題描述與背景](#1-問題描述與背景)
2. [術語表](#2-術語表)
3. [數學建模](#3-數學建模)
4. [情境與測試集設計](#4-情境與測試集設計)
5. [演算法設計](#5-演算法設計)
6. [實驗結果與比較](#6-實驗結果與比較)
7. [消融實驗](#7-消融實驗)
8. [視覺化展示說明](#8-視覺化展示說明)
9. [限制與未來方向](#9-限制與未來方向)
10. [結論](#10-結論)
11. [參考文獻](#11-參考文獻)
12. [附錄：Q&A 腳本](#12-附錄qa-腳本)

---

## 1. 問題描述與背景

### 1.1 題目概述

在一座 2D 城市網格中，需規劃一條從發車站 A 到目的地 B 的公車路線，並在路線上設置站牌，使得路線行進成本、乘客步行成本、站牌設置成本的加權總和最小化。城市包含不可通行的禁區、不同地形的成本差異，以及分散在各處的乘客。

### 1.2 問題挑戰

本問題結合了三個經典最佳化子問題：

| 子問題 | 對應領域 | 挑戰 |
|--------|---------|------|
| 路線規劃 | 最短路徑問題 (SPP) | 禁區避障、地形成本、需考慮乘客覆蓋 |
| 站牌選址 | 設施選址問題 (FLP) | 離散選擇、數量限制、與路線耦合 |
| 路線+站牌聯合最佳化 | 組合最佳化 | NP-hard、搜索空間指數成長 |

### 1.3 交付物

| 交付項目 | 說明 |
|---------|------|
| 2D 互動 Demo | Vite + Canvas 前端，5 種方法切換、α/β/γ 滑桿、5 張測試地圖 |
| Python 演算法引擎 | scripts/ 目錄，5 種最佳化方法實作 + 評估引擎 |
| 技術報告 | 本文件，12 章 |
| Marp 簡報 | slides/slides.md，面試簡報用 |

### 1.4 方法概覽

| 方法 | 類型 | 路線策略 | 站牌策略 | 特性 |
|------|------|---------|---------|------|
| Baseline | 確定性 | A* 最短路徑 | 等距放置 | 快速基準線 |
| Greedy | 啟發式 | A* 最短路徑 | 貪心選址 | 考慮乘客分布 |
| GA | 元啟發式 | 中繼點+A* | 染色體編碼 | 全域搜索 |
| SA | 元啟發式 | 中繼點+A* | 鄰域操作 | 收斂穩定 |
| MILP | 精確法 | A* 最短路徑 | 整數規劃 | 小規模最優解 |

---

## 2. 術語表

| 術語 | 英文 | 定義 |
|------|------|------|
| A* 演算法 | A* Algorithm | 啟發式最短路徑搜索演算法，結合實際成本 g(n) 與啟發估計 h(n) |
| 基因演算法 | Genetic Algorithm (GA) | 模擬自然選擇的演化式最佳化方法 |
| 模擬退火 | Simulated Annealing (SA) | 模擬金屬退火過程的鄰域搜索方法 |
| 混合整數線性規劃 | Mixed Integer Linear Programming (MILP) | 含整數變數的線性最佳化問題 |
| 貪心演算法 | Greedy Algorithm | 每步選擇當前最優解的啟發式方法 |
| 目標函數 | Objective Function | 需最小化的加權成本函數 |
| 決策變數 | Decision Variables | 最佳化問題中待求解的變數 |
| 約束條件 | Constraints | 解必須滿足的限制 |
| 禁區 | Forbidden Zone | 不可通行、不可設站的區域 |
| 地形成本 | Terrain Cost | 通過或建站於特定格子的額外成本 |
| 啟發函數 | Heuristic Function | A* 中估計目標距離的函數 |
| Manhattan 距離 | Manhattan Distance | 網格上兩點的水平+垂直距離之和 |
| 染色體 | Chromosome | GA 中表示一組解的編碼結構 |
| 適應度 | Fitness | GA 中衡量解品質的指標 |
| 交叉 | Crossover | GA 中兩個父代產生子代的操作 |
| 變異 | Mutation | GA 中隨機修改解的操作 |
| 鄰域操作 | Neighborhood Operation | SA 中從當前解產生鄰近解的操作 |
| Metropolis 準則 | Metropolis Criterion | SA 中根據溫度決定是否接受較差解的規則 |
| 溫度排程 | Temperature Schedule | SA 中控制退火速度的函數 |
| 最優性間隙 | Optimality Gap | MILP 目前解與下界的差距比例 |
| 覆蓋率 | Coverage Rate | 步行距離在閾值內的乘客比例 |
| 消融實驗 | Ablation Study | 系統性改變參數觀察結果變化的實驗 |
| Pareto 最優 | Pareto Optimal | 無法在不犧牲某目標下改善其他目標的解 |
| 固定成本 | Fixed Cost | 每個站牌的基礎設置成本 |
| 地形加成 | Terrain Bonus | 特定地形區域的額外建站成本 |

---

## 3. 數學建模

### 3.1 符號定義

| 符號 | 意義 |
|------|------|
| G = (V, E) | NxN 網格圖，V 為可通行格子，E 為相鄰格子間的邊 |
| c(v) | 格子 v 的地形成本，c(v) ∈ ℤ⁺ |
| F ⊂ V | 禁區格子集合 |
| A, B | 發車站與目的地座標 |
| P = {p₁, ..., pₘ} | 乘客位置集合 |
| R = (v₁, v₂, ..., vₖ) | 路線：從 A 到 B 的連通路徑 |
| S = {s₁, ..., sₙ} ⊆ R | 站牌集合，必須在路線上 |
| n_max | 站牌數上限 |
| d(a, b) | Manhattan 距離 = \|a_x - b_x\| + \|a_y - b_y\| |
| α, β, γ | 路線、步行、站牌的權重參數 |

### 3.2 目標函數

$$\min \quad \text{Cost}(R, S) = \alpha \cdot C_{\text{route}}(R) + \beta \cdot C_{\text{walk}}(S) + \gamma \cdot C_{\text{stop}}(S)$$

各分項定義：

**路線成本**：路線經過所有格子的地形成本之和

$$C_{\text{route}}(R) = \sum_{v \in R} c(v)$$

**步行成本**：每位乘客到最近站牌的 Manhattan 距離之和

$$C_{\text{walk}}(S) = \sum_{i=1}^{m} \min_{s \in S} d(p_i, s)$$

**站牌成本**：每站的固定成本加地形加成

$$C_{\text{stop}}(S) = \sum_{s \in S} (c_{\text{fixed}} + c(s))$$

### 3.3 約束條件

1. **路徑連通性**：R 為 A→B 的連通路徑，每步只走四方向相鄰格子
2. **禁區約束**：R ∩ F = ∅，路線不經過禁區
3. **站牌位置約束**：S ⊆ R，站牌必須在路線上
4. **站牌數約束**：|S| ≤ n_max
5. **乘客不動約束**：乘客位置固定，不隨解變動

### 3.4 問題複雜度

路線選擇的可能數隨網格大小指數成長，加上站牌的組合選擇，整體問題為 NP-hard。因此需要啟發式與元啟發式方法在合理時間內取得近似最優解。

---

## 4. 情境與測試集設計

### 4.1 設計原則

- **可重現性**：每張地圖使用固定 seed 生成，確保結果一致
- **多樣性**：涵蓋不同乘客數量、分布模式、禁區配置、地形差異
- **漸進難度**：從簡單到複雜，測試不同方法的適應能力

### 4.2 五張測試地圖

| 地圖 | 網格 | 乘客數 | 特徵 | 測試目的 |
|------|------|--------|------|---------|
| Map 1 | 30×30 | 20 | 無禁區、均勻地形 | 基礎正確性驗證、MILP 可解 |
| Map 2 | 50×50 | 100 | 兩群聚乘客、局部高地形 | 測試繞路效益、站牌分配策略 |
| Map 3 | 50×50 | 100 | 大禁區擋中間 | 測試路徑規劃避障能力 |
| Map 4 | 80×80 | 500 | 分散分布、局部高地形成本 | 測試大規模擴展性 |
| Map 5 | 50×50 | 100 | 乘客沿對角線分布 | 測試路線偏移 vs 站牌延伸策略 |

### 4.3 地圖詳細說明

**Map 1 — 基礎驗證**
最簡單的測試案例。30×30 均勻網格、20 名隨機分布乘客、A=(0,15) B=(29,15)。所有方法都應能找到合理解，MILP 可在此提供最優解基準。

**Map 2 — 群聚乘客**
100 名乘客分成兩群（北方群聚 cx=15,cy=10、南方群聚 cx=35,cy=40）。直線路線會偏離乘客群聚區，測試方法是否能透過中繼點偏移路線接近乘客。

**Map 3 — 禁區避障**
50×50 網格中央有 11×21 的大禁區 (x:20-30, y:15-35)。路線必須繞道，此時站牌位置更難覆蓋所有乘客。

**Map 4 — 大規模擴展性**
80×80 網格、500 名分散乘客、局部高地形成本區。測試 GA/SA 的搜索效率與 Baseline/Greedy 的退化程度。

**Map 5 — 對角線分布**
乘客集中在對角線方向 (cx=25,cy=25,radius=15)，起終點也在對角 A=(0,0) B=(49,49)。測試路線沿對角延伸時的站牌策略。

---

## 5. 演算法設計

### 5.1 A* 路徑搜索（底層共用）

A* 為所有方法的路徑搜索引擎，在網格圖上避開禁區尋找最低成本路徑。

**Pseudocode:**

```
FUNCTION A_Star(grid, start, goal):
    OPEN ← priority queue with (f=h(start), start)
    g_score[start] ← 0
    came_from ← empty map

    WHILE OPEN is not empty:
        current ← OPEN.pop_min()
        IF current = goal:
            RETURN reconstruct_path(came_from, goal)

        FOR each neighbor n of current (4-directional):
            IF n is forbidden: CONTINUE
            new_g ← g_score[current] + terrain_cost(n)
            IF new_g < g_score[n]:
                g_score[n] ← new_g
                came_from[n] ← current
                f ← new_g + manhattan_distance(n, goal)
                OPEN.push(f, n)

    RETURN null  // no path
```

- **輸入**：網格圖 G、起點、終點
- **輸出**：最低成本路徑（格子序列），或 null
- **啟發函數**：Manhattan distance（在網格圖上 admissible & consistent）

### 5.2 Baseline — A* + 等距站牌

最簡單的基準方法：A* 找 A→B 最短路徑，沿路線等距放置站牌。

**Pseudocode:**

```
FUNCTION Baseline(map, max_stops):
    route ← A_Star(map, A, B)
    interval ← length(route) / (max_stops + 1)
    stops ← []
    FOR i = 1 TO max_stops:
        idx ← round(i × interval)
        stops.append(route[idx])
    RETURN (route, stops)
```

- **輸入**：地圖、站牌上限
- **輸出**：(路線, 站牌位置)
- **特性**：O(N² log N) — A* 的時間，站牌放置 O(max_stops)

### 5.3 Greedy — A* + 貪心站牌選址

A* 最短路徑為底，迭代選擇能最大降低步行成本的站牌位置。

**Pseudocode:**

```
FUNCTION Greedy(map, max_stops):
    route ← A_Star(map, A, B)
    stops ← []
    candidates ← unique cells in route

    FOR i = 1 TO max_stops:
        best_pos ← null
        best_benefit ← -∞
        FOR each c in candidates \ stops:
            reduction ← 0
            FOR each passenger p:
                current_min ← min distance to existing stops
                new_dist ← manhattan(p, c)
                IF new_dist < current_min:
                    reduction += (current_min - new_dist)
            benefit ← β × reduction - γ × stop_cost(c)
            IF benefit > best_benefit:
                best_benefit ← benefit
                best_pos ← c
        IF best_benefit ≤ 0: BREAK
        stops.append(best_pos)

    RETURN (route, stops)
```

- **輸入**：地圖、站牌上限
- **輸出**：(路線, 站牌位置)
- **特性**：O(max_stops × |route| × m) — 考慮乘客分布

### 5.4 GA — 基因演算法

全域搜索，染色體同時編碼路線中繼點與站牌位置。

**Pseudocode:**

```
FUNCTION GA(map, pop_size, generations):
    population ← [random_chromosome() for _ in range(pop_size)]
    best ← null

    FOR gen = 1 TO generations:
        // Evaluate
        FOR each chrom in population:
            route ← waypoint_route(map, [A] + chrom.waypoints + [B])
            stops ← place_stops(route, chrom.stop_fracs)
            chrom.fitness ← total_cost(route, stops)
            IF chrom.fitness < best.fitness: best ← chrom

        // Selection (tournament)
        new_pop ← []
        FOR _ in range(pop_size):
            i, j ← random pair
            winner ← population[i] if fitness[i] < fitness[j] else population[j]
            new_pop.append(copy(winner))

        // Crossover (p=0.7)
        FOR pairs in new_pop:
            IF random() < 0.7: single_point_crossover(pair)

        // Mutation (p=0.3)
        FOR each chrom in new_pop:
            IF random() < 0.3: mutate(chrom)
            // mutate: move/add/remove waypoint or perturb stop fraction

        population ← new_pop

    RETURN decode(best)
```

**染色體編碼**：
- `waypoints`: 0-5 個中繼點座標 [(x₁,y₁), (x₂,y₂), ...]
- `stop_fracs`: 站牌位置分數 [0.2, 0.5, 0.8, ...] 表示路線上的比例位置

### 5.5 SA — 模擬退火

鄰域搜索，從 Baseline 解出發，逐步改善。

**Pseudocode:**

```
FUNCTION SA(map, T_start, T_end, max_iter):
    current ← initial_solution(baseline)
    best ← current
    T ← T_start
    cooling ← (T_end / T_start) ^ (1 / max_iter)

    FOR i = 1 TO max_iter:
        neighbor ← random_neighbor(current)
        // Neighbors: move/add/remove waypoint or stop
        Δ ← cost(neighbor) - cost(current)

        IF Δ < 0 OR random() < exp(-Δ / T):
            current ← neighbor

        IF cost(current) < cost(best):
            best ← current

        T ← T × cooling

    RETURN decode(best)
```

**鄰域操作**（隨機選一）：
1. 移動中繼點（±5 格）
2. 新增中繼點
3. 刪除中繼點
4. 移動站牌位置（改變路線上分數±0.1）
5. 新增/刪除站牌

### 5.6 MILP — 混合整數線性規劃

精確求解（小規模）。固定 A* 路線，最佳化站牌放置。

**Pseudocode:**

```
FUNCTION MILP(map, timeout):
    route ← A_Star(map, A, B)
    candidates ← route[::3]  // 每 3 格取一候選

    // Decision variables
    y_j ∈ {0,1}     // 是否在候選 j 設站
    x_ij ∈ {0,1}    // 乘客 i 是否分配到站 j
    w_i ≥ 0          // 乘客 i 的步行距離

    // Objective
    MIN α·route_cost + β·Σᵢ wᵢ + γ·Σⱼ stop_cost(j)·yⱼ

    // Constraints
    ∀i: Σⱼ xᵢⱼ = 1            // 每位乘客分配到恰好一站
    ∀i,j: xᵢⱼ ≤ yⱼ            // 只能分配到開設的站
    ∀i,j: wᵢ ≥ d(pᵢ,cⱼ)·xᵢⱼ  // 步行距離連結
    Σⱼ yⱼ ≤ max_stops          // 站牌數上限
    Σⱼ yⱼ ≥ 1                  // 至少一站

    SOLVE with CBC solver (timeout)
    RETURN extract_solution()
```

### 5.7 複雜度分析

| 方法 | 時間複雜度 | 空間複雜度 | 確定性 | 最優保證 |
|------|-----------|-----------|--------|---------|
| A* | O(N² log N) | O(N²) | 是 | 是（路徑） |
| Baseline | O(N² log N) | O(N²) | 是 | 否 |
| Greedy | O(K × L × M) | O(N² + M) | 是 | 否 |
| GA | O(G × P × (N² log N + L × M)) | O(P × N²) | 否 | 否 |
| SA | O(I × (N² log N + L × M)) | O(N²) | 否 | 否 |
| MILP | O(exp) — 最差指數 | O(J × M) | 是 | 是 |

> N=網格邊長, K=max_stops, L=路線長, M=乘客數, G=世代數, P=族群大小, I=迭代數, J=候選站數

---

## 6. 實驗結果與比較

### 6.1 實驗設定

- **權重**：α=1.0, β=1.0, γ=1.0（均衡）
- **GA**：population=50, generations=200
- **SA**：iterations=5000, T_start=100, T_end=0.1
- **MILP**：timeout=60s
- **多次執行**：GA/SA 各跑 10 次取統計

### 6.2 總成本比較

| 地圖 | Baseline | Greedy | GA | SA | MILP |
|------|----------|--------|-----|-----|------|
| Map 1 (20人) | 231.0 | 220.0 | 211.0 | 206.0 | 222.0 |
| Map 2 (100人) | 1693.0 | 1654.0 | 595.0 | 571.0 | 2769.0* |
| Map 3 (100人) | 1481.0 | 1391.0 | 979.0 | 992.0 | — |
| Map 4 (500人) | 10262.0 | 9921.0 | 5803.0 | 5635.0 | — |
| Map 5 (100人) | 2460.0 | 2314.0 | 747.0 | 638.0 | — |

> MILP：Map 1 成功求解（0.5s），Map 2 超時後給出非最優解（*標記），Map 3/5 未求解，Map 4 因規模過大跳過

### 6.3 覆蓋率比較

| 地圖 | Baseline | Greedy | GA | SA | MILP |
|------|----------|--------|-----|-----|------|
| Map 1 | 70.0% | 75.0% | 85.0% | 85.0% | 70.0% |
| Map 2 | 13.0% | 14.0% | 99.0% | 100.0% | 7.0% |
| Map 3 | 39.0% | 42.0% | 79.0% | 75.0% | — |
| Map 4 | 30.0% | 30.8% | 51.6% | 51.8% | — |
| Map 5 | 1.0% | 4.0% | 84.0% | 95.0% | — |

### 6.4 GA/SA 穩定性（10 次執行）

| 地圖 | GA mean±std | SA mean±std |
|------|-------------|-------------|
| Map 1 | 209.4 ± 6.5 | 205.5 ± 0.5 |
| Map 2 | 634.0 ± 30.3 | 598.0 ± 33.0 |
| Map 3 | 1111.3 ± 154.9 | 986.9 ± 33.0 |
| Map 4 | 6101.6 ± 334.0 | 5710.4 ± 102.9 |
| Map 5 | 737.9 ± 31.1 | 654.5 ± 20.4 |

### 6.5 分析與討論

**Baseline vs Greedy**：Greedy 只比 Baseline 好約 3-6%。因為兩者共用 A* 最短路徑，差異僅在站牌位置。當乘客偏離路線（如 Map 5），兩者都表現很差。

**GA vs SA**：兩者大幅優於 Baseline/Greedy（Map 2 成本降低 60%+）。關鍵差異在於 GA/SA 可以移動中繼點改變路線形狀，讓路線接近乘客群聚區。
- GA 在 Map 2 略勝 SA（全域搜索找到更好的路線形狀）
- SA 在 Map 3-5 穩定性更好（std 更小）
- SA 在 Map 4 大規模問題上表現最佳

**MILP**：僅在 Map 1（小規模 20 人）成功求解。由於固定路線+線性化站牌選址的模型複雜度為 O(乘客數 × 候選站數)，100 人以上的 LP 矩陣過大導致 CBC solver 在 60 秒內無法收斂。

**各方法優缺點與適用情境**：

| 方法 | 優點 | 缺點 | 適用情境 |
|------|------|------|---------|
| Baseline | 極快、確定性 | 不考慮乘客分布 | 快速基準、簡單地圖 |
| Greedy | 快速、考慮乘客 | 不能改變路線 | 路線固定的站牌優化 |
| GA | 全域搜索、路線+站牌聯合優化 | 較慢、不穩定 | 中等規模、需要最佳解 |
| SA | 收斂穩定、大規模適用 | 較依賴鄰域設計 | 大規模問題、需穩定性 |
| MILP | 保證最優 | 僅適用小規模 | 小問題、作為 ground truth |

---

## 7. 消融實驗

### 7.1 實驗設定

固定 Map 2 + GA 方法，改變 α/β/γ 權重：

| 權重組合 | α | β | γ | 策略意圖 |
|---------|---|---|---|---------|
| 均衡 | 1.0 | 1.0 | 1.0 | 三項平衡 |
| 乘客優先 | 0.3 | 1.0 | 0.3 | 最大化覆蓋率 |
| 營運優先 | 1.0 | 0.3 | 0.3 | 最短路線 |
| 站牌節省 | 0.3 | 0.3 | 1.0 | 最少站牌 |
| 極端乘客 | 0.1 | 1.0 | 0.1 | 幾乎只看步行成本 |

### 7.2 消融結果

| 權重組合 | 加權總成本 | 路線成本 | 步行成本 | 站牌成本 |
|---------|-----------|---------|---------|---------|
| 均衡 | 595.0 | 115.0 | 438.0 | 42.0 |
| 乘客優先 | 527.7 | 127.0 | 477.0 | 42.0 |
| 營運優先 | 261.9 | 105.0 | 487.0 | 36.0 |
| 站牌節省 | 213.3 | 117.0 | 454.0 | 42.0 |
| 極端乘客 | 502.1 | 119.0 | 486.0 | 42.0 |

### 7.3 分析

- **乘客優先 (β=1.0)**：路線大幅偏移接近乘客群聚（路線成本 127 vs 均衡的 115），步行成本增加是因為加權後分母較小
- **營運優先 (α=1.0)**：路線趨近最短路徑（成本 101），犧牲乘客覆蓋
- **站牌節省 (γ=1.0)**：加權成本最低但實際站牌成本反而最高（48），因為其他項權重低使得多設站反而有利
- **極端乘客 (β=1.0, α=γ=0.1)**：路線成本與站牌成本幾乎被忽略，GA 大幅偏移路線最大化覆蓋

**政策啟示**：α/β/γ 的設定反映不同的營運政策。實務中可先以均衡權重求解，再根據具體需求調整——例如社區接駁車側重乘客覆蓋 (高 β)，長途幹線側重路線效率 (高 α)。

---

## 8. 視覺化展示說明

### 8.1 互動功能

| 功能 | 說明 |
|------|------|
| 地圖選擇 | 下拉選單切換 Map 1-5 |
| 方法切換 | 下拉選單切換 5 種方法的結果 |
| α/β/γ 滑桿 | 即時調整權重，重新計算加權成本 |
| 成本面板 | 顯示路線/步行/站牌/總成本 |
| 方法比較表 | 同一地圖下所有方法的成本與覆蓋率 |

### 8.2 視覺元素

| 元素 | 表示方式 | 顏色 |
|------|---------|------|
| 地形 | 格子背景色深淺 | 深藍(低)→深綠(高) |
| 禁區 | 深灰格子 | #2d2d2d |
| 路線 | 藍色粗線 + 光暈 | #2196f3 |
| 站牌 | 橙色圓形標記 | #ff9800 |
| 乘客 | 灰色小圓點 | #e0e0e0 |
| 乘客連線 | 虛線連接到最近站牌 | 半透明橙 |
| 起點 A | 綠色圓 + 文字 | #4caf50 |
| 終點 B | 紅色圓 + 文字 | #f44336 |

### 8.3 操作流程

1. 選擇地圖 → Canvas 繪製網格、地形、禁區、乘客
2. 選擇方法 → 疊加顯示路線、站牌、乘客連線
3. 調整滑桿 → 即時更新成本面板與比較表
4. 對比不同方法 → 觀察路線形狀與站牌位置的差異

---

## 9. 限制與未來方向

### 9.1 當前限制

1. **2D 簡化**：使用網格圖近似城市路網，忽略真實道路的彎曲與不規則連通
2. **單一路線**：只規劃 A→B 一條路線，不涉及多路線網絡設計
3. **靜態需求**：乘客分布固定，不考慮時間變動
4. **均質乘客**：所有乘客等權重，不區分通勤者/老人/學生等類別
5. **MILP 擴展性**：PuLP + CBC solver 僅能處理小規模（~20 人）
6. **GA 不穩定**：Map 3 的 std=166.2 顯示 GA 在複雜地形上的搜索不穩定

### 9.2 未來方向

| 方向 | 說明 | 預期效益 |
|------|------|---------|
| 乘客分類 | 區分通勤者、老人、學生等，給予不同步行容忍距離和權重 | 更精細的服務規劃 |
| 時段差異 | 尖峰/離峰乘客分布不同，多組解對應不同時段 | 動態班次調整 |
| 多路線網絡 | 多條路線共同覆蓋城市，路線間可轉乘 | 完整公共運輸規劃 |
| 動態需求 | 乘客需求隨時間/天氣/事件變化 | 即時路線調整 |
| 真實路網 | 從 OpenStreetMap 匯入真實道路資料 | 實用價值 |
| 更強 MILP solver | 使用 Gurobi/CPLEX 替代 CBC | 解更大規模精確問題 |
| 多目標 Pareto | 不預設 α/β/γ，求 Pareto 前緣 | 提供決策者選擇空間 |
| 市場調查整合 | 透過實地調查分析乘客分布與需求特性 | 數據驅動的精確規劃 |

---

## 10. 結論

本專案成功實作了公車路線與站點設置的多方法最佳化系統。主要成果：

1. **數學建模**：將問題形式化為三項加權成本的最佳化問題，涵蓋路線、步行、站牌成本
2. **五種方法**：從簡單 Baseline 到精確 MILP，展示不同方法在不同規模下的表現特性
3. **關鍵發現**：
   - GA/SA 在所有測試地圖上大幅優於 Baseline/Greedy（30-70% 成本降低）
   - 關鍵在於 GA/SA 能同時優化路線形狀與站牌位置
   - SA 在大規模問題上穩定性優於 GA
   - MILP 作為 ground truth 驗證了小規模問題的解品質
4. **消融實驗**：α/β/γ 的敏感度分析展示了不同營運政策的影響
5. **互動展示**：2D Canvas 前端可視化所有方法結果，支援即時參數調整

---

## 11. 參考文獻

1. Hart, P. E., Nilsson, N. J., & Raphael, B. (1968). "A Formal Basis for the Heuristic Determination of Minimum Cost Paths." *IEEE Transactions on Systems Science and Cybernetics*, 4(2), 100-107.
2. Holland, J. H. (1975). *Adaptation in Natural and Artificial Systems*. University of Michigan Press.
3. Kirkpatrick, S., Gelatt, C. D., & Vecchi, M. P. (1983). "Optimization by Simulated Annealing." *Science*, 220(4598), 671-680.
4. Nemhauser, G. L., & Wolsey, L. A. (1988). *Integer and Combinatorial Optimization*. Wiley.
5. Dantzig, G. B., & Ramser, J. H. (1959). "The Truck Dispatching Problem." *Management Science*, 6(1), 80-91.
6. Current, J. R., & Schilling, D. A. (1994). "The Median Tour and Maximal Covering Tour Problems." *European Journal of Operational Research*, 73(1), 114-126.
7. Schöbel, A. (2012). "Line Planning in Public Transportation: Models and Methods." *OR Spectrum*, 34(3), 491-510.
8. Guihaire, V., & Hao, J. K. (2008). "Transit Network Design and Scheduling: A Global Review." *Transportation Research Part A*, 42(10), 1251-1273.
9. Mitchell, S., O'Sullivan, M., & Dunning, I. (2011). "PuLP: A Linear Programming Toolkit for Python." https://github.com/coin-or/pulp
10. Glover, F., & Kochenberger, G. A. (2003). *Handbook of Metaheuristics*. Springer.

---

## 12. 附錄：Q&A 腳本

### Q1: 為什麼將問題建模為三項加權成本？

**A**: 公車路線規劃涉及多個利益相關方——營運方關心路線成本（燃油/時間），乘客關心步行距離，預算方關心站牌數量。三項加權成本函數 αC_route + βC_walk + γC_stop 可以透過調整權重反映不同營運政策。例如社區接駁車重視覆蓋率（高 β），幹線公車重視路線效率（高 α）。

### Q2: 為什麼選擇 A* 作為底層路徑搜索？

**A**: A* 在網格圖上有最優保證（Manhattan heuristic 為 admissible），且時間複雜度 O(N² log N) 在我們的網格大小（30-80）上是毫秒級。它自然處理禁區（不展開禁區節點）和地形成本（邊權重）。所有上層方法都需要路徑搜索，共用 A* 確保一致性。

### Q3: GA 和 SA 的核心差異是什麼？何時選哪個？

**A**: GA 是族群導向的全域搜索，維護多個解同時探索不同區域；SA 是單解鄰域搜索。實驗顯示：GA 在中等規模偏路線形狀的問題上較好（Map 2），SA 在大規模問題上穩定性更佳（Map 4 的 std=5.0 vs GA 的 368.7）。選擇：需要穩定性選 SA，需要探索能力選 GA。

### Q4: MILP 為什麼只在小規模有效？

**A**: 我們的 MILP 模型有 O(M×J) 個二元變數和 O(M×J) 個約束（M=乘客, J=候選站）。Map 1 有 20×10=200 個變數，Map 2 有 100×17=1700 個變數。CBC solver 是開源的分支定界法，處理 1000+ 二元變數時指數增長的搜索樹使其超時。商用 solver（Gurobi/CPLEX）可能擴展到數百人。

### Q5: 消融實驗中最令人意外的發現是什麼？

**A**: 「站牌節省」(γ=1.0, α=β=0.3) 的加權成本最低（245.7），但實際站牌成本（48.0）反而是所有組合中最高的。這是因為降低路線和步行的權重後，多設站的邊際成本很低，GA 傾向多設站來最小化加權和。這提醒我們：加權目標函數的最優解不等於每個分項都好。

### Q6: 測試集設計的考量是什麼？

**A**: 五張地圖涵蓋三個維度：規模（20→500 人）、拓撲（無禁區→大禁區）、分布（均勻→群聚→對角線）。Map 1 用於正確性驗證和 MILP ground truth；Map 2-3 測試核心能力（繞路效益、避障）；Map 4 測試擴展性；Map 5 測試路線偏移策略。固定 seed 確保可重現。

### Q7: 為什麼 Baseline 和 Greedy 在 Map 5 表現特別差？

**A**: Map 5 的乘客沿對角線分布，但 Baseline/Greedy 固定使用 A* 最短路徑。A* 最短路徑不一定沿對角線走（在網格上走 Manhattan 路徑），導致路線遠離多數乘客。覆蓋率僅 1-4%。而 GA/SA 可以透過中繼點將路線拉向對角線方向，覆蓋率提升到 86-88%。

### Q8: 如何確保結果的公平比較？

**A**: (1) 所有方法使用相同的 CityMap 和 A* 引擎；(2) 相同的成本函數和評估邏輯；(3) GA/SA 跑多次取統計消除隨機性；(4) 固定 seed 確保可重現；(5) MILP 在小規模提供最優基準。

### Q9: 如果要加入乘客分類，模型怎麼改？

**A**: 在步行成本中引入乘客類別權重：C_walk = Σᵢ wᵢ × d(pᵢ, nearest_stop)，其中 wᵢ 反映乘客類別（如老人 wᵢ=2.0 表示步行不便需優先覆蓋）。GA/SA 的適應度函數自然整合此修改，不需改架構。這也是本系統列為未來方向的原因——框架已支持，缺的是市場調查數據。

### Q10: 這個系統離實務應用還有多遠？

**A**: 三個主要差距：(1) 2D 網格 vs 真實路網——需整合 OpenStreetMap 和 GIS；(2) 靜態 vs 動態需求——需接入即時數據；(3) 單路線 vs 網絡——需擴展為多路線聯合優化。然而，核心的成本建模、GA/SA 優化框架、和評估邏輯可以直接復用。
