# improve_perf_area: baseline_area_v11
Parent branch: baseline_area_v10
Build config: MediumBoomV3Config
BoomTile (parent): BoomTile
BoomTile (child):  BoomTile
Synthesis success: True; STA success: True
embench: 19/19 with IPC, mean IPC 1.432266; riscv-tests: 237/239 passed

## Objective

| metric | parent | child | delta |
|---|---|---|---|
| mean embench IPC | 1.432266 | 1.432266 | +0.000% |
| total cell area (um2) | 5,481,536 | 5,475,768 | -0.105% |
| SRAM macro area (um2) | 1,188,250 | 1,188,250 | +0.000% |
| fmax (MHz) | 38.45 | 48.17 | +25.280% |
| embench speed/MHz | 2.197645 | 2.197645 | +0.000% |
| embench speed score | 84.499 | 105.861 | +25.280% |
| embench_speed_score_area_eff (speed/mm2) -- gates | 15.415286 | 19.332549 | +25.412% |
| ipc_area_eff (IPC/mm2) -- recorded | 0.261289 | 0.261564 | +0.105% |

Verdict: **IMPROVED +25.412% vs parent**

## Hard gates

- PASS perf_area_eff: 19.332549 speed/mm2 >= parent 15.415286 speed/mm2 (child fmax 48.17 MHz)
- PASS riscv-tests: no regressions against the seed's 239 tests

Gates: **PASSED** (recorded as status=ok)
