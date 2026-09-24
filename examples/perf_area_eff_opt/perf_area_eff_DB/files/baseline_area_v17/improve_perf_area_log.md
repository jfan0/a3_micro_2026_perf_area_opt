# improve_perf_area: baseline_area_v17
Parent branch: baseline_area_v16
Build config: MediumBoomV3Config
BoomTile (parent): BoomTile
BoomTile (child):  BoomTile
Synthesis success: True; STA success: True
embench: 19/19 with IPC, mean IPC 1.428141; riscv-tests: 237/239 passed

## Objective

| metric | parent | child | delta |
|---|---|---|---|
| mean embench IPC | 1.428141 | 1.428141 | +0.000% |
| total cell area (um2) | 5,024,660 | 4,993,670 | -0.617% |
| SRAM macro area (um2) | 1,167,490 | 1,167,490 | +0.000% |
| fmax (MHz) | 52.37 | 53.29 | +1.757% |
| embench speed/MHz | 2.192370 | 2.192370 | +0.000% |
| embench speed score | 114.814 | 116.831 | +1.757% |
| embench_speed_score_area_eff (speed/mm2) -- gates | 22.850188 | 23.395899 | +2.388% |
| ipc_area_eff (IPC/mm2) -- recorded | 0.284226 | 0.285990 | +0.621% |

Verdict: **IMPROVED +2.388% vs parent**

## Hard gates

- PASS perf_area_eff: 23.395899 speed/mm2 > best so far (v16) 22.850188 speed/mm2 (child fmax 53.29 MHz)
- PASS riscv-tests: no regressions against the seed's 239 tests

Gates: **PASSED** (recorded as status=ok)
