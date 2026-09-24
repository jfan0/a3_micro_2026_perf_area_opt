# improve_perf_area: baseline_area_v13
Parent branch: baseline_area_v12
Build config: MediumBoomV3Config
BoomTile (parent): BoomTile
BoomTile (child):  BoomTile
Synthesis success: True; STA success: True
embench: 19/19 with IPC, mean IPC 1.432266; riscv-tests: 237/239 passed

## Objective

| metric | parent | child | delta |
|---|---|---|---|
| mean embench IPC | 1.432266 | 1.432266 | +0.000% |
| total cell area (um2) | 5,482,042 | 5,305,560 | -3.219% |
| SRAM macro area (um2) | 1,188,250 | 1,188,250 | +0.000% |
| fmax (MHz) | 38.65 | 48.17 | +24.631% |
| embench speed/MHz | 2.197645 | 2.197645 | +0.000% |
| embench speed score | 84.939 | 105.861 | +24.631% |
| embench_speed_score_area_eff (speed/mm2) -- gates | 15.494041 | 19.952759 | +28.777% |
| ipc_area_eff (IPC/mm2) -- recorded | 0.261265 | 0.269956 | +3.326% |

Verdict: **IMPROVED +28.777% vs parent**

## Hard gates

- PASS perf_area_eff: 19.952759 speed/mm2 > best so far (v9) 19.332549 speed/mm2 (child fmax 48.17 MHz)
- PASS riscv-tests: no regressions against the seed's 239 tests

Gates: **PASSED** (recorded as status=ok)
