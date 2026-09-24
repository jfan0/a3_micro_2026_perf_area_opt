# improve_perf_area: baseline_area_v15_timing
Parent branch: baseline_area_v15
Build config: MediumBoomV3Config
BoomTile (parent): BoomTile
BoomTile (child):  BoomTile
Synthesis success: True; STA success: True
embench: 19/19 with IPC, mean IPC 1.428116; riscv-tests: 237/239 passed

## Objective

| metric | parent | child | delta |
|---|---|---|---|
| mean embench IPC | 1.428116 | 1.428116 | +0.000% |
| total cell area (um2) | 4,999,074 | 4,999,156 | +0.002% |
| SRAM macro area (um2) | 1,167,490 | 1,167,490 | +0.000% |
| fmax (MHz) | 43.48 | 48.17 | +10.787% |
| embench speed/MHz | 2.192332 | 2.192332 | +0.000% |
| embench speed score | 95.323 | 105.605 | +10.787% |
| embench_speed_score_area_eff (speed/mm2) -- gates | 19.068051 | 21.124491 | +10.785% |
| ipc_area_eff (IPC/mm2) -- recorded | 0.285676 | 0.285671 | -0.002% |

Verdict: **IMPROVED +10.785% vs parent**

## Hard gates

- PASS perf_area_eff: 21.124491 speed/mm2 > best so far (v14) 20.571389 speed/mm2 (child fmax 48.17 MHz)
- PASS riscv-tests: no regressions against the seed's 239 tests

Gates: **PASSED** (recorded as status=ok)
