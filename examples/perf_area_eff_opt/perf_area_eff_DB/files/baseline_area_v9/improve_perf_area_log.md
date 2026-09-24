# improve_perf_area: baseline_area_v9
Parent branch: baseline_area_v8
Build config: MediumBoomV3Config
BoomTile (parent): BoomTile
BoomTile (child):  BoomTile
Synthesis success: True; STA success: True
embench: 19/19 with IPC, mean IPC 1.432266; riscv-tests: 237/239 passed

## Objective

| metric | parent | child | delta |
|---|---|---|---|
| mean embench IPC | 1.432266 | 1.432266 | +0.000% |
| total cell area (um2) | 5,473,384 | 5,475,768 | +0.044% |
| SRAM macro area (um2) | 1,188,250 | 1,188,250 | +0.000% |
| fmax (MHz) | 46.79 | 48.17 | +2.949% |
| embench speed/MHz | 2.197645 | 2.197645 | +0.000% |
| embench speed score | 102.828 | 105.861 | +2.949% |
| embench_speed_score_area_eff (speed/mm2) -- gates | 18.786882 | 19.332549 | +2.905% |
| ipc_area_eff (IPC/mm2) -- recorded | 0.261678 | 0.261564 | -0.044% |

Verdict: **IMPROVED +2.905% vs parent**

## Hard gates

- PASS perf_area_eff: 19.332549 speed/mm2 >= parent 18.786882 speed/mm2 (child fmax 48.17 MHz)
- PASS riscv-tests: no regressions against the seed's 239 tests

Gates: **PASSED** (recorded as status=ok)
