# improve_perf_area: baseline_area_v2
Parent branch: baseline_area_v1
Build config: MediumBoomV3Config
BoomTile (parent): BoomTile
BoomTile (child):  BoomTile
Synthesis success: True; STA success: True
embench: 19/19 with IPC, mean IPC 1.449806; riscv-tests: 237/239 passed

## Objective

| metric | parent | child | delta |
|---|---|---|---|
| mean embench IPC | 1.449806 | 1.449806 | +0.000% |
| total cell area (um2) | 7,371,858 | 6,738,322 | -8.594% |
| SRAM macro area (um2) | 1,641,487 | 1,641,487 | +0.000% |
| fmax (MHz) | 39.51 | 46.6 | +17.945% |
| embench speed/MHz | 2.229238 | 2.229238 | +0.000% |
| embench speed score | 88.077 | 103.882 | +17.945% |
| embench_speed_score_area_eff (speed/mm2) -- gates | 11.947760 | 15.416671 | +29.034% |
| ipc_area_eff (IPC/mm2) -- recorded | 0.196668 | 0.215158 | +9.402% |

Verdict: **IMPROVED +29.034% vs parent**

## Hard gates

- PASS perf_area_eff: 15.416671 speed/mm2 >= parent 11.947760 speed/mm2 (child fmax 46.6 MHz)
- PASS riscv-tests: no regressions against the seed's 239 tests

Gates: **PASSED** (recorded as status=ok)
