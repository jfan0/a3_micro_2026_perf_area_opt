# improve_perf_area: baseline_area_v8
Parent branch: baseline_area_v7_1
Build config: MediumBoomV3Config
BoomTile (parent): BoomTile
BoomTile (child):  BoomTile
Synthesis success: True; STA success: True
embench: 19/19 with IPC, mean IPC 1.432266; riscv-tests: 237/239 passed

## Objective

| metric | parent | child | delta |
|---|---|---|---|
| mean embench IPC | 1.432266 | 1.432266 | +0.000% |
| total cell area (um2) | 5,636,879 | 5,473,384 | -2.900% |
| SRAM macro area (um2) | 1,233,138 | 1,188,250 | -3.640% |
| fmax (MHz) | 45.39 | 46.79 | +3.084% |
| embench speed/MHz | 2.197645 | 2.197645 | +0.000% |
| embench speed score | 99.751 | 102.828 | +3.084% |
| embench_speed_score_area_eff (speed/mm2) -- gates | 17.696157 | 18.786882 | +6.164% |
| ipc_area_eff (IPC/mm2) -- recorded | 0.254088 | 0.261678 | +2.987% |

Verdict: **IMPROVED +6.164% vs parent**

## Hard gates

- PASS perf_area_eff: 18.786882 speed/mm2 >= parent 17.696157 speed/mm2 (child fmax 46.79 MHz)
- PASS riscv-tests: no regressions against the seed's 239 tests

Gates: **PASSED** (recorded as status=ok)
