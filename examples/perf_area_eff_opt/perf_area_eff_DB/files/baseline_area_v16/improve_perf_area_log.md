# improve_perf_area: baseline_area_v16
Parent branch: baseline_area_v15_timing
Build config: MediumBoomV3Config
BoomTile (parent): BoomTile
BoomTile (child):  BoomTile
Synthesis success: True; STA success: True
embench: 19/19 with IPC, mean IPC 1.428141; riscv-tests: 237/239 passed

## Objective

| metric | parent | child | delta |
|---|---|---|---|
| mean embench IPC | 1.428116 | 1.428141 | +0.002% |
| total cell area (um2) | 4,999,156 | 5,024,660 | +0.510% |
| SRAM macro area (um2) | 1,167,490 | 1,167,490 | +0.000% |
| fmax (MHz) | 48.17 | 52.37 | +8.719% |
| embench speed/MHz | 2.192332 | 2.192370 | +0.002% |
| embench speed score | 105.605 | 114.814 | +8.721% |
| embench_speed_score_area_eff (speed/mm2) -- gates | 21.124491 | 22.850188 | +8.169% |
| ipc_area_eff (IPC/mm2) -- recorded | 0.285671 | 0.284226 | -0.506% |

Verdict: **IMPROVED +8.169% vs parent**

## Hard gates

- PASS perf_area_eff: 22.850188 speed/mm2 > best so far (v15_timing) 21.124491 speed/mm2 (child fmax 52.37 MHz)
- PASS riscv-tests: no regressions against the seed's 239 tests

Gates: **PASSED** (recorded as status=ok)
