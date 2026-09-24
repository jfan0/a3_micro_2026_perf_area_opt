# improve_perf_area: baseline_area_v7_1
Parent branch: baseline_area_v6_2
Build config: MediumBoomV3Config
BoomTile (parent): BoomTile
BoomTile (child):  BoomTile
Synthesis success: True; STA success: True
embench: 19/19 with IPC, mean IPC 1.432266; riscv-tests: 237/239 passed

## Objective

| metric | parent | child | delta |
|---|---|---|---|
| mean embench IPC | 1.444178 | 1.432266 | -0.825% |
| total cell area (um2) | 5,964,896 | 5,636,879 | -5.499% |
| SRAM macro area (um2) | 1,588,098 | 1,233,138 | -22.351% |
| fmax (MHz) | 46.24 | 45.39 | -1.838% |
| embench speed/MHz | 2.219955 | 2.197645 | -1.005% |
| embench speed score | 102.651 | 99.751 | -2.825% |
| embench_speed_score_area_eff (speed/mm2) -- gates | 17.209139 | 17.696157 | +2.830% |
| ipc_area_eff (IPC/mm2) -- recorded | 0.242113 | 0.254088 | +4.946% |

Verdict: **IMPROVED +2.830% vs parent**

## Hard gates

- PASS perf_area_eff: 17.696157 speed/mm2 >= parent 17.209139 speed/mm2 (child fmax 45.39 MHz)
- PASS riscv-tests: no regressions against the seed's 239 tests

Gates: **PASSED** (recorded as status=ok)
